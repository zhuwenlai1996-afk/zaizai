# picture_book_gen — 中文 AI 绘本一键生成器

把 [`picture_book/ziqi_cloud_bunny`](../picture_book/ziqi_cloud_bunny/) 那套**人机协作工作流**封装成命令行：输入一个主题和主角信息，跑一条命令，自动产出 4 份 Markdown 文档：

1. `01-策划方案.md` — 角色 + 大纲 + 逐页骨架 + 画风
2. `02-编辑评审.md` — 自动审稿与改进建议
3. `03-逐页文案.md` — 12 页（封面 + 内页 + 祝福页）的中文成稿
4. `04-生图提示词.md` — 每页的英文 prompt（含主角锚点，保证跨页一致性）

每一步的产物都保存在磁盘上，**你可以在任何一步停下来手工编辑**，再继续跑下一步。

---

## 工作流

```
            主题 + 主角         ┌───────────────────┐
              │                 │ 任意步骤产物可     │
              ▼                 │ 手工编辑后再继续   │
         ┌─────────┐            │                   │
   step1 │ 策划方案 │ ◀──────────┘                   │
         └────┬────┘                                │
              ▼                                     │
         ┌─────────┐                                │
   step2 │ 编辑评审 │ ◀──────────────────────────────┤
         └────┬────┘                                │
              ▼                                     │
         ┌─────────┐                                │
   step3 │ 逐页文案 │ ◀──────────────────────────────┤
         └────┬────┘                                │
              ▼                                     │
         ┌──────────┐                               │
   step4 │ 生图提示词 │ ─────►  喂给 Midjourney /    │
         └──────────┘          DALL·E / 即梦 / ...  │
```

---

## 安装

```bash
pip install -r picture_book_gen/requirements.txt
# 或只装核心两个包:
pip install "openai>=1.30" "pyyaml>=6.0"
```

设置 OpenAI API Key：

```bash
# Linux / macOS
export OPENAI_API_KEY=sk-xxxxxx

# Windows PowerShell
$env:OPENAI_API_KEY="sk-xxxxxx"
```

> 还没拿到 API Key？没关系，下面有 **`--dry-run` 模式**，不联网也能先把流水线跑通。

---

## 使用

### 方式 A · YAML 配置（推荐）

```bash
# 1. 复制示例配置
cp picture_book_gen/examples/config.example.yaml my_book.yaml

# 2. 编辑 my_book.yaml 填入你的标题、主题、主角、画风等

# 3. 运行
python -m picture_book_gen -c my_book.yaml -o ./book_output
```

### 方式 B · 命令行参数（轻量试跑）

```bash
python -m picture_book_gen \
  --title "勇敢的小蘑菇" \
  --topic "勇敢与友谊" \
  --protagonist-name "豆豆" \
  --protagonist-age 4 \
  --target-age "3-6" \
  -o ./book_output
```

### 试跑 / 省钱模式（不调用 API）

加 `--dry-run`，**不联网、不消耗 API 额度**，只产出"结构正确"的占位文档：

```bash
python -m picture_book_gen -c my_book.yaml -o ./book_output --dry-run
```

适合：
- 没拿到 API Key 时先验证管道
- 调试 prompt 模板
- CI 集成测试

### 断点续跑 · 单步执行

```bash
# 只跑第 1 步
python -m picture_book_gen -c my_book.yaml --from-step 1 --to-step 1

# 第 1 步产物你打开手动改完了，从第 2 步跑到底
python -m picture_book_gen -c my_book.yaml --from-step 2

# 单独重跑第 4 步（基于已存在的 01/03 产物）
python -m picture_book_gen -c my_book.yaml --from-step 4 --to-step 4
```

> Pipeline 会从 `output/01-策划方案.md`、`02-编辑评审.md` 等已存在文件读取上一步结果，
> 所以你可以在任何一步打开 markdown 改完再继续。

---

## 命令行参数速查

| 参数 | 默认 | 说明 |
|---|---|---|
| `-c, --config` | | YAML 配置文件路径（推荐） |
| `-o, --output` | `./book_output` | 输出目录 |
| `--title` | | 绘本标题（无 config 时必填） |
| `--topic` | | 故事主题（无 config 时必填） |
| `--protagonist-name` | | 主角名（无 config 时必填） |
| `--protagonist-age` | `5` | 主角年龄 |
| `--target-age` | `3-6` | 目标读者年龄段 |
| `--total-pages` | `12` | 总页数（含封面与祝福页） |
| `--model` | `gpt-4o-mini` | OpenAI 模型 |
| `--dry-run` | 关 | 不调用 API，产出占位结构 |
| `--from-step` | `1` | 起始步骤（1~4） |
| `--to-step` | `4` | 结束步骤（1~4） |

---

## 配置文件字段

完整示例见 [`examples/config.example.yaml`](./examples/config.example.yaml)：

```yaml
title: 子琪的云朵兔子大冒险
topic: 陪伴与勇敢

protagonist:
  name: 华子琪
  age: 5
  appearance: 黑色双低辫，珍珠头饰，圆脸，自信笑容，常穿白色纱裙

target_age: "3-6"
total_pages: 12
art_style: 温暖水彩童书风格、柔和自然光、低饱和明亮色、梦幻但真实
emotion_keywords: [陪伴, 勇敢, 被爱, 梦想]

llm:
  model: gpt-4o-mini
  temperature: 0.8
```

---

## 输出结构

```
book_output/
├── 01-策划方案.md
├── 02-编辑评审.md
├── 03-逐页文案.md
└── 04-生图提示词.md
```

每个文件顶部都自动写入元信息（标题、模型、是否 dry-run、主角与主题），方便归档对比。

---

## 模块结构

```
picture_book_gen/
├── __init__.py
├── __main__.py            # python -m picture_book_gen 入口
├── cli.py                 # argparse 与主流程
├── pipeline.py            # BookConfig + LLMClient + Pipeline 编排
├── prompts.py             # 4 步提示词模板
├── examples/
│   └── config.example.yaml
├── requirements.txt
└── README.md
```

---

## 成本估算（参考）

以 `gpt-4o-mini`、12 页绘本、默认 prompt 为例，端到端跑完一本约消耗：

- 输入 token：~3K
- 输出 token：~5K
- 估算成本：约 **\$0.005 ~ \$0.01 / 本**（不含图模生成）

切到 `gpt-4o` 大约是 **\$0.10 ~ \$0.20 / 本**。

---

## 与 picture_book/ziqi_cloud_bunny 的关系

- [`picture_book/ziqi_cloud_bunny/`](../picture_book/ziqi_cloud_bunny/) 是这套工作流**手写的样本** —— 想看"成品长什么样"看这里。
- `picture_book_gen/` 是这套工作流**自动化的实现** —— 想"做你自己的一本"用这里。

---

## 路线图

- [ ] 步骤 5：自动调用 image API 生成插画（gpt-image-1 / DALL·E 3）
- [ ] 步骤 6：合成可印刷 PDF（含中文文字层 + 出血位 + CMYK）
- [ ] 多模型支持：Anthropic Claude、本地 LLM（通过 `OPENAI_BASE_URL` 兼容接口）
- [ ] 角色一致性增强：基于参考图自动生成更精准的主角锚点描述
- [ ] 流式输出，长 prompt 实时显示进度
- [ ] 评测套件：用一组主题批量生成、人工打分，对比不同 prompt 的产出质量
