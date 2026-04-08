# frontend_nicegui/layout.py
"""布局模块 - 侧边栏导航"""

from nicegui import ui, app
from .styles import COLORS, GLOBAL_CSS


# 导航项配置
NAV_ITEMS = [
    {"id": "dashboard", "label": "仪表盘", "icon": "home"},
    {"id": "resumes", "label": "管理简历", "icon": "description"},
    {"id": "search", "label": "搜索职位", "icon": "search"},
    {"id": "applications", "label": "投递记录", "icon": "send", "badge": None},
    {"id": "messages", "label": "消息中心", "icon": "message", "badge": None},
    {"id": "settings", "label": "设置", "icon": "settings"},
]


def navigate_to(page_id: str):
    """导航到指定页面"""
    ui.navigate.to(f'/{page_id}')


def render_sidebar():
    """渲染侧边栏"""
    # 添加全局样式（每个页面都需要）
    ui.add_head_html(GLOBAL_CSS)

    with ui.left_drawer().classes(
        'w-56 bg-[#16161d] border-r border-[rgba(255,255,255,0.12)]'
    ) as drawer:
        # Logo
        ui.label('AUTO_JOB_HUNTER').classes(
            'text-[#00d4ff] font-mono font-bold text-lg text-center py-4'
        )
        ui.html('<div style="height: 1px; background: rgba(255,255,255,0.12); margin: 0.5rem 1rem;"></div>')

        # 导航菜单
        for item in NAV_ITEMS:
            badge = item.get('badge')
            with ui.button(
                item['label'],
                icon=item['icon'],
                on_click=lambda p=item['id']: navigate_to(p)
            ).classes(
                'w-full justify-start text-[#c4c4c8] font-mono text-sm '
                'bg-transparent hover:bg-[rgba(255,255,255,0.05)] '
                'border-none shadow-none mb-1'
            ):
                if badge is not None and badge > 0:
                    with ui.badge().classes('absolute top-0 right-0 bg-[#ef4444] text-white text-xs min-w-[1.25rem] h-5 flex items-center justify-center rounded-full').style('font-size: 0.65rem; padding: 0 0.3rem;'):
                        ui.label(str(badge) if badge < 100 else '99+').classes('text-white text-xs')

        # 底部版本信息
        ui.space()
        with ui.column().classes('w-full p-4'):
            ui.label('v1.0.0').classes(
                'text-[#9ca3af] text-xs text-center font-mono'
            )

    return drawer


def render_page_header(title: str, subtitle: str = None):
    """渲染页面标题"""
    with ui.column().classes('w-full items-center mb-6'):
        ui.label(title).classes(
            'text-[#00d4ff] font-mono text-2xl font-bold'
        )
        if subtitle:
            ui.label(subtitle).classes(
                'text-[#71717a] text-sm mt-1'
            )


async def refresh_badges():
    """刷新侧边栏角标数据"""
    import httpx
    from .config import API_BASE

    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            # 获取未读消息数
            r = await client.get(f"{API_BASE}/messages", params={"page": 1, "page_size": 1}, timeout=10)
            if r.is_success:
                data = r.json()
                unread = data.get("unread", 0)
                for item in NAV_ITEMS:
                    if item["id"] == "messages":
                        item["badge"] = unread if unread > 0 else None

            # 获取失败的投递数
            r = await client.get(f"{API_BASE}/applications", params={"page": 1, "page_size": 100}, timeout=10)
            if r.is_success:
                data = r.json()
                failed = sum(1 for item in data.get("items", []) if item.get("status") == "failed")
                for nav_item in NAV_ITEMS:
                    if nav_item["id"] == "applications":
                        nav_item["badge"] = failed if failed > 0 else None
    except Exception:
        pass