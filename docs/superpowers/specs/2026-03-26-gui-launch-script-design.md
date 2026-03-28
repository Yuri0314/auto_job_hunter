# 一键启动脚本设计

## 背景

当前需要分别启动后端(FastAPI)和前端(Streamlit)两个服务，操作繁琐。

## 目标

新增 `python run.py gui` 命令，一键启动完整Web界面。

## 设计

### 修改 run.py

新增 `gui` 子命令，实现：

1. 启动 FastAPI 后端（端口 8000）作为主进程
2. 启动 Streamlit 前端（端口 8501）作为子进程
3. 自动打开浏览器访问前端
4. Ctrl+C 时优雅关闭两个进程

### 命令一览

| 命令 | 作用 |
|------|------|
| `python run.py gui` | 一键启动Web界面 |
| `python run.py web` | 只启动后端API |
| `python run.py search ...` | 命令行搜索 |
| `python run.py init` | 初始化系统 |
| `python run.py daemon` | 守护进程模式 |

### 技术实现

```python
def run_gui():
    import subprocess
    import webbrowser
    import time

    # 启动后端
    backend = subprocess.Popen([sys.executable, "-m", "uvicorn", ...])

    # 启动前端
    frontend = subprocess.Popen([sys.executable, "-m", "streamlit", "run", ...])

    # 打开浏览器
    time.sleep(2)
    webbrowser.open("http://localhost:8501")

    # 等待退出
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        backend.terminate()
        frontend.terminate()
```

## 影响范围

- 修改 `run.py`（约30行代码）
- 架构不变，仍保持前后端分离