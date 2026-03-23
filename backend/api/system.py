"""系统管理相关API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.config import get_settings


router = APIRouter()


class SystemStatus(BaseModel):
    """系统状态"""
    status: str
    version: str
    database: str
    ai_configured: bool
    platforms_configured: list


class PlatformStatus(BaseModel):
    """平台状态"""
    platform: str
    logged_in: bool
    cookie_saved: bool


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    settings = get_settings()

    platforms = []
    if settings.boss_username:
        platforms.append("boss")
    if settings.liepin_username:
        platforms.append("liepin")
    if settings.maimai_username:
        platforms.append("maimai")

    return SystemStatus(
        status="running",
        version=settings.app_version,
        database="connected" if settings.database_url else "not configured",
        ai_configured=bool(settings.openai_api_key or settings.ollama_base_url),
        platforms_configured=platforms,
    )


@router.get("/platforms", response_model=list[PlatformStatus])
async def get_platform_status():
    """获取各平台状态"""
    from backend.automation.browser import get_cookie_manager

    cookie_manager = get_cookie_manager()
    settings = get_settings()

    platforms = []

    # BOSS直聘
    boss_info = cookie_manager.get_cookie_info("boss")
    platforms.append(PlatformStatus(
        platform="boss",
        logged_in=False,  # 需要实际检查
        cookie_saved=boss_info is not None,
    ))

    # 猎聘
    liepin_info = cookie_manager.get_cookie_info("liepin")
    platforms.append(PlatformStatus(
        platform="liepin",
        logged_in=False,
        cookie_saved=liepin_info is not None,
    ))

    return platforms


@router.post("/login/{platform}")
async def login_platform(
    platform: str,
    db: Session = Depends(get_db),
):
    """登录指定平台"""
    from backend.adapters import Platform, get_adapter

    try:
        platform_enum = Platform(platform)
        adapter = get_adapter(platform_enum)

        # TODO: 获取账号密码或返回登录引导
        return {
            "message": f"Please login to {platform} manually",
            "login_url": adapter.base_url,
        }

    except ValueError:
        return {"error": f"Unknown platform: {platform}"}


@router.get("/logs")
async def get_logs(
    limit: int = 100,
    level: str = None,
):
    """获取系统日志"""
    # TODO: 实现日志查询
    return {
        "logs": [],
        "total": 0,
    }


@router.post("/shutdown")
async def shutdown_system():
    """关闭系统"""
    # TODO: 实现优雅关闭
    return {"message": "Shutdown initiated"}