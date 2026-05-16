"""核心修复逻辑: Real-ESRGAN 放大 + GFPGAN 人脸修复."""
from __future__ import annotations

# 必须在 basicsr/gfpgan/realesrgan 之前导入, 打 torchvision 补丁
from . import compat  # noqa: F401

import os
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch


# ---------------------------------------------------------------------------
# 模型权重下载
# ---------------------------------------------------------------------------
MODEL_URLS = {
    # Real-ESRGAN x4 通用模型 (基于 RRDBNet, 23 blocks)
    "RealESRGAN_x4plus.pth": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.1.0/RealESRGAN_x4plus.pth"
    ),
    # GFPGAN v1.4 人脸修复模型
    "GFPGANv1.4.pth": (
        "https://github.com/TencentARC/GFPGAN/releases/download/"
        "v1.3.0/GFPGANv1.4.pth"
    ),
    # 人脸检测器 (GFPGAN 内部依赖, facexlib 也会用)
    "detection_Resnet50_Final.pth": (
        "https://github.com/xinntao/facexlib/releases/download/"
        "v0.1.0/detection_Resnet50_Final.pth"
    ),
    "parsing_parsenet.pth": (
        "https://github.com/xinntao/facexlib/releases/download/"
        "v0.2.2/parsing_parsenet.pth"
    ),
}


def _get_weights_dir() -> Path:
    """获取权重目录 (兼容 PyInstaller 打包后的运行环境)."""
    if getattr(sys, "frozen", False):
        # PyInstaller exe 运行时, 把权重放在 exe 同目录的 weights/ 下
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    weights = base / "weights"
    weights.mkdir(parents=True, exist_ok=True)
    return weights


def _download(url: str, dst: Path) -> None:
    """带进度提示的下载."""
    print(f"[下载] {dst.name}\n  从 {url}")

    def _hook(blocknum: int, blocksize: int, total: int) -> None:
        if total <= 0:
            return
        downloaded = blocknum * blocksize
        pct = min(100.0, downloaded * 100.0 / total)
        sys.stdout.write(f"\r  进度: {pct:6.2f}%")
        sys.stdout.flush()

    tmp = dst.with_suffix(dst.suffix + ".part")
    urllib.request.urlretrieve(url, tmp, _hook)
    tmp.rename(dst)
    sys.stdout.write("\n")


def ensure_weights() -> Path:
    """确保所有模型权重已下载, 返回权重根目录."""
    weights_dir = _get_weights_dir()
    for name, url in MODEL_URLS.items():
        dst = weights_dir / name
        if not dst.exists():
            _download(url, dst)
    # facexlib 在运行时会到 ~/.cache 或库内部寻找权重,
    # 我们顺便把检测/解析权重拷贝到 facexlib 期望的位置
    try:
        import facexlib
        fx_dir = Path(facexlib.__file__).parent / "weights"
        fx_dir.mkdir(parents=True, exist_ok=True)
        for fn in ("detection_Resnet50_Final.pth", "parsing_parsenet.pth"):
            src = weights_dir / fn
            tgt = fx_dir / fn
            if src.exists() and not tgt.exists():
                try:
                    tgt.write_bytes(src.read_bytes())
                except Exception:
                    pass
    except Exception:
        pass
    return weights_dir


# ---------------------------------------------------------------------------
# 修复器
# ---------------------------------------------------------------------------
@dataclass
class RestoreOptions:
    upscale: int = 2                # 最终放大倍数
    face_enhance: bool = True       # 是否启用 GFPGAN 人脸修复
    bg_tile: int = 400              # Real-ESRGAN 分块大小, 显存不足时调小
    device: Optional[str] = None    # 'cuda' / 'cpu' / None=自动
    fp16: bool = True               # GPU 上使用半精度, 提速并省显存


class PhotoRestorer:
    """老照片修复器."""

    def __init__(self, opts: RestoreOptions):
        self.opts = opts
        self.weights_dir = ensure_weights()
        self.device = self._resolve_device(opts.device)
        self._bg_upsampler = self._build_bg_upsampler()
        self._face_enhancer = (
            self._build_face_enhancer() if opts.face_enhance else None
        )

    # -- 设备选择 ----------------------------------------------------------
    @staticmethod
    def _resolve_device(device: Optional[str]) -> str:
        if device:
            return device
        return "cuda" if torch.cuda.is_available() else "cpu"

    # -- Real-ESRGAN 背景超分 ---------------------------------------------
    def _build_bg_upsampler(self):
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64,
            num_block=23, num_grow_ch=32, scale=4,
        )
        half = self.opts.fp16 and self.device == "cuda"
        return RealESRGANer(
            scale=4,
            model_path=str(self.weights_dir / "RealESRGAN_x4plus.pth"),
            model=model,
            tile=self.opts.bg_tile,
            tile_pad=10,
            pre_pad=0,
            half=half,
            device=self.device,
        )

    # -- GFPGAN 人脸修复 ---------------------------------------------------
    def _build_face_enhancer(self):
        from gfpgan import GFPGANer
        return GFPGANer(
            model_path=str(self.weights_dir / "GFPGANv1.4.pth"),
            upscale=self.opts.upscale,
            arch="clean",
            channel_multiplier=2,
            bg_upsampler=self._bg_upsampler,
            device=self.device,
        )

    # -- 单张图片修复 ------------------------------------------------------
    def restore_image(self, img_bgr: np.ndarray) -> np.ndarray:
        """输入 BGR 图像, 返回修复后的 BGR 图像."""
        if self._face_enhancer is not None:
            _, _, output = self._face_enhancer.enhance(
                img_bgr,
                has_aligned=False,
                only_center_face=False,
                paste_back=True,
            )
            return output
        # 仅做整体放大
        output, _ = self._bg_upsampler.enhance(
            img_bgr, outscale=self.opts.upscale
        )
        return output

    def restore_file(self, src: Path, dst: Path) -> None:
        img = cv2.imdecode(
            np.fromfile(str(src), dtype=np.uint8), cv2.IMREAD_COLOR
        )
        if img is None:
            raise RuntimeError(f"无法读取图片: {src}")
        out = self.restore_image(img)
        # 用 imencode 写出, 兼容中文路径
        ext = dst.suffix.lower() or ".png"
        ok, buf = cv2.imencode(ext, out)
        if not ok:
            raise RuntimeError(f"无法编码输出: {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(buf.tobytes())


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif"}


def collect_inputs(path: Path) -> list[Path]:
    """收集输入图片. 支持单文件或目录."""
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(
            p for p in path.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
        )
    raise FileNotFoundError(f"输入路径不存在: {path}")


def make_output_path(src: Path, in_root: Path, out_root: Path) -> Path:
    """根据输入文件计算输出路径, 保持目录结构."""
    if in_root.is_file():
        return out_root / f"{src.stem}_restored{src.suffix}"
    rel = src.relative_to(in_root)
    return out_root / rel.with_name(f"{rel.stem}_restored{rel.suffix}")
