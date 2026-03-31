# frontend_nicegui/components/buttons.py
"""按钮组件"""

from nicegui import ui


def render_action_button(label: str, icon: str = None, on_click=None, primary: bool = False):
    """渲染操作按钮"""
    btn_class = (
        'primary-btn px-4 py-2 rounded-lg text-sm font-semibold '
        'bg-gradient-to-r from-cyan-600 to-cyan-400 text-black'
        if primary else
        'action-btn px-4 py-2 rounded-lg text-sm font-semibold '
        'bg-[rgba(30,30,40,0.9)] border border-[#00d4ff] text-[#00d4ff]'
    )

    btn = ui.button(
        label,
        icon=icon,
        on_click=on_click
    ).classes(btn_class)

    return btn