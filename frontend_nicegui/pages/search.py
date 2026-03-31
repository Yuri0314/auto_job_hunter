# frontend_nicegui/pages/search.py
"""搜索职位页面"""

import httpx
from nicegui import ui

API_BASE = "http://localhost:8000/api"


async def search_jobs_api(keywords: str, platforms: list, city: str = None, auto_apply: bool = False):
    """调用搜索 API"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{API_BASE}/applications/search-and-apply",
                json={
                    "keywords": keywords,
                    "platforms": platforms,
                    "city": city,
                    "auto_apply": auto_apply,
                    "max_count": 20,
                },
                timeout=120
            )
            if r.is_success:
                return r.json()
            return {"success": False, "error": r.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def render_search_page():
    """渲染搜索页面"""
    from ..layout import render_page_header

    render_page_header("SEARCH_JOBS", "多平台搜索 · 智能过滤 · 自动投递")

    # 搜索表单
    with ui.card().classes('w-full p-4 mb-4'):
        ui.label("搜索条件").classes('text-white font-semibold mb-3')

        with ui.grid(columns=2).classes('w-full gap-4'):
            keywords_input = ui.input(
                label="搜索关键词",
                placeholder="如: Python后端"
            ).classes('col-span-2')

            platforms_select = ui.select(
                ['boss', 'liepin'],
                label="选择平台",
                multiple=True,
                value=['boss']
            )

            city_input = ui.input(
                label="目标城市",
                placeholder="如: 北京"
            )

        auto_apply_check = ui.checkbox("自动投递符合条件的职位").classes('mt-2')

    # 结果容器
    results_container = ui.column().classes('w-full')

    async def do_search():
        keywords = keywords_input.value
        platforms = platforms_select.value
        city = city_input.value
        auto_apply = auto_apply_check.value

        if not keywords:
            ui.notify("请输入搜索关键词", type='warning')
            return
        if not platforms:
            ui.notify("请选择至少一个平台", type='warning')
            return

        # 显示加载
        results_container.clear()
        with results_container:
            ui.spinner(size='lg')
            ui.label("正在搜索职位，请稍候...").classes('text-[#9ca3af]')

        # 调用 API
        result = await search_jobs_api(keywords, platforms, city, auto_apply)

        # 显示结果
        results_container.clear()
        with results_container:
            if result.get("error"):
                ui.notify(f"搜索失败: {result.get('error')}", type='negative')
                return

            total = result.get("total_found", 0)
            filtered = result.get("filtered", 0)
            applied = result.get("applied", 0)

            ui.label(f"发现: {total} | 符合条件: {filtered} | 已投递: {applied}").classes(
                'text-[#00d4ff] font-mono mb-4'
            )

            jobs = result.get("jobs", [])
            if not jobs:
                ui.label("没有找到符合条件的职位").classes('text-[#9ca3af]')
            else:
                for job in jobs:
                    _render_job_card(job)

    ui.button("开始搜索", icon="search", on_click=do_search).classes('primary-btn mt-4')


def _render_job_card(job: dict):
    """渲染职位卡片"""
    with ui.card().classes('w-full mb-2 p-4'):
        with ui.row().classes('w-full justify-between items-start'):
            with ui.column():
                ui.label(job.get("title", "未知职位")).classes('text-white font-semibold')
                ui.label(
                    f"{job.get('company', '-')} | {job.get('city', '-')} | "
                    f"{job.get('salary', '-')} | {job.get('platform', '-').upper()}"
                ).classes('text-[#9ca3af] text-sm')

        with ui.row().classes('gap-2 mt-2'):
            ui.button("详情", on_click=lambda: _show_job_detail(job)).classes('action-btn text-xs')

            url = job.get("url")
            if url:
                ui.link("原链接", url, new_tab=True).classes(
                    'action-btn text-xs no-underline'
                )


def _show_job_detail(job: dict):
    """显示职位详情弹窗"""
    with ui.dialog() as dialog, ui.card().classes('w-[500px] p-4'):
        ui.label(f"职位详情: {job.get('title')}").classes('text-xl font-bold mb-4')

        with ui.column().classes('w-full gap-1'):
            ui.label(f"公司: {job.get('company', '-')}").classes('text-white')
            ui.label(f"城市: {job.get('city', '-')}").classes('text-white')
            ui.label(f"薪资: {job.get('salary', '-')}").classes('text-white')
            ui.label(f"平台: {job.get('platform', '-').upper()}").classes('text-white')

        if job.get("description"):
            ui.label("职位描述").classes('text-[#00d4ff] mt-4 mb-2')
            desc = job.get("description", "")
            ui.label(desc[:500] + ("..." if len(desc) > 500 else "")).classes('text-[#c4c4c8] text-sm')

        ui.button("关闭", on_click=dialog.close).classes('primary-btn mt-4')

    dialog.open()