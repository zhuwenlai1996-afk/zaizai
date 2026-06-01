"""命令行入口。"""
import argparse
import sys
from pathlib import Path

from .pipeline import BookConfig, LLMClient, Pipeline, load_config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="picture_book_gen",
        description="中文 AI 绘本一键生成器（4 步：策划 → 评审 → 文案 → 生图提示词）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    p.add_argument(
        "-c", "--config", type=Path, default=None,
        help="YAML 配置文件路径（推荐方式）。可参考 picture_book_gen/examples/config.example.yaml",
    )
    p.add_argument(
        "-o", "--output", type=Path, default=Path("./book_output"),
        help="输出目录",
    )

    # 简易参数（无 --config 时用）
    p.add_argument("--title", help="绘本标题")
    p.add_argument("--topic", help="故事主题（如 '勇敢'、'分享'）")
    p.add_argument("--protagonist-name", help="主角姓名")
    p.add_argument("--protagonist-age", type=int, default=5, help="主角年龄")
    p.add_argument("--target-age", default="3-6", help="目标读者年龄段")
    p.add_argument("--total-pages", type=int, default=12, help="总页数（含封面与祝福页）")

    # LLM 配置
    p.add_argument("--model", default=None, help="OpenAI 模型，默认 gpt-4o-mini")
    p.add_argument(
        "--dry-run", action="store_true",
        help="不调用 API，只产出结构化模板（试跑或省钱）",
    )

    # 控制流
    p.add_argument("--from-step", type=int, choices=[1, 2, 3, 4], default=1,
                   help="从第几步开始")
    p.add_argument("--to-step", type=int, choices=[1, 2, 3, 4], default=4,
                   help="到第几步结束")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    # 加载或构造配置
    if args.config:
        cfg = load_config(args.config)
    else:
        if not (args.title and args.topic and args.protagonist_name):
            print(
                "错误: 必须提供 --config，或同时提供 --title --topic --protagonist-name",
                file=sys.stderr,
            )
            return 2
        cfg = BookConfig(
            title=args.title,
            topic=args.topic,
            protagonist_name=args.protagonist_name,
            protagonist_age=args.protagonist_age,
            target_age=args.target_age,
            total_pages=args.total_pages,
        )

    # 命令行覆盖 YAML
    if args.model:
        cfg.model = args.model
    cfg.dry_run = args.dry_run

    if args.from_step > args.to_step:
        print(f"错误: --from-step ({args.from_step}) 不能大于 --to-step ({args.to_step})",
              file=sys.stderr)
        return 2

    print(f"📖 《{cfg.title}》")
    print(f"   主题: {cfg.topic}  ·  主角: {cfg.protagonist_name}（{cfg.protagonist_age} 岁）")
    print(f"   模型: {cfg.model}{'  ·  DRY-RUN' if cfg.dry_run else ''}")
    print(f"   输出: {args.output.resolve()}")
    print()

    llm = LLMClient(model=cfg.model, dry_run=cfg.dry_run)
    Pipeline(cfg, args.output, llm).run(from_step=args.from_step, to_step=args.to_step)

    print(f"\n✓ 完成。产物在: {args.output.resolve()}")
    return 0
