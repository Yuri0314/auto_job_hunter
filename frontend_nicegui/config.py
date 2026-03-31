# frontend_nicegui/config.py
"""前端配置"""

import os

# API基础地址 - 优先从环境变量获取，否则使用默认值
# NiceGUI和FastAPI同进程运行，使用相同的端口
API_BASE = os.environ.get("API_BASE", "http://localhost:8000/api")


def set_api_base(port: int):
    """设置API端口（在启动时调用）"""
    global API_BASE
    API_BASE = f"http://localhost:{port}/api"