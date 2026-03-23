"""Cookie持久化管理器"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger
from playwright.async_api import BrowserContext

from backend.core.config import get_settings


class CookieManager:
    """Cookie持久化管理，支持多平台Cookie存储和加载"""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or "./cookies")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_cookie_file(self, platform: str) -> Path:
        """获取平台的Cookie文件路径"""
        return self.storage_dir / f"{platform}_cookies.json"

    async def save_cookies(
        self,
        context: BrowserContext,
        platform: str
    ) -> bool:
        """保存Cookie到文件"""
        try:
            cookies = await context.cookies()
            cookie_file = self._get_cookie_file(platform)

            data = {
                "cookies": cookies,
                "saved_at": datetime.now().isoformat(),
                "platform": platform,
            }

            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(cookies)} cookies for {platform}")
            return True

        except Exception as e:
            logger.error(f"Failed to save cookies for {platform}: {e}")
            return False

    async def load_cookies(
        self,
        context: BrowserContext,
        platform: str
    ) -> bool:
        """从文件加载Cookie"""
        try:
            cookie_file = self._get_cookie_file(platform)

            if not cookie_file.exists():
                logger.info(f"No saved cookies found for {platform}")
                return False

            with open(cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            cookies = data.get("cookies", [])

            if cookies:
                await context.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies for {platform}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to load cookies for {platform}: {e}")
            return False

    def get_cookie_info(self, platform: str) -> Optional[Dict[str, Any]]:
        """获取Cookie信息（不加载）"""
        try:
            cookie_file = self._get_cookie_file(platform)

            if not cookie_file.exists():
                return None

            with open(cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "platform": platform,
                "saved_at": data.get("saved_at"),
                "cookie_count": len(data.get("cookies", [])),
            }

        except Exception as e:
            logger.error(f"Failed to get cookie info for {platform}: {e}")
            return None

    def delete_cookies(self, platform: str) -> bool:
        """删除指定平台的Cookie"""
        try:
            cookie_file = self._get_cookie_file(platform)

            if cookie_file.exists():
                cookie_file.unlink()
                logger.info(f"Deleted cookies for {platform}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete cookies for {platform}: {e}")
            return False

    def list_saved_platforms(self) -> List[str]:
        """列出所有已保存Cookie的平台"""
        platforms = []

        for file in self.storage_dir.glob("*_cookies.json"):
            platform = file.stem.replace("_cookies", "")
            platforms.append(platform)

        return platforms

    async def check_login_status(
        self,
        context: BrowserContext,
        platform: str,
        check_url: str,
        login_indicator: str
    ) -> bool:
        """检查登录状态"""
        try:
            page = await context.new_page()

            await page.goto(check_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 检查是否存在登录指示器（如用户头像、用户名等）
            element = await page.query_selector(login_indicator)

            await page.close()

            return element is not None

        except Exception as e:
            logger.error(f"Failed to check login status for {platform}: {e}")
            return False


# 全局Cookie管理器实例
_cookie_manager: Optional[CookieManager] = None


def get_cookie_manager() -> CookieManager:
    """获取Cookie管理器单例"""
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    return _cookie_manager