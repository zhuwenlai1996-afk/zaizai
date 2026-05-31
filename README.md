# zaizai

> **让前沿 AI 真正落到普通人手里。**
> 一个面向中文非技术用户的开源工具集合：老照片修复、办公自动化、IT 资产清点、AI 辅助内容创作。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#)
[![Status](https://img.shields.io/badge/status-active-success.svg)](#)

---

## 项目定位

很多最先进的 AI 模型（GFPGAN、Real-ESRGAN、GPT、扩散模型等）已经开源很久了，但对一位 **不会装 Python 的奶奶**、**只会用 Excel 的基层 HR**、**想做绘本却没画功的家长** 而言，"模型已开源" ≠ "他们能用"。

`zaizai` 是一个**个人维护的小工具集**，每个子项目都瞄准一个真实场景，把这些 AI / 自动化能力**封装成普通中文用户可以一键使用的形态**——一个 `.exe`、一条命令行、一份可复用的工作流。

---

## 子项目一览

| 子项目 | 解决的问题 | 关键技术 | 文档 |
|---|---|---|---|
| 🖼 **photo_restore** | 修复模糊、褪色的老照片，可一键打包成 Windows `.exe` 给不会用 Python 的家人 | PyTorch · GFPGAN · Real-ESRGAN · PyInstaller | [./photo_restore/README.md](./photo_restore/README.md) |
| 📊 **attendance_ranking** | 替代企业脆弱、易错的考勤排名 Excel 公式，输出带条件格式与图表的报表 | openpyxl · pandas | [./attendance_ranking/README.md](./attendance_ranking/README.md) |
| 💻 **pc_inventory** | 部门电脑资产采集与汇总：通过组策略 / 计划任务在每台电脑静默采集主机名、序列号、IP，再汇总成 Excel | Python 标准库 · openpyxl · PyInstaller | [./pc_inventory/README.md](./pc_inventory/README.md) |
| ✨ **picture_book_gen** | 中文 AI 绘本一键生成器：输入主题 + 主角，自动产出策划 → 评审 → 文案 → 生图提示词 4 份文档 | OpenAI API · Prompt Engineering · Pipeline | [./picture_book_gen/README.md](./picture_book_gen/README.md) |
| 📖 **picture_book / ziqi_cloud_bunny** | "中文 AI 绘本人机协作工作流"参考样本：策划 → 编辑评审 → 分镜文案 → 生图提示词 | LLM · 文生图 prompt 工程 | [./picture_book/ziqi_cloud_bunny/README.md](./picture_book/ziqi_cloud_bunny/README.md) |

---

## 仓库结构

```
zaizai/
├── photo_restore/             # 老照片修复 (Python 包)
│   ├── __init__.py
│   ├── __main__.py            # 支持 python -m photo_restore
│   ├── cli.py
│   ├── compat.py              # basicsr / torchvision 兼容补丁
│   ├── restorer.py
│   └── README.md
│
├── attendance_ranking/        # 考勤排名自动化
│   ├── ranking.py
│   └── README.md
│
├── pc_inventory/              # 部门电脑资产采集与汇总
│   ├── __main__.py            # 子命令: collect / aggregate / info
│   ├── sysinfo.py
│   ├── collect.py
│   ├── aggregate.py
│   ├── department_map.example.csv
│   └── README.md
│
├── picture_book_gen/          # 中文 AI 绘本一键生成器
│   ├── __main__.py            # python -m picture_book_gen
│   ├── cli.py
│   ├── pipeline.py            # BookConfig + LLMClient + Pipeline
│   ├── prompts.py             # 4 步提示词模板
│   ├── examples/config.example.yaml
│   ├── requirements.txt
│   └── README.md
│
├── picture_book/
│   └── ziqi_cloud_bunny/      # AI 绘本工作流的手写样本
│       ├── 01-策划方案-原始版.md
│       ├── 02-编辑评审.md
│       ├── 03-逐页文案-修订版.md
│       ├── 04-生图提示词-修订版.md
│       └── README.md
│
├── tests/                     # pytest 测试
├── requirements.txt           # photo_restore 的依赖
├── photo_restore.spec         # PyInstaller 打包配置 (photo_restore)
├── pc_inventory_collect.spec  # PyInstaller 打包配置 (pc_inventory)
├── build.bat                  # Windows 一键打包: photo_restore
├── build_pc_inventory.bat     # Windows 一键打包: pc_inventory
├── LICENSE                    # MIT
└── README.md                  # ← 你正在看这个
```

---

## 快速开始

各子项目独立运行，请按需查看对应的 README。

### photo_restore（最常用）

```bash
git clone https://github.com/zhuwenlai1996-afk/zaizai.git
cd zaizai
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m photo_restore -i old.jpg -o output/
```

Windows 一键打包成 `.exe`：双击根目录的 `build.bat`。
完整说明见 [photo_restore/README.md](./photo_restore/README.md)。

### attendance_ranking

```bash
pip install openpyxl pandas
python attendance_ranking/ranking.py -i 输入.xlsx -o 输出.xlsx
```

完整说明见 [attendance_ranking/README.md](./attendance_ranking/README.md)。

### pc_inventory

```bash
pip install openpyxl

# 在每台电脑上采集
python -m pc_inventory collect -o \\fileserver\share\pc_inventory\data --silent

# 在管理员电脑上汇总
python -m pc_inventory aggregate -i \\fileserver\share\pc_inventory\data -o 部门电脑清单.xlsx
```

完整说明见 [pc_inventory/README.md](./pc_inventory/README.md)。

### picture_book_gen

```bash
pip install -r picture_book_gen/requirements.txt
export OPENAI_API_KEY=sk-xxxxxx

# 一键生成一本中文绘本（4 份 markdown：策划/评审/文案/生图提示词）
python -m picture_book_gen \
  --title "勇敢的小蘑菇" --topic "勇敢与友谊" \
  --protagonist-name "豆豆" --protagonist-age 4 \
  -o ./book_output

# 没有 API Key 时先试跑（不联网，产出占位结构）
python -m picture_book_gen -c picture_book_gen/examples/config.example.yaml --dry-run
```

完整说明见 [picture_book_gen/README.md](./picture_book_gen/README.md)。

### picture_book / ziqi_cloud_bunny

这是一个**文档型项目**，不是可执行代码。它是 `picture_book_gen` 工作流的**手写参考样本**——你想看"自动生成出来大致长什么样"，可以先看这里。详见 [picture_book/ziqi_cloud_bunny/README.md](./picture_book/ziqi_cloud_bunny/README.md)。

---

## 设计理念

1. **门槛优先**：每个工具都问自己一句"这个能不能交给我妈用？"，能就发布，不能就继续封装。
2. **中文文档第一**：服务被英文 AI 生态长期忽视的中文非技术用户。
3. **诚实标注边界**：AI 不是魔法，能做什么、做不好什么（如中文长句渲染）都在文档里写清楚。
4. **可复用的工作流，而不只是代码**：picture_book 那种"流程文档"也是这个仓库的一部分。

---

## 致谢

`photo_restore` 站在以下开源项目的肩膀上，特别感谢：

- [GFPGAN](https://github.com/TencentARC/GFPGAN) · 腾讯 ARC 实验室
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) · Xintao Wang 等
- [BasicSR](https://github.com/XPixelGroup/BasicSR) / [facexlib](https://github.com/xinntao/facexlib)

各模型权重遵循其原始开源协议，详见 [LICENSE](./LICENSE) 中的第三方说明。

---

## 许可

本仓库代码采用 [MIT License](./LICENSE) 开源。
注意：第三方模型权重不在 MIT 范围内，商业使用前请确认上游协议。

---

## 关于作者

Maintained by [@zhuwenlai1996-afk](https://github.com/zhuwenlai1996-afk).
欢迎通过 [Issues](https://github.com/zhuwenlai1996-afk/zaizai/issues) 反馈 bug 与建议。
