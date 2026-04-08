# frontend_nicegui/pages/dashboard.py
"""仪表盘页面 - 求职者视角的求职进展总览"""

import httpx
from nicegui import ui
from datetime import datetime, timedelta

from ..config import API_BASE


# ============== API 调用 ==============

async def fetch_application_stats():
    """获取投递统计数据"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            # 获取投递列表（取前100条用于统计）
            r = await client.get(f"{API_BASE}/applications", params={"page": 1, "page_size": 100}, timeout=10)
            if r.is_success:
                data = r.json()
                items = data.get("items", [])
                total = data.get("total", 0)

                # 按状态分类统计
                stats = {"pending": 0, "viewed": 0, "interview": 0, "rejected": 0, "offer": 0, "total": total}
                today_count = 0
                today = datetime.now().strftime("%Y-%m-%d")

                for item in items:
                    status = item.get("status", "")
                    stats[status] = stats.get(status, 0) + 1

                    # 今日投递
                    created_at = item.get("created_at", "")
                    if created_at and created_at[:10] == today:
                        today_count += 1

                stats["today"] = today_count
                return stats
    except Exception:
        pass
    return {"pending": 0, "viewed": 0, "interview": 0, "rejected": 0, "offer": 0, "total": 0, "today": 0}


async def fetch_recent_applications(limit=5):
    """获取最近投递记录"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/applications", params={"page": 1, "page_size": limit}, timeout=10)
            if r.is_success:
                return r.json().get("items", [])
    except Exception:
        pass
    return []


async def fetch_resume_status():
    """获取简历状态"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/resume/status", timeout=10)
            if r.is_success:
                return r.json()
    except Exception:
        pass
    return {"has_resume": False}


async def fetch_platform_status():
    """获取平台登录状态"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/system/platforms", timeout=10)
            if r.is_success:
                return r.json().get("platforms", [])
    except Exception:
        pass
    return []


# ============== UI 组件 ==============

def _render_stat_card(label, value, icon="trending_up", color="blue"):
    """渲染统计卡片"""
    color_map = {
        "blue": "from-[#00d4ff]/20 to-[#00d4ff]/5 border-[#00d4ff]/30",
        "green": "from-[#10b981]/20 to-[#10b981]/5 border-[#10b981]/30",
        "yellow": "from-[#fbbf24]/20 to-[#fbbf24]/5 border-[#fbbf24]/30",
        "purple": "from-[#a855f7]/20 to-[#a855f7]/5 border-[#a855f7]/30",
        "red": "from-[#ef4444]/20 to-[#ef4444]/5 border-[#ef4444]/30",
    }
    gradient = color_map.get(color, color_map["blue"])

    with ui.card().classes(f'p-4 min-w-[140px] bg-gradient-to-br {gradient}'):
        with ui.row().classes('items-center gap-2'):
            ui.icon(icon, size='sm').classes('text-[#00d4ff]')
            ui.label(label).classes('text-[#9ca3af] text-sm')
        ui.label(str(value)).classes('text-white font-bold text-2xl mt-1')


def _render_status_badge(status):
    """渲染状态标签"""
    status_styles = {
        "pending": ("等待回应", "bg-[#00d4ff]/20 text-[#00d4ff]"),
        "viewed": ("已读", "bg-[#10b981]/20 text-[#10b981]"),
        "interview": ("面试", "bg-[#fbbf24]/20 text-[#fbbf24]"),
        "rejected": ("拒绝", "bg-[#ef4444]/20 text-[#ef4444]"),
        "offer": ("Offer", "bg-[#a855f7]/20 text-[#a855f7]"),
    }
    text, style = status_styles.get(status, (status, "bg-gray-700 text-gray-300"))
    ui.label(text).classes(f'text-xs px-2 py-0.5 rounded {style}')


def _render_application_row(app, on_click):
    """渲染单条投递记录"""
    with ui.row().classes('items-center justify-between py-3 border-b border-[#1e1e24] hover:bg-white/5 px-3 -mx-3 cursor-pointer'):
        with ui.column().classes('flex-1'):
            ui.label(app.get("job_title", "未知职位")).classes('text-white text-sm font-medium')
            ui.label(f"{app.get('company', '未知公司')} · {app.get('platform', '-')}").classes('text-[#9ca3af] text-xs')
        with ui.column().classes('items-end'):
            _render_status_badge(app.get("status", "pending"))
            created_at = app.get("created_at", "")
            if created_at:
                ui.label(created_at[:10]).classes('text-[#9ca3af] text-xs mt-1')


