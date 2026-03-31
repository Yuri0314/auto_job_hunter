# frontend_nicegui/app.py
"""NiceGUI 应用入口"""

from nicegui import ui
from fastapi import FastAPI

from .styles import apply_styles
from .layout import render_sidebar


def setup_nicegui(fastapi_app: FastAPI):
    """将 NiceGUI 挂载到 FastAPI 应用"""

    # 应用全局样式
    apply_styles()

    # 渲染侧边栏（全局布局）
    render_sidebar()

    # 定义页面路由
    @ui.page('/')
    def index():
        """首页 - 重定向到仪表盘"""
        ui.navigate.to('/dashboard')

    @ui.page('/dashboard')
    def dashboard_page():
        from .pages.dashboard import render_dashboard
        render_dashboard()

    @ui.page('/resumes')
    def resumes_page():
        from .pages.resume_manager import render_resume_manager
        render_resume_manager()

    @ui.page('/search')
    def search_page():
        from .pages.search import render_search_page
        render_search_page()

    @ui.page('/applications')
    def applications_page():
        from .pages.applications import render_applications_page
        render_applications_page()

    @ui.page('/messages')
    def messages_page():
        from .pages.messages import render_messages_page
        render_messages_page()

    @ui.page('/settings')
    def settings_page():
        from .pages.settings import render_settings_page
        render_settings_page()

    # 挂载到 FastAPI
    ui.run_with(
        fastapi_app,
        mount_path='/ui',
        title='Auto Job Hunter',
        favicon='⚡',
    )