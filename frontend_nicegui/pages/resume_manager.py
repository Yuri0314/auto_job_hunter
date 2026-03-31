# frontend_nicegui/pages/resume_manager.py
"""简历管理页面"""

import httpx
from nicegui import ui, app

from ..config import API_BASE


async def fetch_resumes():
    """获取简历列表"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{API_BASE}/resume/list", timeout=10)
            if r.is_success:
                return r.json()
    except Exception as e:
        ui.notify(f"获取简历列表失败: {e}", type='negative')
    return {"items": [], "total": 0}


async def delete_resume_api(resume_id: int):
    """删除简历"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.delete(f"{API_BASE}/resume/{resume_id}", timeout=10)
            return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def set_primary_api(resume_id: int):
    """设置主简历"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{API_BASE}/resume/{resume_id}/set-primary", timeout=10)
            return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def render_resume_manager():
    """渲染简历管理页面"""
    from ..layout import render_page_header

    render_page_header("RESUME_MANAGER", "简历管理 · 多简历支持 · 智能解析")

    # Tab 切换
    with ui.tabs().classes('w-full mb-4') as tabs:
        tab_list = ui.tab('简历列表', icon='list')
        tab_upload = ui.tab('上传简历', icon='upload')
        tab_paste = ui.tab('粘贴文本', icon='edit_note')

    with ui.tab_panels(tabs, value=tab_list).classes('w-full'):
        with ui.tab_panel(tab_list):
            _render_resume_list()

        with ui.tab_panel(tab_upload):
            ui.label("上传简历文件").classes('text-white font-semibold mb-2')
            ui.label("支持 PDF、Word、Markdown、TXT 格式").classes('text-[#9ca3af] text-sm')
            ui.upload(label="选择文件").classes('w-full')

        with ui.tab_panel(tab_paste):
            ui.label("粘贴简历内容").classes('text-white font-semibold mb-2')
            ui.textarea(placeholder="粘贴您的简历内容...").classes('w-full h-64')
            ui.button("解析文本").classes('primary-btn mt-4')


def _render_resume_list():
    """渲染简历列表"""
    resumes_data = {"items": [], "total": 0}
    container = ui.column().classes('w-full')

    async def load_resumes():
        nonlocal resumes_data
        resumes_data = await fetch_resumes()
        refresh_list()
        ui.notify("列表已刷新", type='positive')

    def refresh_list():
        container.clear()
        with container:
            items = resumes_data.get("items", [])
            if not items:
                ui.label("暂无简历，请上传或粘贴简历内容").classes('text-[#9ca3af] text-center py-8')
                return

            # 工具栏
            ui.button("刷新列表", icon="refresh", on_click=load_resumes).classes('action-btn mb-4')

            # 简历卡片
            for resume in items:
                _render_resume_card(resume, load_resumes)

    # 初始加载
    ui.timer(0.1, load_resumes, once=True)


def _render_resume_card(resume: dict, on_refresh):
    """渲染简历卡片"""
    resume_id = resume.get("id")
    is_primary = resume.get("is_primary", False)
    profile = resume.get("profile") or {}

    with ui.card().classes('w-full mb-2 p-4'):
        with ui.row().classes('w-full items-center justify-between'):
            # 左侧信息
            with ui.column().classes('flex-1'):
                with ui.row().classes('items-center gap-2'):
                    ui.label(resume.get("name", "未命名")).classes('text-white font-semibold text-lg')
                    if is_primary:
                        ui.badge("主简历", color='positive').classes('text-xs')

                ui.label(
                    f"{resume.get('file_type', '-').upper()} · "
                    f"{resume.get('created_at', '')[:10] if resume.get('created_at') else '-'}"
                ).classes('text-[#9ca3af] text-sm')

                if profile.get("current_position"):
                    ui.label(
                        f"{profile.get('current_position', '-')} · "
                        f"{profile.get('experience_years', '-')}年经验"
                    ).classes('text-[#c4c4c8] text-sm')

            # 右侧操作
            with ui.row().classes('gap-2'):
                ui.button("查看", on_click=lambda: _show_detail(resume)).classes('action-btn text-xs')

                if not is_primary:
                    async def do_set_primary(rid=resume_id):
                        result = await set_primary_api(rid)
                        if result.get("success"):
                            ui.notify("已设为主简历", type='positive')
                            await on_refresh()
                        else:
                            ui.notify(result.get("error", "设置失败"), type='negative')
                    ui.button("设为主简历", on_click=do_set_primary).classes('action-btn text-xs')

                async def do_delete(rid=resume_id):
                    result = await delete_resume_api(rid)
                    if result.get("success"):
                        ui.notify("删除成功", type='positive')
                        await on_refresh()
                    else:
                        ui.notify(result.get("error", "删除失败"), type='negative')
                ui.button("删除", on_click=do_delete).classes(
                    'bg-[rgba(248,113,113,0.15)] border border-[#f87171] text-[#f87171] text-xs'
                )


def _show_detail(resume: dict):
    """显示简历详情弹窗"""
    profile = resume.get("profile") or {}

    with ui.dialog() as dialog, ui.card().classes('w-[500px] p-4'):
        ui.label(f"简历详情: {resume.get('name')}").classes('text-xl font-bold mb-4')

        with ui.grid(columns=2).classes('w-full gap-2'):
            ui.label("姓名:").classes('text-[#9ca3af]')
            ui.label(profile.get("name", "-")).classes('text-white')
            ui.label("电话:").classes('text-[#9ca3af]')
            ui.label(profile.get("phone", "-")).classes('text-white')
            ui.label("邮箱:").classes('text-[#9ca3af]')
            ui.label(profile.get("email", "-")).classes('text-white')
            ui.label("职位:").classes('text-[#9ca3af]')
            ui.label(profile.get("current_position", "-")).classes('text-white')

        ui.button("关闭", on_click=dialog.close).classes('primary-btn mt-4')

    dialog.open()