"""API路由模块"""

from fastapi import APIRouter

from .jobs import router as jobs_router
from .applications import router as applications_router
from .messages import router as messages_router
from .user import router as user_router
from .config import router as config_router
from .system import router as system_router

api_router = APIRouter()

api_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(applications_router, prefix="/applications", tags=["Applications"])
api_router.include_router(messages_router, prefix="/messages", tags=["Messages"])
api_router.include_router(user_router, prefix="/user", tags=["User"])
api_router.include_router(config_router, prefix="/config", tags=["Config"])
api_router.include_router(system_router, prefix="/system", tags=["System"])