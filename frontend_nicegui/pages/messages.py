# frontend_nicegui/pages/messages.py
"""消息中心页面"""

from nicegui import ui


def render_messages_page():
    """渲染消息中心页面"""
    from ..layout import render_page_header

    render_page_header("MESSAGES", "HR消息 · 自动回复")

    ui.label("消息中心功能开发中...").classes('text-[#9ca3af] text-center py-8')

    with ui.card().classes('w-full p-8'):
        ui.label("即将支持:").classes('text-white mb-2')
        ui.label("• 查看 HR 消息").classes('text-[#c4c4c8]')
        ui.label("• 智能自动回复").classes('text-[#c4c4c8]')
        ui.label("• 消息提醒").classes('text-[#c4c4c8]')