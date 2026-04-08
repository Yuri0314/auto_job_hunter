# frontend_nicegui/pages/resume_manager.py
"""简历管理页面"""

import httpx
from nicegui import ui, app

from ..config import API_BASE


async def fetch_resumes():
    """获取简历列表"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/resume/list", timeout=10)
            if r.is_success:
                return r.json()
    except Exception as e:
        ui.notify(f"获取简历列表失败: {e}", type='negative')
    return {"items": [], "total": 0}


async def one_click_job_api(platforms, max_apply=20, use_ai=False, auto_apply=True):
    """调用一键求职API"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(
                f"{API_BASE}/resume/one-click-job",
                json={
                    "platforms": platforms,
                    "max_apply": max_apply,
                    "use_ai_keywords": use_ai,
                    "auto_apply": auto_apply,
                },
                timeout=300,  # 一键求职可能耗时较长
            )
            return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def delete_resume_api(resume_id: int):
    """删除简历"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.delete(f"{API_BASE}/resume/{resume_id}", timeout=10)
            return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def set_primary_api(resume_id: int):
    """设置主简历"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(f"{API_BASE}/resume/{resume_id}/set-primary", timeout=10)
            return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def upload_resume_api(file_content: bytes, filename: str):
    """上传简历到API"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(
                f"{API_BASE}/resume/upload",
                files={"file": (filename, file_content)},
                timeout=60,
            )
            return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def parse_text_api(text: str):
    """解析粘贴的简历文本"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(
                f"{API_BASE}/resume/parse-text",
                json={"text": text, "use_ai": False},
                timeout=60,
            )
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

    # 创建简历列表容器，保存刷新函数引用
    list_container = ui.column().classes('w-full')
    refresh_list_fn = None

    with ui.tab_panels(tabs, value=tab_list).classes('w-full'):
        with ui.tab_panel(tab_list):
            refresh_list_fn = _render_resume_list(list_container)

        with ui.tab_panel(tab_upload):
            _render_upload_tab(tabs, refresh_list_fn)

        with ui.tab_panel(tab_paste):
            _render_paste_tab(tabs, refresh_list_fn)


def _render_resume_list(container):
    """渲染简历列表，返回刷新函数"""
    resumes_data = {"items": [], "total": 0}

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

    # 返回刷新函数供外部调用
    return load_resumes


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
                    # 优先显示解析出的姓名，如果没有则显示简历名称
                    display_name = (profile and profile.get("name")) or resume.get("name", "未命名")
                    ui.label(display_name).classes('text-white font-semibold text-lg')
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
                # 开始求职 - 主按钮
                async def start_job_search(r=resume, p=profile):
                    await _show_job_search_dialog(r, p)
                ui.button("🚀 开始求职", on_click=start_job_search).classes('primary-btn text-xs')

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


