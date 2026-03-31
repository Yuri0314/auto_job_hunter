"""FastAPI主应用"""

import sys

# Windows asyncio 兼容性修复 - Playwright 需要子进程支持
# 必须使用 ProactorEventLoopPolicy 而不是 SelectorEventLoopPolicy
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.core.config import get_settings, reload_settings
from backend.core.database import init_db, SessionLocal
from backend.api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Auto Job Hunter...")

    # 初始化数据库
    init_db()
    logger.info("Database initialized")

    # 加载配置（包含数据库覆盖）
    db = SessionLocal()
    try:
        reload_settings(db)
        logger.info("Configuration loaded (with database overrides)")
    finally:
        db.close()

    yield

    # 关闭时
    logger.info("Shutting down Auto Job Hunter...")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="自动求职投递系统 - 支持多平台智能求职",
        lifespan=lifespan,
    )

    # CORS配置 - 从配置文件读取允许的域名
    allowed_origins = settings.allowed_origins.split(",") if settings.allowed_origins else []
    # 开发模式下允许所有来源，生产模式使用配置的域名
    if settings.debug and not allowed_origins:
        allowed_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS allowed origins: {allowed_origins}")

    # 注册路由
    app.include_router(api_router, prefix="/api")

    # 挂载 NiceGUI 前端
    try:
        from frontend_nicegui.app import setup_nicegui
        setup_nicegui(app)
        logger.info("NiceGUI frontend mounted at /ui")
    except ImportError as e:
        logger.warning(f"NiceGUI not available: {e}")

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )