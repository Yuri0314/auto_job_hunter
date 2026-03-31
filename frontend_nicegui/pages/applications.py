# frontend_nicegui/pages/applications.py
"""投递记录页面"""

from nicegui import ui


def render_applications_page():
    """渲染投递记录页面"""
    from ..layout import render_page_header

    render_page_header("APPLICATIONS", "投递记录 · 状态追踪")

    ui.label("投递记录功能开发中...").classes('text-[#9ca3af] text-center py-8')

    with ui.card().classes('w-full p-8'):
        ui.label("即将支持:").classes('text-white mb-2')
        ui.label("• 查看所有投递记录").classes('text-[#c4c4c8]')
        ui.label("• 按状态筛选").classes('text-[#c4c4c8]')
        ui.label("• 查看投递详情").classes('text-[#c4c4c8]')