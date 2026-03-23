"""平台适配器模块"""

from .base_adapter import (
    Platform,
    BasePlatformAdapter,
    SearchResult,
    ApplicationResult,
    Message,
)
from .boss_adapter import BossAdapter
from .liepin_adapter import LiepinAdapter

__all__ = [
    "Platform",
    "BasePlatformAdapter",
    "SearchResult",
    "ApplicationResult",
    "Message",
    "BossAdapter",
    "LiepinAdapter",
]


def get_adapter(platform: Platform) -> BasePlatformAdapter:
    """获取平台适配器"""
    adapters = {
        Platform.BOSS: BossAdapter,
        Platform.LIEPIN: LiepinAdapter,
    }

    adapter_class = adapters.get(platform)
    if not adapter_class:
        raise ValueError(f"Unsupported platform: {platform}")

    return adapter_class()