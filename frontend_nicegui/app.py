# frontend_nicegui/app.py
"""NiceGUI 应用入口"""

from nicegui import ui, app
from fastapi import FastAPI

from .styles import COLORS, GLOBAL_CSS
from .layout import render_sidebar
from .config import set_api_base


def setup_nicegui(fastapi_app: FastAPI, port: int = 8000):
    """将 NiceGUI 挂载到 FastAPI 应用"""

    # 设置API地址
    set_api_base(port)

    # 定义页面路由
    @ui.page('/dashboard')
    def dashboard_page():
        render_sidebar()
        from .pages.dashboard import render_dashboard
        render_dashboard()

    @ui.page('/resumes')
    def resumes_page():
        render_sidebar()
        from .pages.resume_manager import render_resume_manager
        render_resume_manager()

    @ui.page('/search')
    def search_page():
        render_sidebar()
        from .pages.search import render_search_page
        render_search_page()

    @ui.page('/applications')
    def applications_page():
        render_sidebar()
        from .pages.applications import render_applications_page
        render_applications_page()

    @ui.page('/messages')
    def messages_page():
        render_sidebar()
        from .pages.messages import render_messages_page
        render_messages_page()

    @ui.page('/settings')
    def settings_page():
        render_sidebar()
        from .pages.settings import render_settings_page
        render_settings_page()

    # 挂载到 FastAPI，启用暗黑模式
    ui.run_with(
        fastapi_app,
        mount_path='/ui',
        title='Auto Job Hunter',
        favicon='⚡',
        dark=True,
    )