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
        # 如果浏览器已关闭，重新创建
        if self._browser is not None:
            try:
                # 检查浏览器是否仍然有效
                if self._browser.is_connected():
                    return
            except Exception:
                pass
            # 浏览器已断开连接，重置状态
            logger.info("Browser was closed, restarting...")
            self._browser = None
            self._context = None
            self._page = None
            self._playwright = None

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

        # 使用 launch_persistent_context 启动持久化浏览器
        # 这样浏览器会复用用户数据目录，Cookie 和会话都会保留
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
        }

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            args=launch_args,
            **context_options,
        )

        # 获取浏览器实例
        self._browser = self._context.browser

        # 获取或创建页面
        if self._context.pages:
            # 使用自动创建的初始页面
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        self._page.set_default_timeout(30000)

        # 在页面上注入反检测脚本（使用 page.add_init_script 确保对当前页面生效）
        await self._apply_stealth_to_page(self._page)

        logger.info("Browser started successfully")

    async def _apply_stealth(self) -> None:
        """应用反检测脚本"""
        if not self._context:
            return

        # 使用更完善的反检测脚本
        from .stealth import STEALTH_SCRIPT

        # 添加基础反检测
        await self._context.add_init_script(STEALTH_SCRIPT)

        # 添加针对 BOSS直聘等网站的额外反检测
        await self._context.add_init_script("""
            // 覆盖 window.close() - BOSS检测到自动化后会尝试关闭窗口
            window.close = function() {
                console.log('[STEALTH] window.close() blocked');
            };

            // 拦截 window.open("", "_self").close() 模式
            var origOpen = window.open;
            window.open = function(url, name, features) {
                if (name === '_self') return window;
                return { close: function() { console.log('[STEALTH] pseudo.close'); }, closed: false };
            };

            // 关键修复: BOSS直聘的前端会调用 history.back() 来阻止自动化访问
            // 在 Playwright 中，新标签页的 history 回退会到 about:blank（白屏）
            // 解决方案: 在 init_script 中立即覆盖 history 导航方法（不延迟）
            // init_script 在页面任何 JS 执行前运行，所以可以确保拦截生效
            (function() {
                var originalBack = history.back.bind(history);
                var originalForward = history.forward.bind(history);
                var originalGo = history.go.bind(history);

                Object.defineProperty(history, 'back', {
                    value: function() {
                        console.log('[STEALTH] history.back() called - replaced with noop');
                    },
                    configurable: true,
                    writable: true
                });

                Object.defineProperty(history, 'forward', {
                    value: function() {
                        console.log('[STEALTH] history.forward() called - replaced with noop');
                    },
                    configurable: true,
                    writable: true
                });

                Object.defineProperty(history, 'go', {
                    value: function(delta) {
                        console.log('[STEALTH] history.go(' + delta + ') called - ignored if negative');
                        if (delta < 0) return;
                        return originalGo(delta);
                    },
                    configurable: true,
                    writable: true
                });

                console.log('[STEALTH] History interception activated at page init');
            })();

            // 阻止 location.reload() - BOSS 检测到自动化后会不断刷新页面
            location.reload = function() {
                console.log('[STEALTH] location.reload() blocked');
                return;
            };

            // 隐藏 webdriver 特征
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });

            // 伪造 Chrome 特征
            window.chrome = window.chrome || {
                app: { isInstalled: false },
                csi: function() {},
                loadTimes: function() {}
            };

            // 伪造 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });

            // 伪造语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
                configurable: true
            });

            console.log('[Stealth] Anti-detection scripts loaded');
        """)

    async def _apply_stealth_to_page(self, page: Page) -> None:
        """对单个页面应用反检测脚本（用于持久化上下文的初始页面）"""
        # 使用 page.add_init_script 确保脚本在当前页面执行
        # 这些脚本会在页面刷新后重新执行

        # 基础反检测
        from .stealth import STEALTH_SCRIPT
        await page.add_init_script(STEALTH_SCRIPT)

        # BOSS 直聘专用反检测 - 立即执行拦截，不延迟
        await page.add_init_script("""
            // 覆盖 window.close() - BOSS检测到自动化后会尝试关闭窗口
            window.close = function() {
                console.log('[STEALTH] window.close() blocked');
            };

            // 拦截 window.open("", "_self").close() 模式
            var origOpen = window.open;
            window.open = function(url, name, features) {
                if (name === '_self') return window;
                return { close: function() { console.log('[STEALTH] pseudo.close'); }, closed: false };
            };

            // 关键修复: BOSS直聘的前端会调用 history.back() 来阻止自动化访问
            // 在 Playwright 中，新标签页的 history 回退会到 about:blank（白屏）
            // 解决方案: 在 init_script 中立即覆盖 history 导航方法（不延迟）
            // init_script 在页面任何 JS 执行前运行，所以可以确保拦截生效
            (function() {
                var originalBack = history.back.bind(history);
                var originalForward = history.forward.bind(history);
                var originalGo = history.go.bind(history);

                Object.defineProperty(history, 'back', {
                    value: function() {
                        console.log('[STEALTH] history.back() called - replaced with noop');
                    },
                    configurable: true,
                    writable: true
                });

                Object.defineProperty(history, 'forward', {
                    value: function() {
                        console.log('[STEALTH] history.forward() called - replaced with noop');
                    },
                    configurable: true,
                    writable: true
                });

                Object.defineProperty(history, 'go', {
                    value: function(delta) {
                        console.log('[STEALTH] history.go(' + delta + ') called - ignored if negative');
                        if (delta < 0) return;
                        return originalGo(delta);
                    },
                    configurable: true,
                    writable: true
                });

                console.log('[STEALTH] History interception activated at page init');
            })();

            // 阻止 location.reload() - BOSS 检测到自动化后会不断刷新页面
            location.reload = function() {
                console.log('[STEALTH] location.reload() blocked');
                return;
            };

            // 隐藏 webdriver 特征
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });

            // 伪造 Chrome 特征
            window.chrome = window.chrome || {
                app: { isInstalled: false },
                csi: function() {},
                loadTimes: function() {}
            };

            // 伪造 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });

            // 伪造语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
                configurable: true
            });

            console.log('[Stealth] Anti-detection scripts loaded');
        """)

    async def new_page(self) -> Page:
        """创建新页面"""
        if not self._context:
            await self.start()

        # 调试：检查是否有现有页面
        if self._page and not self._page.is_closed():
            logger.warning(f"Creating new page while existing page is still open: {self._page.url}")

        self._page = await self._context.new_page()

        # 设置默认超时
        self._page.set_default_timeout(30000)

        logger.info(f"Created new page, URL: {self._page.url}")

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
        # 使用绝对路径存储浏览器用户数据
        user_data_dir = str(Path.cwd() / "browser_data")
        # 始终使用有界面模式，避免被反爬检测
        _browser_manager = PlaywrightManager(
            headless=False,  # 有界面模式，更不容易被检测
            user_data_dir=user_data_dir,
        )
    return _browser_manager


async def close_and_reset_browser_manager():
    """关闭并重置浏览器管理器（用于登录时重新应用反检测脚本）"""
    global _browser_manager
    if _browser_manager is not None:
        try:
            await _browser_manager.close()
            logger.info("Browser closed for reset")
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    _browser_manager = None


def reset_browser_manager():
    """重置浏览器管理器（仅重置变量，不关闭浏览器）"""
    global _browser_manager
    _browser_manager = None