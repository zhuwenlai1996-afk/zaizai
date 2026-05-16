# 老照片智能修复工具 (photo-restore)

集成 **GFPGAN**（人脸修复）+ **Real-ESRGAN**（整体超分放大）的命令行工具，
专为修复模糊、褪色的老照片而设计。

支持 Windows / macOS / Linux，可打包成单文件 `.exe` 在没有 Python 环境的电脑上运行。

---

## 效果

| 输入 | 处理 |
|---|---|
| 模糊的扫描件 / 翻拍老照片 | 先用 GFPGAN 还原人脸细节（皮肤、眼睛、五官清晰），再用 Real-ESRGAN 把整张图放大 2~4 倍并锐化 |

---

## 一、快速开始（本地 Python 运行）

### 1. 环境要求

- Python **3.10 ~ 3.12**（推荐 3.10）
- 显卡（可选）：NVIDIA GPU + CUDA 11.8/12.1 会快很多；没有 GPU 也能跑，CPU 模式约 30s~2min/张
- 磁盘：约 1.5 GB（依赖 + 模型权重）

### 2. 安装

```bash
git clone https://github.com/zhuwenlai1996-afk/zaizai.git
cd zaizai

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> **GPU 用户**：先到 https://pytorch.org/get-started/locally/ 选择对应
> CUDA 版本的 torch 安装命令（例如 `pip install torch torchvision --index-url
> https://download.pytorch.org/whl/cu121`），然后再 `pip install -r requirements.txt`。

> **国内用户**加速：
> ```bash
> pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 3. 使用

```bash
# 修复单张照片，默认放大 2 倍
python -m photo_restore -i old.jpg -o output/

# 放大 4 倍
python -m photo_restore -i old.jpg -o output/ --upscale 4

# 批量处理整个目录（递归）
python -m photo_restore -i photos/ -o restored/

# 仅做整体放大，不动人脸
python -m photo_restore -i old.jpg -o output/ --no-face

# 强制使用 CPU
python -m photo_restore -i old.jpg -o output/ --device cpu

# 显存不足时调小分块
python -m photo_restore -i old.jpg -o output/ --tile 200

# 查看全部参数
python -m photo_restore --help
```

输出文件命名规则：`原文件名_restored.原扩展名`。

> **首次运行**会自动下载约 400 MB 模型权重到项目根目录的 `weights/`
> 文件夹，下载位置在 GitHub releases，国内可能较慢，可以挂代理或多试几次。

---

## 二、打包成 Windows .exe

打包后会生成一个独立的 `photo-restore.exe`，**双击或拖拽图片到 cmd 即可使用**，
**接收文件的电脑不需要装 Python**。

### Windows 一键打包

直接双击运行项目根目录下的 **`build.bat`**：

```
build.bat
```

它会自动完成：
1. 创建 `venv` 虚拟环境
2. 安装所有依赖 + PyInstaller
3. 清理旧的 `build/` `dist/`
4. 执行 PyInstaller 打包

完成后产物在：

```
dist/photo-restore/photo-restore.exe        <- 主程序
dist/photo-restore/_internal/                <- 必需的依赖 dll/数据
```

整个 `dist/photo-restore/` 文件夹是绿色版，复制走就能用。

### 手动打包（任意系统）

```bash
pip install pyinstaller>=6.3
pyinstaller photo_restore.spec --clean --noconfirm
```

### 使用打包后的 exe

```bat
cd dist\photo-restore

REM 修复单张
photo-restore.exe -i C:\photos\old.jpg -o C:\photos\restored\

REM 批量
photo-restore.exe -i C:\photos\album -o C:\photos\restored --upscale 4
```

> exe 第一次运行时也会下载模型权重，权重保存在 **exe 同级的 `weights/`
> 目录**，下次运行直接复用。如果你想做成完全离线的安装包，可以在打包前先
> 本地运行一次脚本把 `weights/` 下载下来，然后把 `weights/` 文件夹复制到
> `dist/photo-restore/weights/` 一起分发即可。

---

## 三、命令行参数速查

| 参数 | 默认 | 说明 |
|---|---|---|
| `-i, --input` | 必填 | 输入图片或目录 |
| `-o, --output` | `output` | 输出目录 |
| `-s, --upscale` | `2` | 放大倍数 1~4 |
| `--no-face` | 关 | 关闭 GFPGAN 人脸修复 |
| `--device` | `auto` | `auto` / `cuda` / `cpu` |
| `--tile` | `400` | Real-ESRGAN 分块大小，显存不足调小（如 200/100） |
| `--fp32` | 关 | 禁用 FP16 半精度（数值更稳，速度稍慢） |
| `-v, --version` | | 查看版本 |

---

## 四、项目结构

```
zaizai/
├── photo_restore/
│   ├── __init__.py
│   ├── __main__.py        # 支持 python -m photo_restore
│   ├── cli.py             # 命令行参数解析与主流程
│   ├── compat.py          # torchvision/basicsr 兼容性补丁
│   └── restorer.py        # 核心: Real-ESRGAN + GFPGAN
├── requirements.txt       # 依赖清单
├── photo_restore.spec     # PyInstaller 打包配置
├── build.bat              # Windows 一键打包脚本
├── .gitignore
└── README.md
```

---

## 五、常见问题

**Q: 提示 `ModuleNotFoundError: No module named 'torchvision.transforms.functional_tensor'`**
A: 这是 `basicsr 1.4.2` 与新版 `torchvision` 的已知不兼容。本项目在
   `photo_restore/compat.py` 里已自动打补丁，请确认你是通过
   `python -m photo_restore` 而非直接 `python xxx.py` 运行的。

**Q: GPU 上 OOM（显存不足）**
A: 加 `--tile 200` 或更小，或加 `--fp32 --tile 200`。最稳的兜底是 `--device cpu`。

**Q: 模型权重下载失败**
A: 手动到下面地址下载，放到项目根目录的 `weights/` 里：
- `RealESRGAN_x4plus.pth`：https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
- `GFPGANv1.4.pth`：https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
- `detection_Resnet50_Final.pth`：https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth
- `parsing_parsenet.pth`：https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth

**Q: 打出来的 exe 太大（约 2~3 GB）？**
A: PyTorch + CUDA 库本身就大。如果只想发给 CPU 用户，可以在打包前装 CPU 版 torch：
```
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```
体积可以降到 ~800 MB。

---

## 致谢

本工具站在巨人的肩膀上：

- [GFPGAN](https://github.com/TencentARC/GFPGAN) — 腾讯 ARC 实验室的人脸修复
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) — Xintao Wang 等人的实用超分模型
- [BasicSR](https://github.com/XPixelGroup/BasicSR) / [facexlib](https://github.com/xinntao/facexlib)

模型权重各自遵循其原始开源协议（学术与个人非商业使用均可）。
