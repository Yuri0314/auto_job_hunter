"""API路由模块"""

from fastapi import APIRouter

from .jobs import router as jobs_router
from .applications import router as applications_router
from .messages import router as messages_router
from .user import router as user_router
from .config import router as config_router
from .system import router as system_router
from .settings import router as settings_router
from .resume import router as resume_router
from .search import router as search_router

api_router = APIRouter()

api_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(applications_router, prefix="/applications", tags=["Applications"])
api_router.include_router(messages_router, prefix="/messages", tags=["Messages"])
api_router.include_router(user_router, prefix="/user", tags=["User"])
api_router.include_router(config_router, prefix="/config", tags=["Config"])
api_router.include_router(system_router, prefix="/system", tags=["System"])
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
api_router.include_router(resume_router, prefix="/resume", tags=["Resume"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])