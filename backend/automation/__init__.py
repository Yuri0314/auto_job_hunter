"""自动化模块"""

from .browser import (
    PlaywrightManager,
    get_browser_manager,
    CookieManager,
    get_cookie_manager,
    apply_stealth,
)
from .interaction import HumanSimulator, CaptchaSolver

__all__ = [
    "PlaywrightManager",
    "get_browser_manager",
    "CookieManager",
    "get_cookie_manager",
    "apply_stealth",
    "HumanSimulator",
    "CaptchaSolver",
]