async def _show_job_search_dialog(resume: dict, profile: dict):
    """显示求职偏好确认弹窗"""
    # 从简历预填充偏好
    default_positions = (profile.get("target_positions") or []) if profile else []
    default_cities = (profile.get("preferred_cities") or []) if profile else []
    default_keywords = ", ".join(default_positions[:3]) if default_positions else ""
    default_cities_text = ", ".join(default_cities[:3]) if default_cities else ""

    with ui.dialog() as dialog, ui.card().classes('w-[480px] p-6'):
        ui.label("🚀 开始求职").classes('text-xl font-bold mb-2')
        ui.label("基于您的简历信息，为您推荐和投递匹配职位").classes('text-[#9ca3af] text-sm mb-4')

        # 目标职位
        ui.label("目标职位").classes('text-white font-semibold text-sm mb-1')
        keywords_input = ui.textarea(
            value=default_keywords,
            placeholder="如：Python开发工程师, 后端开发, 数据工程师",
        ).classes('w-full').props('outlined dense rows=2')
        ui.label("用逗号分隔多个职位关键词").classes('text-[#9ca3af] text-xs mb-3')

        # 意向城市
        ui.label("意向城市").classes('text-white font-semibold text-sm mb-1')
        cities_input = ui.textarea(
            value=default_cities_text,
            placeholder="如：北京, 上海, 深圳, 杭州",
        ).classes('w-full').props('outlined dense rows=2')
        ui.label("用逗号分隔多个城市").classes('text-[#9ca3af] text-xs mb-3')

        # 投递模式
        ui.label("投递模式").classes('text-white font-semibold text-sm mb-2')
        mode = ui.toggle({
            'smart': '🤖 智能探索',
            'manual': '🎯 手动筛选',
        }, value='smart').classes('w-full')

        with ui.row().classes('w-full items-center gap-3 mt-2'):
            auto_apply_checkbox = ui.checkbox("自动投递匹配的职位", value=True)

        with ui.row().classes('w-full items-center gap-3'):
            max_apply_input = ui.number(label="每日最多投递", value=20, min=1, max=100)
            platform_select = ui.select(
                options={'boss': 'BOSS直聘', 'liepin': '猎聘'},
                value='boss',
                label='目标平台',
            ).classes('flex-1')

        # 状态消息区
        status_label = ui.label().classes('text-sm')

        # 按钮
        with ui.row().classes('w-full justify-end gap-3 mt-4'):
            ui.button("取消", on_click=dialog.close).classes('action-btn')

            async def do_start():
                keywords = [k.strip() for k in keywords_input.value.split(",") if k.strip()]
                cities = [c.strip() for c in cities_input.value.split(",") if c.strip()]

                if not keywords:
                    ui.notify("请输入目标职位关键词", type='warning')
                    return

                # 关闭偏好弹窗
                dialog.close()

                # 显示进度弹窗
                await _show_progress_dialog(keywords, cities, mode.value,
                                            auto_apply_checkbox.value,
                                            int(max_apply_input.value),
                                            [platform_select.value])

            ui.button("开始求职", on_click=do_start).classes('primary-btn')

    dialog.open()


async def _show_progress_dialog(keywords, cities, mode, auto_apply, max_apply, platforms):
    """显示求职执行进度"""
    with ui.dialog() as dialog, ui.card().classes('w-[480px] p-6'):
        ui.label("🚀 求职进行中...").classes('text-xl font-bold mb-4')

        # 进度条
        progress = ui.linear_progress(value=0, show_value=True).classes('w-full')

        # 日志区
        log_container = ui.column().classes('w-full mt-4 max-h-[300px] overflow-y-auto')

        def add_log(msg):
            with log_container:
                ui.label(f"• {msg}").classes('text-[#9ca3af] text-sm')

        add_log(f"开始执行，关键词: {', '.join(keywords)}")
        add_log(f"目标城市: {', '.join(cities) if cities else '不限'}")
        add_log(f"平台: {', '.join(platforms)}")
        add_log("")

        # 执行一键求职
        try:
            progress.set_value(10)
            add_log("正在生成搜索关键词...")

            result = await one_click_job_api(
                platforms=platforms,
                max_apply=max_apply,
                use_ai=True,
                auto_apply=auto_apply and mode == 'smart',
            )

            progress.set_value(90)

            if result.get("success"):
                add_log(f"✅ 完成！发现 {result.get('total_found', 0)} 个职位")
                add_log(f"✅ 已投递 {result.get('total_applied', 0)} 个职位")
                progress.set_value(100)

                ui.notify(f"求职完成！已投递 {result.get('total_applied', 0)} 个职位",
                          type='positive', timeout=5000)

                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button("查看投递记录",
                              on_click=lambda: (dialog.close(),
                                                ui.navigate.to('/applications'))).classes('action-btn')
                    ui.button("查看消息", icon="mail",
                              on_click=lambda: (dialog.close(),
                                                ui.navigate.to('/messages'))).classes('primary-btn')
                    ui.button("关闭", on_click=dialog.close).classes('action-btn')
            else:
                add_log(f"❌ 执行失败: {result.get('error', '未知错误')}")
                progress.set_value(100)

                ui.notify(result.get("error", "执行失败"), type='negative')
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button("关闭", on_click=dialog.close).classes('primary-btn')

        except Exception as e:
            add_log(f"❌ 执行出错: {str(e)}")
            progress.set_value(100)
            ui.notify(f"执行出错: {str(e)}", type='negative')
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button("关闭", on_click=dialog.close).classes('primary-btn')

    dialog.open()


