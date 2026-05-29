@echo off
REM ============================================================
REM  部门电脑资产采集器 - Windows 一键打包脚本
REM ============================================================
REM  用法: 双击运行, 或在命令行执行 build_pc_inventory.bat
REM
REM  前置: 已安装 Python 3.8+ 并加入 PATH
REM  输出: dist\pc_inventory_collect.exe (单文件)
REM ============================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  [1/3] 创建/激活虚拟环境
echo ============================================================
if not exist "venv_pcinv\" (
    python -m venv venv_pcinv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败, 请确认已安装 Python 3.8+
        pause
        exit /b 1
    )
)
call venv_pcinv\Scripts\activate.bat

echo.
echo ============================================================
echo  [2/3] 安装 PyInstaller (采集器只用标准库, 无其他依赖)
echo ============================================================
python -m pip install --upgrade pip
pip install "pyinstaller>=6.3"
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  [3/3] PyInstaller 打包 (约 30 秒)
echo ============================================================
if exist "build\" rmdir /S /Q build
pyinstaller pc_inventory_collect.spec --clean --noconfirm
if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  打包完成!
echo ============================================================
echo  可执行文件: dist\pc_inventory_collect.exe
echo.
echo  使用示例:
echo    pc_inventory_collect.exe -o \\server\share\pc_inventory\data
echo    pc_inventory_collect.exe -o \\server\share\pc_inventory\data --silent
echo ============================================================
pause
