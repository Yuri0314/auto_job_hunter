#!/usr/bin/env python
"""
Auto Job Hunter - 自动求职投递系统

命令行入口
"""

import asyncio
import argparse
import subprocess
import sys
import time
import webbrowser
import os
from loguru import logger

# Windows asyncio 兼容性修复 - Playwright 需要 ProactorEventLoop 支持子进程
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from backend.core.config import get_settings
from backend.core.database import init_db
from backend.services import Orchestrator, get_orchestrator
from backend.adapters import Platform


def setup_logging():
    """配置日志"""
    settings = get_settings()
    logger.add(
        "logs/auto_job_hunter_{time}.log",
        rotation="1 day",
        retention="7 days",
        level=settings.log_level,
    )


async def run_search(
    keywords: str,
    platforms: list,
    city: str = None,
    apply: bool = False,
    use_ai: bool = False,
):
    """运行职位搜索"""
    orchestrator = await get_orchestrator(use_ai=use_ai)

    platform_enums = [Platform(p) for p in platforms]

    result = await orchestrator.run_job_search_cycle(
        platforms=platform_enums,
        keywords=keywords,
        city=city,
        apply_filtered=apply,
    )

    logger.info(f"Search completed: {result}")
    print(f"\n搜索结果:")
    print(f"  发现职位: {result['total_jobs']}")
    print(f"  过滤后: {result['filtered_jobs']}")
    print(f"  已投递: {result['applied_jobs']}")
    print(f"  成功数: {result['success_count']}")


async def run_daemon(interval: int = 60, use_ai: bool = False):
    """以守护进程模式运行"""
    orchestrator = await get_orchestrator(use_ai=use_ai)

    logger.info(f"Starting daemon mode, interval: {interval} minutes")

    await orchestrator.start_scheduled(interval_minutes=interval)


async def run_web(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """启动Web服务（FastAPI + NiceGUI）"""
    import uvicorn

    logger.info(f"Starting web server at {host}:{port}")
    logger.info(f"NiceGUI UI: http://localhost:{port}/ui")

    # Windows 兼容性：使用 WindowsSelectorEventLoopPolicy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 添加frontend_nicegui到reload监控目录
    reload_dirs = ["backend", "frontend_nicegui"] if reload else None

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=reload_dirs,
    )


def run_gui(port: int = 8000, no_browser: bool = False):
    """一键启动GUI界面（FastAPI + NiceGUI 单服务）"""
    import urllib.request

    # Windows asyncio 兼容性
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 50)
    print("Auto Job Hunter - 启动中...")
    print("=" * 50)

    # 检查端口是否已被占用
    def check_port_in_use(port):
        try:
            urllib.request.urlopen(f"http://localhost:{port}/docs", timeout=1)
            return True
        except:
            return False

    # 检查并提示
    if check_port_in_use(port):
        print(f"\n[警告] 端口 {port} 已被占用，服务可能已在运行")
        print("  如需重启，请先关闭旧进程: taskkill /F /IM python.exe")
        print("  或使用不同端口: python run.py gui --port 8080")
        print(f"\n请在浏览器访问: http://localhost:{port}/ui/dashboard")
        return

    try:
        print(f"\n启动服务 (端口 {port})...")

        # 打开浏览器
        ui_url = f"http://localhost:{port}/ui/dashboard"
        if not no_browser:
            print(f"正在打开浏览器: {ui_url}")
            webbrowser.open(ui_url)

        print("\n" + "=" * 50)
        print("服务已启动!")
        print(f"  NiceGUI界面: http://localhost:{port}/ui/dashboard")
        print(f"  API文档:     http://localhost:{port}/docs")
        print("=" * 50)
        print("\n按 Ctrl+C 停止服务...")

        # 启动uvicorn服务
        import uvicorn
        uvicorn.run(
            "backend.main:app",
            host="127.0.0.1",
            port=port,
        )

    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n启动错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Auto Job Hunter - 自动求职投递系统"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # search 子命令
    search_parser = subparsers.add_parser("search", help="搜索职位")
    search_parser.add_argument(
        "-k", "--keywords",
        required=True,
        help="搜索关键词"
    )
    search_parser.add_argument(
        "-p", "--platforms",
        nargs="+",
        default=["boss", "liepin"],
        choices=["boss", "liepin", "maimai"],
        help="平台选择"
    )
    search_parser.add_argument(
        "-c", "--city",
        help="城市"
    )
    search_parser.add_argument(
        "-a", "--apply",
        action="store_true",
        help="自动投递过滤后的职位"
    )
    search_parser.add_argument(
        "--ai",
        action="store_true",
        help="使用AI模式"
    )

    # daemon 子命令
    daemon_parser = subparsers.add_parser("daemon", help="守护进程模式")
    daemon_parser.add_argument(
        "-i", "--interval",
        type=int,
        default=60,
        help="搜索间隔(分钟)"
    )
    daemon_parser.add_argument(
        "--ai",
        action="store_true",
        help="使用AI模式"
    )

    # web 子命令
    web_parser = subparsers.add_parser("web", help="启动Web服务")
    web_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="监听地址"
    )
    web_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="端口"
    )

    # init 子命令
    init_parser = subparsers.add_parser("init", help="初始化系统")

    # gui 子命令
    gui_parser = subparsers.add_parser("gui", help="一键启动GUI界面")
    gui_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务端口"
    )
    gui_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开浏览器"
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging()

    # 初始化数据库
    init_db()

    if args.command == "search":
        asyncio.run(run_search(
            keywords=args.keywords,
            platforms=args.platforms,
            city=args.city,
            apply=args.apply,
            use_ai=args.ai,
        ))

    elif args.command == "daemon":
        asyncio.run(run_daemon(
            interval=args.interval,
            use_ai=args.ai,
        ))

    elif args.command == "web":
        asyncio.run(run_web(
            host=args.host,
            port=args.port,
        ))

    elif args.command == "init":
        print("初始化数据库...")
        init_db()
        print("初始化完成!")
        print("\n请配置 .env 文件或设置环境变量:")
        print("  - BOSS_PHONE: BOSS直聘手机号")
        print("  - LIEPIN_PHONE: 猎聘手机号")
        print("  - MAIMAI_PHONE: 脉脉手机号")
        print("  - OPENAI_API_KEY: OpenAI API密钥(可选)")
        print("\n启动Web服务: python -m backend.cli web")
        print("启动GUI界面: python -m backend.cli gui")

    elif args.command == "gui":
        run_gui(
            port=args.port,
            no_browser=args.no_browser,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()