# ============== 主页面 ==============

def render_dashboard():
    """渲染仪表盘页面"""
    from ..layout import render_page_header

    render_page_header("DASHBOARD", "求职进展总览")

    # 数据容器
    stats = {"total": 0, "today": 0, "pending": 0, "viewed": 0, "interview": 0}
    recent_apps = []
    resume_status = {"has_resume": False}
    platforms = []

    async def load_data():
        nonlocal stats, recent_apps, resume_status, platforms
        stats, recent_apps, resume_status, platforms = await asyncio.gather(
            fetch_application_stats(),
            fetch_recent_applications(5),
            fetch_resume_status(),
            fetch_platform_status(),
        )
        refresh_ui()

    def refresh_ui():
        content.clear()
        with content:
            _render_overview_section(stats, resume_status, platforms)
            _render_quick_actions(resume_status)
            _render_recent_applications(recent_apps)

    async def refresh_all():
        with ui.notify("刷新中...", type='info'):
            await load_data()
        ui.notify("数据已更新", type='positive')

    content = ui.column().classes('w-full')
    ui.timer(0.1, load_data, once=True)


def _render_overview_section(stats, resume_status, platforms):
    """渲染概览区域"""
    ui.label("今日概览").classes('text-white font-semibold text-lg mb-3')

    with ui.row().classes('w-full gap-3'):
        _render_stat_card("累计投递", stats.get("total", 0), "send", "blue")
        _render_stat_card("今日投递", stats.get("today", 0), "today", "green")
        _render_stat_card("等待回应", stats.get("pending", 0), "hourglass_empty", "yellow")
        _render_stat_card("已读", stats.get("viewed", 0), "visibility", "green")
        _render_stat_card("面试邀请", stats.get("interview", 0), "meeting_room", "purple")


def _render_quick_actions(resume_status):
    """渲染快速操作区"""
    with ui.card().classes('w-full p-4 mt-4'):
        ui.label("快速操作").classes('text-white font-semibold mb-3')
        with ui.row().classes('w-full gap-3'):
            # 搜索职位
            ui.button("🔍 搜索职位", on_click=lambda: ui.navigate.to('/search')).classes('action-btn')

            # 管理简历
            ui.button("📄 管理简历", on_click=lambda: ui.navigate.to('/resumes')).classes('action-btn')

            # 投递记录
            ui.button("📋 投递记录", on_click=lambda: ui.navigate.to('/applications')).classes('action-btn')

            # 消息中心
            ui.button("💬 消息中心", on_click=lambda: ui.navigate.to('/messages')).classes('action-btn')

            # 系统设置
            ui.button("⚙️ 设置", on_click=lambda: ui.navigate.to('/settings')).classes('action-btn')


def _render_recent_applications(recent_apps):
    """渲染最近投递区域"""
    with ui.card().classes('w-full p-4 mt-4'):
        with ui.row().classes('w-full items-center justify-between mb-3'):
            ui.label("最近投递").classes('text-white font-semibold')
            if recent_apps:
                ui.button("查看全部", icon="arrow_forward",
                          on_click=lambda: ui.navigate.to('/applications')).classes('text-xs text-[#00d4ff]')

        if not recent_apps:
            with ui.column().classes('w-full items-center justify-center py-8'):
                ui.icon("send", size='3em').classes('text-[#9ca3af] mb-2')
                ui.label("暂无投递记录").classes('text-[#9ca3af]')
                ui.label("去搜索职位开始投递吧").classes('text-[#9ca3af] text-sm')
                with ui.row().classes('mt-3'):
                    ui.button("搜索职位", icon="search",
                              on_click=lambda: ui.navigate.to('/search')).classes('primary-btn')
        else:
            for app in recent_apps:
                _render_application_row(app, None)


# 需要 asyncio.gather
import asyncio
