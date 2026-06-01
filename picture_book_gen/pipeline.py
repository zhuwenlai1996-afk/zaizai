"""配置 + LLM 客户端 + 4 步流水线编排。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import prompts


# ----------------------------- 配置 -----------------------------

@dataclass
class BookConfig:
    title: str
    topic: str
    protagonist_name: str
    protagonist_age: int = 5
    protagonist_appearance: str = ""
    target_age: str = "3-6"
    total_pages: int = 12
    art_style: str = "温暖水彩童书风格、柔和自然光、低饱和明亮色、梦幻但真实"
    emotion_keywords: List[str] = field(
        default_factory=lambda: ["陪伴", "勇敢", "梦想"]
    )

    # 运行时
    model: str = "gpt-4o-mini"
    temperature: float = 0.8
    dry_run: bool = False


def load_config(path: Path) -> BookConfig:
    """从 YAML 文件加载配置。延迟 import pyyaml，避免无 yaml 时也阻断 CLI 模式。"""
    try:
        import yaml  # noqa: WPS433
    except ImportError as exc:
        raise RuntimeError(
            "未安装 PyYAML；请 `pip install pyyaml`，或改用纯命令行参数（不传 --config）。"
        ) from exc

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    proto = raw.get("protagonist") or {}
    llm_cfg = raw.get("llm") or {}

    return BookConfig(
        title=raw["title"],
        topic=raw["topic"],
        protagonist_name=proto.get("name", "小主人公"),
        protagonist_age=int(proto.get("age", 5)),
        protagonist_appearance=str(proto.get("appearance", "")),
        target_age=str(raw.get("target_age", "3-6")),
        total_pages=int(raw.get("total_pages", 12)),
        art_style=str(raw.get("art_style", BookConfig.art_style)),
        emotion_keywords=list(raw.get("emotion_keywords") or [])
        or ["陪伴", "勇敢", "梦想"],
        model=str(llm_cfg.get("model", "gpt-4o-mini")),
        temperature=float(llm_cfg.get("temperature", 0.8)),
    )


# ----------------------------- LLM 客户端 -----------------------------

class LLMClient:
    """OpenAI Chat Completions 的薄封装，支持 dry-run。"""

    def __init__(self, model: str = "gpt-4o-mini", dry_run: bool = False):
        self.model = model
        self.dry_run = dry_run
        self._client = None

        if dry_run:
            return

        try:
            from openai import OpenAI  # noqa: WPS433
        except ImportError as exc:
            raise RuntimeError(
                "未安装 openai SDK；请 `pip install openai>=1.30`，或加 --dry-run 试跑。"
            ) from exc

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "环境变量 OPENAI_API_KEY 未设置；请设置后重试，或加 --dry-run 试跑。"
            )

        self._client = OpenAI(
            api_key=api_key,
            base_url=os.environ.get("OPENAI_BASE_URL") or None,
        )

    def complete(self, system: str, user: str, temperature: float = 0.8) -> str:
        if self.dry_run:
            return _dry_run_response(system, user)

        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""


def _dry_run_response(system: str, user: str) -> str:
    """产出可视的占位内容，让用户验证 pipeline 结构正确。"""
    return (
        "> _**[DRY-RUN 占位]** 已跳过 OpenAI API 调用。_\n"
        "> _去掉 `--dry-run` 并设置 `OPENAI_API_KEY` 后即可生成真实内容。_\n\n"
        "**System prompt 摘要**:\n"
        f"```\n{system[:200]}{'...' if len(system) > 200 else ''}\n```\n\n"
        "**User prompt 摘要**:\n"
        f"```\n{user[:400]}{'...' if len(user) > 400 else ''}\n```\n"
    )


# ----------------------------- 流水线 -----------------------------

_STEP_FILES = {
    1: "01-策划方案.md",
    2: "02-编辑评审.md",
    3: "03-逐页文案.md",
    4: "04-生图提示词.md",
}

_STEP_TITLES = {
    1: "策划方案",
    2: "编辑评审",
    3: "逐页文案",
    4: "生图提示词",
}


class Pipeline:
    def __init__(self, cfg: BookConfig, output_dir: Path, llm: LLMClient):
        self.cfg = cfg
        self.output_dir = Path(output_dir)
        self.llm = llm

    def run(self, from_step: int = 1, to_step: int = 4) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for step in range(from_step, to_step + 1):
            print(f"==> 第 {step} 步: {_STEP_TITLES[step]}")
            sys_prompt, user_prompt = self._build_prompt(step)
            content = self.llm.complete(sys_prompt, user_prompt, self.cfg.temperature)
            out_path = self.output_dir / _STEP_FILES[step]
            out_path.write_text(self._header(step) + content + "\n", encoding="utf-8")
            print(f"    ✓ 写入 {out_path}")

    def _build_prompt(self, step: int):
        if step == 1:
            return prompts.step1_plan(self.cfg)
        if step == 2:
            return prompts.step2_review(self.cfg, self._read_prev(1))
        if step == 3:
            return prompts.step3_pages(
                self.cfg, self._read_prev(1), self._read_prev(2)
            )
        if step == 4:
            return prompts.step4_image_prompts(
                self.cfg, self._read_prev(1), self._read_prev(3)
            )
        raise ValueError(f"未知步骤 {step}")

    def _read_prev(self, step: int) -> str:
        path = self.output_dir / _STEP_FILES[step]
        if not path.exists():
            raise FileNotFoundError(
                f"第 {step} 步产物 {path} 不存在；请先运行该步，或调整 --from-step。"
            )
        return path.read_text(encoding="utf-8")

    def _header(self, step: int) -> str:
        dry = " · DRY-RUN" if self.cfg.dry_run else ""
        return (
            f"# 《{self.cfg.title}》· {_STEP_TITLES[step]}\n\n"
            f"> 由 picture_book_gen 自动生成 · 模型 `{self.cfg.model}`{dry}\n\n"
            f"> 主题: **{self.cfg.topic}** · 主角: **{self.cfg.protagonist_name}**"
            f"（{self.cfg.protagonist_age} 岁） · 目标读者: **{self.cfg.target_age}**\n\n"
            "---\n\n"
        )
