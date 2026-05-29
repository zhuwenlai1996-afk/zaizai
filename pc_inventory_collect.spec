# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 部门电脑资产采集器 (单文件 exe).

用法::

    pyinstaller pc_inventory_collect.spec --clean --noconfirm

产物::

    dist/pc_inventory_collect.exe   <- 单文件, 约 10 MB

只依赖标准库, 体积小, 适合放到共享目录由登录脚本拉起.
"""

block_cipher = None


a = Analysis(
    ["pc_inventory/collect.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["pc_inventory", "pc_inventory.sysinfo"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 标准库里也用不到这些 GUI / 重型库, 统一排除以减小体积
        "tkinter", "matplotlib", "numpy", "openpyxl", "pandas", "PIL",
        "PyQt5", "PyQt6", "PySide2", "PySide6", "torch", "torchvision",
        "basicsr", "gfpgan", "realesrgan", "facexlib",
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="pc_inventory_collect",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
