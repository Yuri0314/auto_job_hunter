"""Playwright浏览器管理器"""

import asyncio
from typing import Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from backend.core.config import get_settings


class PlaywrightManager:
    """Playwright浏览器管理器，支持反检测和Cookie持久化"""

    def __init__(
        self,
        headless: bool = True,
        user_data_dir: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir or "./browser_data"
        self.proxy = proxy
        self.settings = get_settings()

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def start(self) -> None:
        """启动浏览器"""
        if self._browser:
            return

        logger.info("Starting Playwright browser...")

        # 创建用户数据目录
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()

        # 启动浏览器
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]

        if self.proxy:
            launch_args.append(f"--proxy-server={self.proxy}")

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )

        # 创建上下文
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
        }

        self._context = await self._browser.new_context(**context_options)

        # 应用反检测脚本
        await self._apply_stealth()

        logger.info("Browser started successfully")

    async def _apply_stealth(self) -> None:
        """应用反检测脚本"""
        if not self._context:
            return

        # 注入反检测脚本
        await self._context.add_init_script("""
            // 隐藏webdriver属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 修改plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // 修改languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });

            // 隐藏自动化标志
            window.chrome = {
                runtime: {}
            };

            // 覆盖permissions查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    async def new_page(self) -> Page:
        """创建新页面"""
        if not self._context:
            await self.start()

        self._page = await self._context.new_page()

        # 设置默认超时
        self._page.set_default_timeout(30000)

        return self._page

    async def get_page(self) -> Page:
        """获取当前页面或创建新页面"""
        if self._page and not self._page.is_closed():
            return self._page
        return await self.new_page()

    async def close_page(self) -> None:
        """关闭当前页面"""
        if self._page and not self._page.is_closed():
            await self._page.close()
            self._page = None

    async def close(self) -> None:
        """关闭浏览器"""
        if self._page:
            await self.close_page()

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Browser closed")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 全局浏览器管理器实例
_browser_manager: Optional[PlaywrightManager] = None


def get_browser_manager() -> PlaywrightManager:
    """获取浏览器管理器单例"""
    global _browser_manager
    if _browser_manager is None:
        settings = get_settings()
        _browser_manager = PlaywrightManager(
            headless=not settings.debug,
        )
    return _browser_manager