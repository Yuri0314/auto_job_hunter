# frontend_nicegui/pages/settings.py
"""设置页面"""

import httpx
from nicegui import ui

from ..config import API_BASE


def _render_platform_login():
    """渲染平台登录状态"""
    ui.label("平台登录状态").classes('text-white font-semibold mb-2')
    ui.label("点击\"登录\"后，在打开的浏览器窗口中完成登录").classes(
        'text-[#9ca3af] text-sm mb-4'
    )

    container = ui.column().classes('w-full')

    platform_names = {
        "boss": "BOSS直聘",
        "liepin": "猎聘",
        "maimai": "脉脉",
    }

    def refresh_platforms(platforms_data):
        """刷新平台列表"""
        container.clear()
        with container:
            if not platforms_data:
                ui.label("未获取到平台数据").classes('text-[#9ca3af]')
                return

            for p in platforms_data:
                platform_id = p.get("platform")
                cookie_saved = p.get("cookie_saved", False)

                with ui.card().classes('w-full p-3 mb-2'):
                    with ui.row().classes('w-full items-center justify-between'):
                        ui.label(platform_names.get(platform_id, platform_id)).classes(
                            'text-white font-medium'
                        )
                        if cookie_saved:
                            ui.badge("已登录", color='positive')
                        else:
                            ui.badge("未登录", color='negative')

                    with ui.row().classes('gap-2 mt-2'):
                        ui.button(
                            "登录",
                            on_click=lambda pid=platform_id: _do_login_wrapper(pid)
                        ).classes('action-btn text-xs')

                        if cookie_saved:
                            ui.button(
                                "退出",
                                on_click=lambda pid=platform_id: _do_logout_wrapper(pid)
                            ).classes('bg-[rgba(248,113,113,0.15)] border border-[#f87171] text-[#f87171] text-xs')

    async def load_status():
        """加载平台状态"""
        try:
            async with httpx.AsyncClient(http2=False, trust_env=False) as client:
                r = await client.get(f"{API_BASE}/system/platforms", timeout=10)
                if r.is_success:
                    platforms_data = r.json()
                    refresh_platforms(platforms_data)
                else:
                    ui.notify(f"API错误: {r.status_code}", type='negative')
        except Exception as e:
            ui.notify(f"加载失败: {e}", type='negative')

    async def _do_login_wrapper(platform_id: str):
        """执行登录"""
        try:
            async with httpx.AsyncClient(http2=False, trust_env=False) as client:
                r = await client.post(f"{API_BASE}/system/login/{platform_id}", timeout=10)
                result = r.json()
                if result.get("status") == "started":
                    ui.notify("请在打开的浏览器中完成登录", type='info')
                else:
                    ui.notify(result.get("error", "启动失败"), type='negative')
        except Exception as e:
            ui.notify(f"登录失败: {e}", type='negative')

    async def _do_logout_wrapper(platform_id: str):
        """执行退出"""
        try:
            async with httpx.AsyncClient(http2=False, trust_env=False) as client:
                r = await client.post(f"{API_BASE}/system/logout/{platform_id}", timeout=10)
                result = r.json()
                if "error" not in result:
                    ui.notify("已退出登录", type='positive')
                    await load_status()
                else:
                    ui.notify(result.get("error", "退出失败"), type='negative')
        except Exception as e:
            ui.notify(f"退出失败: {e}", type='negative')

    # 刷新按钮
    ui.button("刷新状态", icon="refresh", on_click=load_status).classes('action-btn mb-4')

    # 初始加载
    ui.timer(0.1, load_status, once=True)


def _render_ai_config():
    """渲染 AI 配置"""
    ui.label("AI模型配置").classes('text-white font-semibold mb-2')
    ui.label("配置 OpenAI 或 Ollama 用于智能匹配").classes('text-[#9ca3af] text-sm mb-4')

    with ui.card().classes('w-full p-4'):
        ui.label("OpenAI").classes('text-white font-medium mb-2')
        ui.input(label="API Key", password=True, placeholder="sk-...").classes('w-full mb-2')
        ui.select(['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'], label="模型").classes('w-full mb-4')

        ui.label("Ollama (本地模型)").classes('text-white font-medium mb-2')
        ui.input(label="服务地址", placeholder="http://localhost:11434").classes('w-full mb-2')
        ui.input(label="模型名称", placeholder="llama3, qwen2").classes('w-full mb-4')

        ui.button("保存配置", on_click=lambda: ui.notify("配置已保存", type='positive')).classes(
            'primary-btn'
        )


def _render_system_config():
    """渲染系统配置"""
    ui.label("系统配置").classes('text-white font-semibold mb-4')

    with ui.card().classes('w-full p-4'):
        ui.checkbox("启用调试模式").classes('mb-2')
        ui.select(['DEBUG', 'INFO', 'WARNING', 'ERROR'], label="日志级别", value='INFO').classes(
            'w-full mb-2'
        )
        ui.checkbox("启用定时调度").classes('mb-2')
        ui.slider(min=1, max=20, value=5).props('label="最大并发数"').classes('w-full mb-4')

        ui.button("保存配置", on_click=lambda: ui.notify("配置已保存", type='positive')).classes(
            'primary-btn'
        )


def render_settings_page():
    """渲染设置页面"""
    from ..layout import render_page_header

    render_page_header("SETTINGS", "系统配置 · AI模型 · 平台登录")

    # Tab 布局
    with ui.tabs().classes('w-full mb-4') as tabs:
        tab_platform = ui.tab('平台登录', icon='login')
        tab_ai = ui.tab('AI配置', icon='smart_toy')
        tab_system = ui.tab('系统设置', icon='settings')

    with ui.tab_panels(tabs, value=tab_platform).classes('w-full'):
        with ui.tab_panel(tab_platform):
            _render_platform_login()

        with ui.tab_panel(tab_ai):
            _render_ai_config()

        with ui.tab_panel(tab_system):
            _render_system_config()