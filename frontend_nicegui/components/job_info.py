# frontend_nicegui/components/job_info.py
"""职位信息相关共用组件"""

from nicegui import ui

from ..config import API_BASE


def render_status_badge(status: str) -> ui.label:
    """渲染状态标签"""
    status_map = {
        "success": ("成功", "bg-[#22c55e]/20 text-[#22c55e]"),
        "failed": ("失败", "bg-[#ef4444]/20 text-[#ef4444]"),
        "pending": ("处理中", "bg-[#f59e0b]/20 text-[#f59e0b]"),
    }
    text, color_class = status_map.get(status, (status, "bg-[#6b7280]/20 text-[#9ca3af]"))
    return ui.label(text).classes(f'{color_class} px-2 py-0.5 rounded text-xs font-mono')


def render_application_row(app: dict, on_retry=None):
    """渲染单条投递记录"""
    with ui.row().classes('w-full items-center py-3 px-4 border-b border-[#1f2937] hover:bg-[#ffffff]/5'):
        with ui.column().classes('flex-1'):
            ui.label(f"投递于 {app.get('submitted_at', 'N/A')[:10] if app.get('submitted_at') else 'N/A'}").classes(
                'text-[#9ca3af] text-xs'
            )

        with ui.column().classes('w-32'):
            platform = app.get('platform', 'unknown').upper()
            ui.label(platform).classes('text-[#00d4ff] text-xs font-mono')

        with ui.column().classes('w-24'):
            render_status_badge(app.get('status', 'pending'))

        with ui.column().classes('w-20'):
            if app.get('status') == 'failed' and on_retry:
                ui.button(
                    "重试",
                    icon="refresh",
                    on_click=lambda: on_retry(app),
                ).classes('action-btn text-xs')


def render_message_card(msg: dict, on_mark_read=None, on_reply=None, on_auto_reply=None):
    """渲染消息卡片"""
    is_unread = not msg.get('is_read', True)
    border_color = "#00d4ff" if is_unread else "#1f2937"

    with ui.card().classes('w-full p-4 mb-2').style(f'border-left: 3px solid {border_color}'):
        with ui.row().classes('w-full justify-between items-start'):
            with ui.column():
                sender = msg.get('sender_name', '未知')
                company = msg.get('company', '')
                ui.label(f"{sender} {f'@ {company}' if company else ''}").classes(
                    f'text-white font-semibold {"text-[#00d4ff]" if is_unread else ""}'
                )
                job_title = msg.get('job_title', '')
                if job_title:
                    ui.label(job_title).classes('text-[#9ca3af] text-sm')

            received_at = msg.get('received_at', '')
            if received_at:
                ui.label(received_at[:16]).classes('text-[#6b7280] text-xs')

        content = msg.get('content', '')
        ui.label(content[:120] + ("..." if len(content) > 120 else "")).classes(
            'text-[#c4c4c8] text-sm mt-2'
        )

        # 操作按钮
        with ui.row().classes('gap-2 mt-3'):
            if is_unread and on_mark_read:
                ui.button("标记已读", icon="done", on_click=lambda: on_mark_read(msg)).classes('action-btn text-xs')

            if on_reply:
                ui.button("回复", icon="reply", on_click=lambda: on_reply(msg)).classes('action-btn text-xs')

            if on_auto_reply and msg.get('suggested_reply'):
                ui.button("AI回复", icon="smart_button", on_click=lambda: on_auto_reply(msg)).classes(
                    'primary-btn text-xs'
                )


async def fetch_job_title(job_id: int) -> str:
    """根据 job_id 获取职位名称"""
    try:
        import httpx
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/jobs/{job_id}", timeout=10)
            if r.is_success:
                data = r.json()
                return data.get('title', f'Job #{job_id}')
    except Exception:
        pass
    return f'Job #{job_id}'
