@echo off
echo ========================================
echo   CS2 Highlight Studio
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

REM 先启动应用
echo Starting CS2 Highlight Studio...
start "" pythonw main.py

REM 后台检查依赖
echo Checking dependencies in background...
pip install -q PyQt6 demoparser2 pandas obsws-python 2>nul

REM 检查 FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg 未在 PATH 中，视频处理功能将不可用
    echo 请安装 FFmpeg: https://ffmpeg.org/download.html
)

echo.
echo Done. Close this window.
