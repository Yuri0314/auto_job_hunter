"""API模块"""

from .routes import api_router
from .jobs import router as jobs_router
from .applications import router as applications_router
from .messages import router as messages_router
from .user import router as user_router
from .config import router as config_router
from .system import router as system_router

__all__ = [
    "api_router",
    "jobs_router",
    "applications_router",
    "messages_router",
    "user_router",
    "config_router",
    "system_router",
]