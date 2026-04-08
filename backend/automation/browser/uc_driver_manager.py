"""Undetected ChromeDriver 浏览器管理器

使用 undetected_chromedriver 绕过 BOSS 直聘等网站的反爬检测。
uc 会修改 Chrome 的内存特征，比 playwright_stealth 更彻底。
"""

import sys
import asyncio
from typing import Optional
from pathlib import Path
from loguru import logger

from backend.core.config import get_settings


class UCDriverManager:
    """Undetected ChromeDriver 管理器

    使用 undetected_chromedriver 启动浏览器，专门用于访问
    反爬严格的网站（如 BOSS 直聘）。
    """

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        self.headless = headless
        self.user_data_dir = user_data_dir or "./browser_data_uc"
        self.proxy = proxy
        self.settings = get_settings()

        self._driver = None
        self._loop = None

    @staticmethod
    def _get_chrome_major_version() -> int:
        """获取当前 Chrome 浏览器的主版本号"""
        import subprocess
        import re

        try:
            if sys.platform == "win32":
                # Windows: 通过注册表或命令行获取版本
                import winreg
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Google\Chrome\BLBeacon"
                    )
                    version, _ = winreg.QueryValueEx(key, "version")
                    winreg.CloseKey(key)
                    return int(version.split(".")[0])
                except Exception:
                    pass

                # 回退：通过命令行获取
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                result = subprocess.run(
                    [chrome_path, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                match = re.search(r"(\d+)\.", result.stdout)
                if match:
                    return int(match.group(1))
            else:
                # macOS / Linux
                result = subprocess.run(
                    ["google-chrome", "--version"],
                    capture_output=True, text=True, timeout=5
                )
                match = re.search(r"(\d+)\.", result.stdout)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        return 0

    def _get_driver(self):
        """获取 Selenium WebDriver 实例（同步）"""
        if self._driver is not None:
            try:
                # 检查 driver 是否仍然有效
                self._driver.current_url
                return self._driver
            except Exception:
                pass

        logger.info("Starting undetected-chromedriver browser...")

        import undetected_chromedriver as uc
        from selenium.webdriver.chrome.options import Options

        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

        options = Options()
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # 禁用自动化扩展
        options.add_argument("--disable-extensions")
        # 禁用日志
        options.add_argument("--log-level=3")
        # 禁用默认应用
        options.add_argument("--disable-default-apps")

        if self.headless:
            options.add_argument("--headless")

        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")

        # 检测 Chrome 版本并指定给 uc，避免版本不匹配
        chrome_version = self._get_chrome_major_version()
        logger.info(f"Detected Chrome version: {chrome_version}")

        self._driver = uc.Chrome(
            options=options,
            auto=False,  # 禁用自动下载，使用检测到的版本
            version_main=chrome_version if chrome_version > 0 else None,
        )
        logger.info("undetected-chromedriver started successfully")

        # 注入反检测脚本
        self._inject_stealth_scripts()

        return self._driver

    def _inject_stealth_scripts(self):
        """注入反检测 JavaScript 脚本"""
        stealth_scripts = [
            # 隐藏 webdriver 特征
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            # 伪装 plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            """,
            # 伪装 languages
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            """,
            # 伪装 chrome 对象
            """
            window.chrome = {
                app: {
                    isInstalled: false,
                    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                    RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
                },
                runtime: {
                    OnInstalledReason: { CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update', INSTALL: 'install' },
                    OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                    PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' }
                }
            };
            """,
            # 隐藏 permission 特征
            """
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            """,
        ]

        for script in stealth_scripts:
            try:
                self._driver.execute_script(script)
            except Exception:
                pass

    async def start(self) -> None:
        """启动浏览器（异步包装）"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._get_driver)

    async def get(self, url: str) -> None:
        """导航到 URL"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: self._driver.get(url))

    async def find_element(self, by: str, value: str):
        """查找元素"""
        from selenium.webdriver.common.by import By
        loop = asyncio.get_running_loop()
        by_map = {
            "xpath": By.XPATH,
            "css selector": By.CSS_SELECTOR,
            "id": By.ID,
            "name": By.NAME,
            "class name": By.CLASS_NAME,
        }
        element = await loop.run_in_executor(
            None,
            lambda: self._driver.find_element(by_map.get(by, By.XPATH), value)
        )
        return element

    async def find_elements(self, by: str, value: str):
        """查找所有匹配元素"""
        from selenium.webdriver.common.by import By
        loop = asyncio.get_running_loop()
        by_map = {
            "xpath": By.XPATH,
            "css selector": By.CSS_SELECTOR,
            "id": By.ID,
            "name": By.NAME,
            "class name": By.CLASS_NAME,
        }
        elements = await loop.run_in_executor(
            None,
            lambda: self._driver.find_elements(by_map.get(by, By.XPATH), value)
        )
        return elements

    async def click(self, xpath: str) -> bool:
        """点击元素"""
        try:
            element = await self.find_element("xpath", xpath)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: element.click())
            return True
        except Exception as e:
            logger.debug(f"Click failed: {e}")
            return False

    async def get_text(self, xpath: str) -> Optional[str]:
        """获取元素文本"""
        try:
            element = await self.find_element("xpath", xpath)
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, lambda: element.text)
            return text
        except Exception:
            return None

    async def get_attribute(self, xpath: str, attr: str) -> Optional[str]:
        """获取元素属性"""
        try:
            element = await self.find_element("xpath", xpath)
            loop = asyncio.get_running_loop()
            value = await loop.run_in_executor(None, lambda: element.get_attribute(attr))
            return value
        except Exception:
            return None

    async def send_keys(self, xpath: str, text: str) -> None:
        """输入文本"""
        from selenium.webdriver.common.keys import Keys
        element = await self.find_element("xpath", xpath)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: (element.clear(), element.send_keys(text)))

    async def execute_script(self, script: str):
        """执行 JS"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: self._driver.execute_script(script))

    async def get_cookies(self) -> list:
        """获取 cookies"""
        loop = asyncio.get_running_loop()
        cookies = await loop.run_in_executor(None, lambda: self._driver.get_cookies())
        return cookies

    async def add_cookies(self, cookies: list) -> None:
        """添加 cookies"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: [self._driver.add_cookie(c) for c in cookies])

    async def close(self) -> None:
        """关闭浏览器"""
        if self._driver:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._driver.quit)
            except Exception:
                pass
            self._driver = None
            logger.info("undetected-chromedriver closed")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 全局单例
_uc_driver_manager: Optional[UCDriverManager] = None


def get_uc_driver_manager() -> UCDriverManager:
    """获取 UC Driver 管理器单例"""
    global _uc_driver_manager
    if _uc_driver_manager is None:
        _uc_driver_manager = UCDriverManager(
            headless=False,
            user_data_dir=str(Path.cwd() / "browser_data_uc"),
        )
    return _uc_driver_manager


async def close_and_reset_uc_driver_manager():
    """关闭并重置 UC Driver 管理器"""
    global _uc_driver_manager
    if _uc_driver_manager is not None:
        try:
            await _uc_driver_manager.close()
        except Exception:
            pass
    _uc_driver_manager = None
