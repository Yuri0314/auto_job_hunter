#!/usr/bin/env python
"""
Auto Job Hunter - 自动求职投递系统

命令行入口
"""

import asyncio
import argparse
import sys
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


def run_server(port: int = 8000, reload: bool = False, no_browser: bool = False):
    """启动服务

    Args:
        port: 服务端口
        reload: 开发模式（热重载），注意：此模式下浏览器自动化功能不可用
        no_browser: 不自动打开浏览器
    """
    import urllib.request
    import uvicorn

    # reload 模式需要切换到 SelectorEventLoopPolicy（Windows限制）
    # 但这会导致 Playwright 无法创建子进程，浏览器自动化功能不可用
    if reload and sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("\n[开发模式] 热重载已启用，但浏览器自动化功能（登录、搜索、投递）不可用")
        print("  如需使用浏览器功能，请不加 --reload 参数启动\n")

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
        print("  或使用不同端口: python run.py --port 8080")
        print(f"\n请在浏览器访问: http://localhost:{port}/ui/dashboard")
        return

    try:
        print(f"\n启动服务 (端口 {port})...")
        if reload:
            print("  模式: 开发模式 (热重载)")

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
        reload_dirs = ["backend", "frontend_nicegui"] if reload else None
        uvicorn.run(
            "backend.main:app",
            host="127.0.0.1",
            port=port,
            reload=reload,
            reload_dirs=reload_dirs,
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
        description="Auto Job Hunter - 自动求职投递系统",
        # 无子命令时显示帮助而不是报错
    )

    # 直接参数（默认启动服务）
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务端口 (默认: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="开发模式（热重载），注意：此模式下浏览器自动化功能不可用"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开浏览器"
    )

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="其他命令")

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

    # init 子命令
    init_parser = subparsers.add_parser("init", help="初始化系统")

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

    elif args.command == "init":
        print("初始化数据库...")
        init_db()
        print("初始化完成!")
        print("\n请配置 .env 文件或设置环境变量:")
        print("  - BOSS_PHONE: BOSS直聘手机号")
        print("  - LIEPIN_PHONE: 猎聘手机号")
        print("  - MAIMAI_PHONE: 脉脉手机号")
        print("  - OPENAI_API_KEY: OpenAI API密钥(可选)")
        print("\n启动服务: python run.py")
        print("开发模式: python run.py --reload")

    else:
        # 默认启动服务
        run_server(
            port=args.port,
            reload=args.reload,
            no_browser=args.no_browser,
        )


if __name__ == "__main__":
    main()