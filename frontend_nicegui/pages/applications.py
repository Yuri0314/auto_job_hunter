# frontend_nicegui/pages/applications.py
"""投递记录页面"""

import asyncio
import httpx
from nicegui import ui

from ..config import API_BASE
from ..components.job_info import render_application_row


async def fetch_applications(status: str = None, platform: str = None, page: int = 1, page_size: int = 20):
    """获取投递记录列表"""
    try:
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if platform:
            params["platform"] = platform

        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/applications", params=params, timeout=30)
            if r.is_success:
                return r.json()
            return {"total": 0, "items": []}
    except Exception:
        return {"total": 0, "items": []}


async def fetch_statistics(days: int = 7):
    """获取投递统计"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/applications/statistics", params={"days": days}, timeout=30)
            if r.is_success:
                return r.json()
            return {}
    except Exception:
        return {}


async def retry_application(application_id: int):
    """重试失败的投递"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(f"{API_BASE}/applications/{application_id}/retry", timeout=60)
            if r.is_success:
                result = r.json()
                if result.get("success"):
                    ui.notify("重试成功！", type='positive')
                else:
                    ui.notify(f"重试失败: {result.get('message')}", type='warning')
            else:
                ui.notify(f"重试失败: {r.text}", type='negative')
    except Exception as e:
        ui.notify(f"重试异常: {e}", type='negative')


def render_applications_page():
    """渲染投递记录页面"""
    from ..layout import render_page_header

    render_page_header("APPLICATIONS", "投递记录 · 状态追踪")

    # 顶部操作栏
    with ui.card().classes('w-full p-4 mb-4'):
        with ui.row().classes('w-full gap-4 items-end'):
            ui.button("📧 查看消息", icon="mail",
                      on_click=lambda: ui.navigate.to('/messages')).classes('action-btn')

    # 统计区域
    stats_container = ui.row().classes('w-full gap-4 mb-4')

    # 筛选区域
    with ui.card().classes('w-full p-4 mb-4'):
        with ui.row().classes('w-full gap-4 items-end'):
            status_select = ui.select(
                ['all', 'success', 'failed', 'pending'],
                label="状态",
                value='all'
            ).classes('w-40')

            platform_select = ui.select(
                ['all', 'boss', 'liepin'],
                label="平台",
                value='all'
            ).classes('w-40')

            ui.button("刷新", icon="refresh", on_click=lambda: load_applications()).classes('action-btn')

    # 投递记录列表
    list_container = ui.column().classes('w-full')

    # 分页信息
    pagination_label = ui.label().classes('text-[#6b7280] text-sm mt-4')

    async def load_applications(page: int = 1):
        """加载投递记录"""
        list_container.clear()

        with list_container:
            ui.spinner(size='md')
            ui.label("加载中...").classes('text-[#9ca3af]')

        # 并行加载统计和列表
        status = status_select.value if status_select.value != 'all' else None
        platform = platform_select.value if platform_select.value != 'all' else None

        stats_data, apps_data = await asyncio.gather(
            fetch_statistics(),
            fetch_applications(status=status, platform=platform, page=page, page_size=20),
        )

        # 渲染统计
        stats_container.clear()
        with stats_container:
            total = stats_data.get('total', 0)
            success = stats_data.get('success', 0)
            failed = stats_data.get('failed', 0)
            rate = stats_data.get('success_rate', 0)

            _render_mini_stat("总投递", str(total), "accent_blue")
            _render_mini_stat("成功", str(success), "accent_green")
            _render_mini_stat("失败", str(failed), "accent_red")
            _render_mini_stat("成功率", f"{rate}%", "accent_purple")

        # 渲染列表
        list_container.clear()
        items = apps_data.get('items', [])
        total_count = apps_data.get('total', 0)

        with list_container:
            if not items:
                ui.label("暂无投递记录").classes('text-[#9ca3af] text-center py-8')
            else:
                with ui.card().classes('w-full p-0'):
                    # 表头
                    with ui.row().classes('w-full items-center py-2 px-4 border-b border-[#1f2937] bg-[#ffffff]/5'):
                        ui.label("投递时间").classes('text-[#6b7280] text-xs flex-1')
                        ui.label("平台").classes('text-[#6b7280] text-xs w-32')
                        ui.label("状态").classes('text-[#6b7280] text-xs w-24')
                        ui.label("操作").classes('text-[#6b7280] text-xs w-20')

                    # 列表项
                    for app in items:
                        render_application_row(app, on_retry=_handle_retry)

        # 分页信息
        pagination_label.text = f"第 {page} 页，共 {total_count} 条记录"

        # 分页按钮
        with list_container:
            with ui.row().classes('w-full justify-center gap-4 mt-4'):
                if page > 1:
                    ui.button("上一页", icon="chevron_left",
                              on_click=lambda: load_applications(page - 1)).classes('action-btn')

                if page * 20 < total_count:
                    ui.button("下一页", icon="chevron_right",
                              on_click=lambda: load_applications(page + 1)).classes('action-btn')

    async def _handle_retry(app: dict):
        """处理重试按钮"""
        await retry_application(app['id'])
        await load_applications()

    def _render_mini_stat(label: str, value: str, color: str):
        """渲染迷你统计卡片"""
        color_map = {
            "accent_blue": "#00d4ff",
            "accent_green": "#22c55e",
            "accent_red": "#ef4444",
            "accent_purple": "#a855f7",
        }
        color_val = color_map.get(color, "#00d4ff")
        with ui.column().classes('bg-[#ffffff]/5 rounded-lg p-4 min-w-[120px]'):
            ui.label(value).classes(f'text-2xl font-bold').style(f'color: {color_val}')
            ui.label(label).classes('text-[#6b7280] text-xs')

    # 初始加载
    ui.timer(0.1, lambda: asyncio.create_task(load_applications()), once=True)
