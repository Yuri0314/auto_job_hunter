@echo off
chcp 65001 >nul
setlocal

:: 检查虚拟环境是否存在
if not exist "venv\Scripts\python.exe" (
    echo ==================================================
    echo 虚拟环境不存在，正在创建...
    echo ==================================================
    python -m venv venv
    if errorlevel 1 (
        echo 创建虚拟环境失败！请确保已安装 Python。
        pause
        exit /b 1
    )

    echo 正在安装依赖...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    playwright install chromium
    echo ==================================================
    echo 依赖安装完成！
    echo ==================================================
)

:: 使用虚拟环境启动
echo ==================================================
echo Auto Job Hunter - 启动中...
echo ==================================================
venv\Scripts\python.exe run.py gui

pause