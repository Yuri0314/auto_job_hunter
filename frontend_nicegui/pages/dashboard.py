# frontend_nicegui/pages/dashboard.py
"""仪表盘页面"""

import httpx
from nicegui import ui

API_BASE = "http://localhost:8000/api"


async def fetch_overview():
    """获取仪表盘概览数据"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{API_BASE}/dashboard/overview", timeout=10)
            if r.is_success:
                return r.json()
    except Exception as e:
        ui.notify(f"获取数据失败: {e}", type='negative')
    return {}


def render_dashboard():
    """渲染仪表盘页面"""
    from ..layout import render_page_header
    from ..components import render_stat_card, render_status_indicator

    render_page_header("DASHBOARD", "系统状态总览")

    # 数据容器
    overview = {"platform_status": [], "today_applications": 0, "has_resume": False}

    async def load_data():
        nonlocal overview
        overview = await fetch_overview()
        ui.notify("数据已更新", type='positive')
        refresh_ui()

    def refresh_ui():
        content.clear()
        with content:
            # 平台状态区
            with ui.card().classes('w-full p-4 mb-4'):
                ui.label("平台状态").classes('text-white font-semibold mb-3')
                with ui.row().classes('w-full gap-4'):
                    platforms = overview.get("platform_status", [])
                    if platforms:
                        for p in platforms:
                            render_status_indicator(
                                p.get("platform", "").upper(),
                                p.get("logged_in", False)
                            )
                    else:
                        ui.label("暂无平台数据").classes('text-[#9ca3af]')

            # 统计数据区
            with ui.row().classes('w-full gap-4 mb-4'):
                render_stat_card("今日投递", str(overview.get("today_applications", 0)))
                render_stat_card("简历状态", "已上传" if overview.get("has_resume") else "未上传")

            # 快速操作区
            with ui.card().classes('w-full p-4 mb-4'):
                ui.label("快速操作").classes('text-white font-semibold mb-3')
                with ui.row().classes('w-full gap-3'):
                    ui.button("搜索职位", icon="search",
                              on_click=lambda: ui.navigate.to('/search')).classes('action-btn')
                    ui.button("管理简历", icon="description",
                              on_click=lambda: ui.navigate.to('/resumes')).classes('action-btn')
                    ui.button("投递记录", icon="send",
                              on_click=lambda: ui.navigate.to('/applications')).classes('action-btn')

    content = ui.column().classes('w-full')

    # 初始加载
    ui.timer(0.1, load_data, once=True)

    # 刷新按钮
    ui.button("刷新数据", icon="refresh", on_click=load_data).classes('primary-btn mt-4')