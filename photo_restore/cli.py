"""命令行入口.

用法示例:
    python -m photo_restore -i old.jpg -o output/
    python -m photo_restore -i photos/ -o restored/ --upscale 4
    python -m photo_restore -i old.jpg -o out/ --no-face --device cpu
"""
from __future__ import annotations

# 兼容补丁必须最先导入
from . import compat  # noqa: F401

import argparse
import sys
import time
from pathlib import Path

from . import __version__


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="photo-restore",
        description=(
            "老照片智能修复工具 (GFPGAN 人脸修复 + Real-ESRGAN 整体放大). "
            "首次运行会自动下载约 400MB 模型权重."
        ),
    )
    p.add_argument(
        "-i", "--input", required=True,
        help="输入图片或目录路径",
    )
    p.add_argument(
        "-o", "--output", default="output",
        help="输出目录 (默认: output)",
    )
    p.add_argument(
        "-s", "--upscale", type=int, default=2,
        help="放大倍数, 1~4 (默认: 2)",
    )
    p.add_argument(
        "--no-face", action="store_true",
        help="不启用人脸修复 (仅做整体超分)",
    )
    p.add_argument(
        "--device", choices=["auto", "cuda", "cpu"], default="auto",
        help="计算设备 (默认: auto, 有 CUDA 用 GPU 否则 CPU)",
    )
    p.add_argument(
        "--tile", type=int, default=400,
        help="背景超分分块大小, 显存/内存不足时调小, 0 表示不分块 (默认: 400)",
    )
    p.add_argument(
        "--fp32", action="store_true",
        help="禁用半精度 (FP16), GPU 默认开启半精度",
    )
    p.add_argument(
        "-v", "--version", action="version",
        version=f"photo-restore {__version__}",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    # 延迟导入, 让 --help / --version 不必加载模型
    from .restorer import (
        PhotoRestorer, RestoreOptions, collect_inputs, make_output_path,
    )

    in_path = Path(args.input).expanduser().resolve()
    out_root = Path(args.output).expanduser().resolve()

    try:
        files = collect_inputs(in_path)
    except FileNotFoundError as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 2

    if not files:
        print(f"[错误] 输入目录中没有支持的图片文件: {in_path}", file=sys.stderr)
        return 2

    opts = RestoreOptions(
        upscale=max(1, min(4, args.upscale)),
        face_enhance=not args.no_face,
        bg_tile=args.tile,
        device=None if args.device == "auto" else args.device,
        fp16=not args.fp32,
    )

    print("=" * 60)
    print(" 老照片智能修复工具")
    print("=" * 60)
    print(f" 输入       : {in_path}")
    print(f" 输出目录   : {out_root}")
    print(f" 放大倍数   : {opts.upscale}x")
    print(f" 人脸修复   : {'开启 (GFPGAN v1.4)' if opts.face_enhance else '关闭'}")
    print(f" 计算设备   : {opts.device or 'auto'}")
    print(f" 待处理图片 : {len(files)} 张")
    print("=" * 60)

    print("\n[步骤 1/2] 加载模型 (首次运行需下载约 400MB)...")
    t0 = time.time()
    try:
        restorer = PhotoRestorer(opts)
    except Exception as e:
        print(f"[错误] 模型加载失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 3
    print(f"  模型就绪, 用时 {time.time() - t0:.1f}s")

    print("\n[步骤 2/2] 开始修复...")
    ok_count = 0
    for idx, src in enumerate(files, 1):
        dst = make_output_path(src, in_path, out_root)
        print(f"  [{idx}/{len(files)}] {src.name}  ->  {dst}")
        t = time.time()
        try:
            restorer.restore_file(src, dst)
            ok_count += 1
            print(f"      完成 ({time.time() - t:.1f}s)")
        except Exception as e:
            print(f"      [失败] {e}", file=sys.stderr)

    print("\n" + "=" * 60)
    print(f" 全部完成: {ok_count}/{len(files)} 成功")
    print(f" 输出位置: {out_root}")
    print("=" * 60)
    return 0 if ok_count == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
