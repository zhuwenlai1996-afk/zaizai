"""4 步流水线的 LLM 提示词模板。

每个函数返回 (system_prompt, user_prompt) 二元组。
"""
from __future__ import annotations

from typing import Tuple

# 类型注解里 BookConfig 仅用于 IDE 提示，避免循环 import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pipeline import BookConfig  # pragma: no cover


def step1_plan(cfg: "BookConfig") -> Tuple[str, str]:
    """第 1 步：策划方案。"""
    system = (
        "你是一位资深的中文儿童绘本主编，擅长为 3-9 岁儿童设计有温度、有教育意义的故事。"
        "你的输出始终使用中文 Markdown 格式，结构清晰、要点明确。"
    )
    appearance = cfg.protagonist_appearance or "（请你设计一个适合的外貌锚点，要具体到发型、服装、表情）"
    user = f"""请为下面这本中文儿童绘本起草一份完整的策划方案：

- **绘本标题**: {cfg.title}
- **核心主题**: {cfg.topic}
- **主角**: {cfg.protagonist_name}（{cfg.protagonist_age} 岁）
- **主角外貌锚点**: {appearance}
- **目标读者年龄**: {cfg.target_age}
- **总页数**: {cfg.total_pages}（含封面与祝福页）
- **画风**: {cfg.art_style}
- **情绪关键词**: {", ".join(cfg.emotion_keywords)}

输出请严格包含以下小节：

1. **角色设定** — 主角锚点（外貌、性格、口头禅） + 1~2 个配角
2. **故事大纲** — 开头-发展-高潮-结尾的四幕结构，每幕 2~3 句
3. **逐页规划骨架** — Markdown 表格，{cfg.total_pages} 行：页码 / 场景 / 主导情绪
4. **整体画风提示词** — 给文生图工具用，中英文各一段
5. **负面词建议** — 应避免出现的元素（暴力、刻板印象、对儿童不友好的画面等）
"""
    return system, user


def step2_review(cfg: "BookConfig", step1_output: str) -> Tuple[str, str]:
    """第 2 步：编辑评审。"""
    system = (
        "你是一位严格的儿童绘本资深编辑，专门审查中文绘本初稿的儿童适读性、"
        "价值导向、节奏感与画面可视化潜力。你不说客套话，直接指出问题。"
        "你的输出始终使用中文 Markdown 格式。"
    )
    user = f"""下面是这本绘本的策划初稿，请你站在儿童绘本编辑视角进行评审：

----- 策划初稿开始 -----
{step1_output}
----- 策划初稿结束 -----

请按以下结构给出评审：

1. **总体评价** — 2~3 句
2. **优点清单** — 条目列出
3. **问题清单** — 每条标注严重程度（🔴 重 / 🟡 中 / 🟢 轻）
4. **改进建议** — 针对每条问题给出具体可执行的修改方案
5. **针对 {cfg.target_age} 岁读者的特别提醒** — 例如生僻词、抽象概念、节奏过快等

请坦诚、具体，不要客套。
"""
    return system, user


def step3_pages(cfg: "BookConfig", step1: str, step2: str) -> Tuple[str, str]:
    """第 3 步：逐页文案。"""
    system = (
        "你是一位中文儿童绘本作家，擅长用极简、有韵律的中文为低龄儿童写绘本文案。"
        "每页文字控制在 1~3 句，朗朗上口，不晦涩，避免生僻字。"
        "你的输出始终使用中文 Markdown 格式。"
    )
    last_page = cfg.total_pages
    inner_start = 2
    inner_end = last_page - 1
    user = f"""请综合以下策划方案与编辑评审，写出绘本的逐页文案。

----- 策划方案 -----
{step1}

----- 编辑评审 -----
{step2}

要求：

- 总共 {cfg.total_pages} 页：
  - 第 1 页 = 封面
  - 第 {inner_start}~{inner_end} 页 = 故事内页
  - 第 {last_page} 页 = 给小读者的祝福页

- 每页严格按以下格式输出（注意 H2 标题）：

```
## 第 X 页 · [简短标题]
- **场景**: 一句话描述画面
- **正文**: 这一页要印在书上的中文文字（1~3 句，简洁有节奏）
- **情绪**: 主导情绪关键词
```

- 通篇语言风格统一，前后呼应；价值导向积极，符合中国家庭语境。
"""
    return system, user


def step4_image_prompts(cfg: "BookConfig", step1: str, step3: str) -> Tuple[str, str]:
    """第 4 步：生图提示词。"""
    system = (
        "你是一位精通 AI 文生图工具（Midjourney / DALL·E / 即梦 / Nano Banana 等）的视觉总监，"
        "擅长为中文儿童绘本写出**高一致性、高复用性**的英文提示词。"
        "你的输出使用中文 Markdown 格式，但 prompt 主体保留英文。"
    )
    user = f"""请基于下面的策划画风与逐页文案，为每一页写出可直接喂给 AI 图模的提示词。

----- 策划方案（含画风）-----
{step1}

----- 逐页文案 -----
{step3}

要求：

- 每页严格按以下格式输出：

```
## 第 X 页 · [简短标题]
- **构图**: 中文，描述视觉重心、视角、节奏
- **Prompt (EN)**: 英文，含主角锚点 + 场景 + 画风 + 关键氛围词
- **Negative**: 英文，避免出现的元素
```

- **主角锚点（外貌、服装、发型）必须在每一页 prompt 中复述**，保证角色跨页一致性。
- 整本画风风格描述每页保持一致。
- **不要让模型生成中文文字**——目前所有文生图工具都画不好中文长句，文字部分留给后期排版。
- 输出末尾追加一段 **「工具适配建议」**：分别给 Midjourney 风格化系数、DALL·E 风格修饰、即梦/Nano Banana 中文友好度的简短建议。
"""
    return system, user
