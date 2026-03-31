# frontend_nicegui/components/cards.py
"""卡片组件"""

from nicegui import ui
from ..styles import COLORS


def render_stat_card(label: str, value: str, color: str = None):
    """渲染统计卡片"""
    bg_color = COLORS.get("bg_hover", "rgba(255, 255, 255, 0.05)")
    border_color = COLORS.get("border_default", "rgba(255, 255, 255, 0.12)")
    text_color = COLORS.get(color, COLORS["accent_blue"]) if color else COLORS["accent_blue"]

    with ui.card().classes(
        f'w-full p-4 rounded-lg bg-[{bg_color}] border border-[{border_color}]'
    ):
        ui.label(value).classes(
            f'text-[{text_color}] font-mono text-xl font-bold'
        )
        ui.label(label).classes(
            f'text-[{COLORS["text_muted"]}] text-xs mt-1'
        )


def render_status_indicator(label: str, is_online: bool):
    """渲染状态指示器"""
    status_color = COLORS["accent_green"] if is_online else COLORS["accent_red"]
    status_text = "在线" if is_online else "离线"
    icon = "check_circle" if is_online else "cancel"

    with ui.card().classes(
        'w-full p-3 rounded-lg bg-[rgba(255,255,255,0.05)] '
        'border border-[rgba(255,255,255,0.12)]'
    ):
        with ui.row().classes('items-center gap-2'):
            ui.icon(icon).classes(f'text-{status_color}')
            ui.label(label).classes('text-white text-sm font-medium')
            ui.label(status_text).classes(
                f'text-[{status_color}] text-xs ml-auto'
            )