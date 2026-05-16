# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置.

用法:
    pyinstaller photo_restore.spec --clean

产物:
    dist/photo-restore/photo-restore.exe   <- 主程序
    dist/photo-restore/_internal/...       <- 依赖

打包后, 第一次运行 .exe 会自动下载约 400MB 模型权重到 .exe 同级的
weights/ 目录, 之后再运行就不会重复下载.
"""
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    copy_metadata,
)

# basicsr / gfpgan / realesrgan / facexlib 在运行时通过反射 / register 机制
# 加载子模块, 必须显式收集
hiddenimports = []
for pkg in ("basicsr", "gfpgan", "realesrgan", "facexlib"):
    hiddenimports += collect_submodules(pkg)

# 这些库内部 yaml / 配置文件需要随包一起带走
datas = []
for pkg in ("basicsr", "gfpgan", "realesrgan", "facexlib"):
    datas += collect_data_files(pkg)

# basicsr 用 importlib.metadata 读取自己的版本号, 没有元数据会崩
for pkg in ("basicsr", "gfpgan", "realesrgan", "facexlib", "torch"):
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass


block_cipher = None


a = Analysis(
    ["photo_restore/__main__.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 减小体积, 这些通常用不到
        "matplotlib", "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6",
        "notebook", "IPython", "pandas", "sklearn",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="photo-restore",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="photo-restore",
)
