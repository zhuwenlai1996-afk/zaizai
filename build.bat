@echo off
REM ============================================================
REM  老照片修复工具 - Windows 一键打包脚本
REM ============================================================
REM  用法: 双击运行 build.bat, 或在命令行执行 build.bat
REM
REM  前置: 已安装 Python 3.10+ 并配置在 PATH 中
REM ============================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  [1/4] 创建/激活虚拟环境
echo ============================================================
if not exist "venv\" (
    echo 创建 venv ...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败, 请确认已安装 Python 3.10+
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat

echo.
echo ============================================================
echo  [2/4] 安装依赖 (首次较慢, 请耐心)
echo ============================================================
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
pip install pyinstaller>=6.3

echo.
echo ============================================================
echo  [3/4] 清理旧的构建产物
echo ============================================================
if exist "build\" rmdir /S /Q build
if exist "dist\"  rmdir /S /Q dist

echo.
echo ============================================================
echo  [4/4] PyInstaller 打包中 (约 5~10 分钟)
echo ============================================================
pyinstaller photo_restore.spec --clean --noconfirm
if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  打包完成!
echo ============================================================
echo  可执行文件位置: dist\photo-restore\photo-restore.exe
echo.
echo  使用示例:
echo    cd dist\photo-restore
echo    photo-restore.exe -i C:\path\to\old.jpg -o restored\
echo.
echo  首次运行会自动下载约 400MB 模型权重, 请保持网络通畅.
echo ============================================================
pause
