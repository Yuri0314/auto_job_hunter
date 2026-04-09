"""
Pytest 全局配置

为所有测试设置正确的环境和事件循环策略
"""

import asyncio
import sys

# Windows 上 Playwright 需要 ProactorEventLoop 支持子进程
# 必须在任何异步操作之前设置
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    返回事件循环策略

    pytest-asyncio 推荐使用 event_loop_policy fixture
    而不是重新定义 event_loop fixture
    """
    if sys.platform == "win32":
        return asyncio.WindowsProactorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(autouse=True)
async def cleanup_browser_after_test():
    """每个测试后自动清理浏览器资源"""
    yield
    # 测试后清理浏览器管理器单例
    try:
        from backend.automation.browser import get_browser_manager
        browser = get_browser_manager()
        if browser._browser or browser._context or browser._page:
            await browser.close()
    except Exception:
        pass
