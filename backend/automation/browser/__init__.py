"""浏览器自动化模块"""

from .playwright_manager import PlaywrightManager, get_browser_manager
from .cookie_manager import CookieManager, get_cookie_manager
from .stealth import apply_stealth

__all__ = [
    "PlaywrightManager",
    "get_browser_manager",
    "CookieManager",
    "get_cookie_manager",
    "apply_stealth",
]