def _render_upload_tab(tabs, refresh_list_fn):
    """渲染上传简历Tab"""
    ui.label("上传简历文件").classes('text-white font-semibold mb-2')
    ui.label("支持 PDF、Word、Markdown、TXT 格式").classes('text-[#9ca3af] text-sm mb-4')

    upload_result_container = ui.column().classes('w-full')

    async def handle_upload(e):
        """处理文件上传"""
        try:
            # NiceGUI 3.0+: e.file 是 FileUpload 对象，不是 Starlette UploadFile
            # 使用 e.file.name 获取文件名，await e.file.read() 获取内容
            file_content = await e.file.read()
            filename = e.file.name

            upload_result_container.clear()
            with upload_result_container:
                ui.spinner(size='lg')
                ui.label("正在解析简历...").classes('text-[#9ca3af]')

            result = await upload_resume_api(file_content, filename)

            upload_result_container.clear()
            with upload_result_container:
                if result.get("success"):
                    ui.notify("简历上传成功！", type='positive', timeout=3000)
                    extracted = result.get("extracted_data", {})
                    if extracted:
                        with ui.card().classes('w-full p-4 mt-2'):
                            ui.label("解析结果").classes('text-white font-semibold mb-2')
                            with ui.grid(columns=2).classes('w-full gap-1'):
                                if extracted.get("name"):
                                    ui.label("姓名:").classes('text-[#9ca3af]')
                                    ui.label(extracted.get("name")).classes('text-white')
                                if extracted.get("phone"):
                                    ui.label("电话:").classes('text-[#9ca3af]')
                                    ui.label(extracted.get("phone")).classes('text-white')
                                if extracted.get("email"):
                                    ui.label("邮箱:").classes('text-[#9ca3af]')
                                    ui.label(extracted.get("email")).classes('text-white')
                    if refresh_list_fn:
                        await refresh_list_fn()
                    tabs.value = '简历列表'
                else:
                    ui.notify(result.get("error", "上传失败"), type='negative')
        except Exception as ex:
            ui.notify(f"上传出错: {str(ex)}", type='negative')

    ui.upload(
        label="选择文件",
        on_upload=handle_upload,
        auto_upload=True,
    ).classes('w-full')


def _render_paste_tab(tabs, refresh_list_fn):
    """渲染粘贴文本Tab"""
    ui.label("粘贴简历内容").classes('text-white font-semibold mb-2')
    ui.label("直接粘贴简历文本，系统会自动解析").classes('text-[#9ca3af] text-sm mb-4')

    paste_input = ui.textarea(
        placeholder="粘贴您的简历内容...",
    ).classes('w-full h-64')

    paste_result_container = ui.column().classes('w-full mt-4')

    async def handle_parse():
        """处理文本解析"""
        text = paste_input.value
        if not text or len(text) < 50:
            ui.notify("请粘贴完整的简历内容（至少50字）", type='warning')
            return

        paste_result_container.clear()
        with paste_result_container:
            ui.spinner(size='lg')
            ui.label("正在解析简历...").classes('text-[#9ca3af]')

        result = await parse_text_api(text)

        paste_result_container.clear()
        with paste_result_container:
            if result.get("success"):
                ui.notify("简历解析成功！", type='positive')
                extracted = result.get("extracted_data", {})
                if extracted:
                    with ui.card().classes('w-full p-4'):
                        ui.label("解析结果").classes('text-white font-semibold mb-2')
                        with ui.grid(columns=2).classes('w-full gap-1'):
                            if extracted.get("name"):
                                ui.label("姓名:").classes('text-[#9ca3af]')
                                ui.label(extracted.get("name")).classes('text-white')
                            if extracted.get("phone"):
                                ui.label("电话:").classes('text-[#9ca3af]')
                                ui.label(extracted.get("phone")).classes('text-white')
                            if extracted.get("email"):
                                ui.label("邮箱:").classes('text-[#9ca3af]')
                                ui.label(extracted.get("email")).classes('text-white')
                if refresh_list_fn:
                    await refresh_list_fn()
                tabs.value = '简历列表'
            else:
                ui.notify(result.get("error", "解析失败"), type='negative')

    ui.button("解析文本", on_click=handle_parse).classes('primary-btn')