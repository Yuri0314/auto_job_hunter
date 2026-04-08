"""系统管理相关API"""

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from backend.core.database import get_db
from backend.core.config import get_settings


router = APIRouter()

# 登录任务状态
_login_tasks = {}


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


class LoginStatus(BaseModel):
    """登录状态"""
    platform: str
    status: str  # "idle", "logging_in", "success", "failed"
    message: str
    login_url: Optional[str] = None


@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    settings = get_settings()

    # 检查哪些平台有 Cookie（已登录过）
    from backend.automation.browser.cookie_manager import get_cookie_manager
    cookie_manager = get_cookie_manager()

    platforms = []
    if cookie_manager.get_cookie_info("boss"):
        platforms.append("boss")
    if cookie_manager.get_cookie_info("liepin"):
        platforms.append("liepin")
    if cookie_manager.get_cookie_info("maimai"):
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
    from backend.automation.browser.cookie_manager import get_cookie_manager

    cookie_manager = get_cookie_manager()

    platforms = []

    # BOSS直聘
    boss_info = cookie_manager.get_cookie_info("boss")
    platforms.append(PlatformStatus(
        platform="boss",
        logged_in=False,
        cookie_saved=boss_info is not None,
    ))

    # 猎聘
    liepin_info = cookie_manager.get_cookie_info("liepin")
    platforms.append(PlatformStatus(
        platform="liepin",
        logged_in=False,
        cookie_saved=liepin_info is not None,
    ))

    # 脉脉
    maimai_info = cookie_manager.get_cookie_info("maimai")
    platforms.append(PlatformStatus(
        platform="maimai",
        logged_in=False,
        cookie_saved=maimai_info is not None,
    ))

    return platforms


@router.get("/login-status/{platform}", response_model=LoginStatus)
async def get_login_status(platform: str):
    """获取登录任务状态"""
    task_info = _login_tasks.get(platform, {
        "status": "idle",
        "message": "未开始登录",
    })

    return LoginStatus(
        platform=platform,
        status=task_info["status"],
        message=task_info["message"],
        login_url=task_info.get("login_url"),
    )


async def _do_login(platform: str):
    """执行登录任务（后台运行）"""
    from backend.adapters import Platform, get_adapter

    _login_tasks[platform] = {
        "status": "logging_in",
        "message": "正在启动浏览器...",
    }

    try:
        platform_enum = Platform(platform)
        adapter = get_adapter(platform_enum)

        _login_tasks[platform] = {
            "status": "logging_in",
            "message": "请在打开的浏览器中完成登录（输入手机号+验证码）",
            "login_url": adapter.base_url,
        }

        # 调用适配器登录（用户在浏览器中手动输入手机号和验证码）
        success = await adapter.login("", "")

        if success:
            _login_tasks[platform] = {
                "status": "success",
                "message": "登录成功！Cookie已保存",
            }
        else:
            _login_tasks[platform] = {
                "status": "failed",
                "message": "登录失败或超时",
            }

    except Exception as e:
        logger.error(f"Login task error: {e}")
        _login_tasks[platform] = {
            "status": "failed",
            "message": f"登录出错: {str(e)}",
        }


@router.post("/login/{platform}")
async def login_platform(
    platform: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """登录指定平台（异步）

    流程：
    1. 启动后台登录任务
    2. 打开浏览器窗口
    3. 用户手动输入手机号+验证码登录
    4. 登录成功后自动保存Cookie
    """
    from backend.adapters import Platform, get_adapter

    # 检查平台是否有效
    try:
        platform_enum = Platform(platform)
    except ValueError:
        return {"error": f"未知平台: {platform}"}

    # 检查是否已有登录任务在运行
    task_info = _login_tasks.get(platform, {})
    if task_info.get("status") == "logging_in":
        return {
            "status": "already_running",
            "message": "登录任务正在进行中，请在浏览器中完成登录",
        }

    # 启动后台登录任务
    background_tasks.add_task(_do_login, platform)

    adapter = get_adapter(platform_enum)

    return {
        "status": "started",
        "message": "登录任务已启动，请在打开的浏览器中完成登录",
        "login_url": adapter.base_url,
        "platform": platform,
    }


@router.post("/logout/{platform}")
async def logout_platform(platform: str):
    """退出登录（清除Cookie）"""
    from backend.automation.browser.cookie_manager import get_cookie_manager

    try:
        cookie_manager = get_cookie_manager()
        cookie_manager.delete_cookies(platform)

        # 清除登录状态
        if platform in _login_tasks:
            del _login_tasks[platform]

        return {"message": f"{platform} Cookie已清除"}

    except Exception as e:
        return {"error": str(e)}


@router.get("/logs")
async def get_logs(
    limit: int = 100,
    level: str = None,
):
    """获取系统日志"""
    import os
    import glob
    from datetime import datetime

    log_dir = "./logs"
    log_files = sorted(glob.glob(os.path.join(log_dir, "*.log")), reverse=True)

    logs = []
    total = 0

    for log_file in log_files:
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                total += len(lines)

                for line in reversed(lines):
                    if len(logs) >= limit:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    # 按级别过滤
                    if level:
                        if level.upper() not in line.upper():
                            continue

                    # 解析日志行
                    log_entry = {
                        "raw": line,
                        "source": os.path.basename(log_file),
                    }

                    # 尝试提取时间戳和级别
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 4:
                            log_entry["timestamp"] = parts[0].strip()
                            log_entry["level"] = parts[1].strip()
                            log_entry["module"] = parts[2].strip()
                            log_entry["message"] = "|".join(parts[3:]).strip()

                    logs.append(log_entry)

                if len(logs) >= limit:
                    break

        except Exception as e:
            continue

    return {
        "logs": list(reversed(logs)),
        "total": total,
        "limit": limit,
    }


@router.post("/shutdown")
async def shutdown_system():
    """关闭系统"""
    import sys
    from backend.automation.browser import get_browser_manager
    from loguru import logger

    try:
        logger.info("正在关闭系统...")

        # 关闭浏览器
        try:
            browser = get_browser_manager()
            await browser.close()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")

        # 清理资源
        from backend.services import _orchestrator
        if _orchestrator:
            _orchestrator.stop()
            logger.info("协调器已停止")

        logger.info("系统关闭完成")

        # 退出应用
        sys.exit(0)

    except Exception as e:
        return {"error": str(e)}