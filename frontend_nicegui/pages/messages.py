# frontend_nicegui/pages/messages.py
"""消息中心页面"""

import asyncio
import httpx
from nicegui import ui

from ..config import API_BASE
from ..components.job_info import render_message_card


async def fetch_messages(unread_only: bool = False, platform: str = None, page: int = 1, page_size: int = 20):
    """获取消息列表"""
    try:
        params = {"unread_only": unread_only, "page": page, "page_size": page_size}
        if platform:
            params["platform"] = platform

        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.get(f"{API_BASE}/messages", params=params, timeout=30)
            if r.is_success:
                return r.json()
            return {"total": 0, "unread": 0, "items": []}
    except Exception:
        return {"total": 0, "unread": 0, "items": []}


async def mark_as_read(message_id: int):
    """标记消息为已读"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(f"{API_BASE}/messages/{message_id}/read", timeout=30)
            if r.is_success:
                ui.notify("已标记为已读", type='info')
                return True
    except Exception:
        pass
    return False


async def reply_message(message_id: int, content: str):
    """回复消息"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(
                f"{API_BASE}/messages/{message_id}/reply",
                json={"content": content},
                timeout=60
            )
            if r.is_success:
                result = r.json()
                if result.get("success"):
                    ui.notify("回复成功！", type='positive')
                else:
                    ui.notify(f"回复失败: {result.get('message')}", type='warning')
            else:
                ui.notify(f"回复失败: {r.text}", type='negative')
    except Exception as e:
        ui.notify(f"回复异常: {e}", type='negative')


async def auto_reply_message(message_id: int):
    """AI自动回复"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(f"{API_BASE}/messages/{message_id}/auto-reply", timeout=60)
            if r.is_success:
                result = r.json()
                if result.get("success"):
                    ui.notify("AI回复成功！", type='positive')
                else:
                    ui.notify(f"AI回复失败: {result.get('message')}", type='warning')
            else:
                ui.notify(f"AI回复失败: {r.text}", type='negative')
    except Exception as e:
        ui.notify(f"AI回复异常: {e}", type='negative')


async def check_new_messages():
    """检查新消息"""
    try:
        async with httpx.AsyncClient(http2=False, trust_env=False) as client:
            r = await client.post(f"{API_BASE}/messages/check-new", timeout=60)
            if r.is_success:
                result = r.json()
                new_count = result.get("new_count", 0)
                if new_count > 0:
                    ui.notify(f"发现 {new_count} 条新消息", type='positive')
                else:
                    ui.notify("没有新消息", type='info')
                return True
    except Exception:
        pass
    return False


def render_messages_page():
    """渲染消息中心页面"""
    from ..layout import render_page_header

    render_page_header("MESSAGES", "HR消息 · 自动回复")

    def _handle_check_new():
        """检查新消息"""
        asyncio.create_task(_do_check_new())

    async def _do_check_new():
        await check_new_messages()
        await load_messages()

    # 顶部操作栏
    with ui.card().classes('w-full p-4 mb-4'):
        with ui.row().classes('w-full gap-4 items-end'):
            ui.button("📋 投递记录", icon="list_alt",
                      on_click=lambda: ui.navigate.to('/applications')).classes('action-btn')

            platform_select = ui.select(
                ['all', 'boss', 'liepin'],
                label="平台",
                value='all'
            ).classes('w-40')

            unread_only_check = ui.checkbox("仅显示未读").classes('mt-4')

            ui.button("刷新", icon="refresh", on_click=lambda: load_messages()).classes('action-btn')

            ui.button("检查新消息", icon="mail", on_click=_handle_check_new).classes('primary-btn')

    # 消息列表
    list_container = ui.column().classes('w-full')

    # 分页信息
    pagination_label = ui.label().classes('text-[#6b7280] text-sm mt-4')

    async def load_messages(page: int = 1):
        """加载消息列表"""
        list_container.clear()

        with list_container:
            ui.spinner(size='md')
            ui.label("加载中...").classes('text-[#9ca3af]')

        platform = platform_select.value if platform_select.value != 'all' else None
        unread_only = unread_only_check.value

        data = await fetch_messages(unread_only=unread_only, platform=platform, page=page, page_size=20)

        list_container.clear()
        items = data.get('items', [])
        total_count = data.get('total', 0)
        unread_count = data.get('unread', 0)

        with list_container:
            # 未读统计
            if unread_count > 0:
                ui.label(f"📬 {unread_count} 条未读消息").classes('text-[#00d4ff] mb-4')

            if not items:
                ui.label("暂无消息").classes('text-[#9ca3af] text-center py-8')
            else:
                for msg in items:
                    render_message_card(
                        msg,
                        on_mark_read=_handle_mark_read,
                        on_reply=_handle_reply,
                        on_auto_reply=_handle_auto_reply,
                    )

        # 分页
        pagination_label.text = f"第 {page} 页，共 {total_count} 条消息"

        with list_container:
            with ui.row().classes('w-full justify-center gap-4 mt-4'):
                if page > 1:
                    ui.button("上一页", icon="chevron_left",
                              on_click=lambda: load_messages(page - 1)).classes('action-btn')

                if page * 20 < total_count:
                    ui.button("下一页", icon="chevron_right",
                              on_click=lambda: load_messages(page + 1)).classes('action-btn')

    def _handle_mark_read(msg: dict):
        """处理标记已读"""
        asyncio.create_task(_do_mark_read(msg))

    async def _do_mark_read(msg: dict):
        success = await mark_as_read(msg['id'])
        if success:
            msg['is_read'] = True
            await load_messages()

    def _handle_reply(msg: dict):
        """处理回复按钮"""
        _show_reply_dialog(msg)

    def _show_reply_dialog(msg: dict):
        """显示回复弹窗"""
        with ui.dialog() as dialog, ui.card().classes('w-[500px] p-4'):
            ui.label(f"回复: {msg.get('sender_name', 'HR')}").classes('text-lg font-bold mb-4')

            # 原消息预览
            content = msg.get('content', '')
            ui.label("原消息:").classes('text-[#6b7280] text-sm')
            ui.label(content[:200] + ("..." if len(content) > 200 else "")).classes(
                'text-[#9ca3af] text-sm mb-4 bg-[#ffffff]/5 p-3 rounded'
            )

            reply_input = ui.textarea(
                label="回复内容",
                placeholder="请输入回复内容...",
            ).classes('w-full')

            # 如果有建议回复，显示快捷选项
            suggested = msg.get('suggested_reply')
            if suggested:
                ui.label("AI建议回复:").classes('text-[#00d4ff] text-sm mt-2')
                with ui.row().classes('w-full'):
                    ui.button(
                        "使用建议回复",
                        icon="auto_awesome",
                        on_click=lambda: reply_input.set_value(suggested),
                    ).classes('action-btn text-xs')

            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button("取消", on_click=dialog.close).classes('action-btn')
                ui.button("发送", icon="send", on_click=lambda: _do_reply(dialog, msg, reply_input.value)).classes(
                    'primary-btn'
                )

        dialog.open()

    async def _do_reply(dialog, msg: dict, content: str):
        """执行回复"""
        if not content:
            ui.notify("请输入回复内容", type='warning')
            return

        dialog.close()
        await reply_message(msg['id'], content)
        await load_messages()

    def _handle_auto_reply(msg: dict):
        """处理AI自动回复"""
        asyncio.create_task(_do_auto_reply(msg))

    async def _do_auto_reply(msg: dict):
        await auto_reply_message(msg['id'])
        await load_messages()

    # 初始加载
    ui.timer(0.1, lambda: asyncio.create_task(load_messages()), once=True)
