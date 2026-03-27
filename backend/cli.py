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
from loguru import logger

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


async def run_web(host: str = "0.0.0.0", port: int = 8000):
    """启动Web服务"""
    import uvicorn

    logger.info(f"Starting web server at {host}:{port}")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
    )


def run_gui(backend_port: int = 8000, frontend_port: int = 8501, no_browser: bool = False):
    """一键启动GUI界面（后端+前端）"""
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 50)
    print("Auto Job Hunter - 启动中...")
    print("=" * 50)

    # 启动后端服务
    print(f"\n[1/3] 启动后端服务 (端口 {backend_port})...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", str(backend_port),
    ]
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 启动前端服务
    print(f"[2/3] 启动前端服务 (端口 {frontend_port})...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port", str(frontend_port),
        "--server.headless", "true",
    ]
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=project_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 等待服务启动
    print("[3/3] 等待服务就绪...")
    time.sleep(2)

    # 打开浏览器
    frontend_url = f"http://localhost:{frontend_port}"
    if not no_browser:
        print(f"正在打开浏览器: {frontend_url}")
        webbrowser.open(frontend_url)

    print("\n" + "=" * 50)
    print("服务已启动!")
    print(f"  前端界面: {frontend_url}")
    print(f"  后端API:  http://localhost:{backend_port}")
    print(f"  API文档:  http://localhost:{backend_port}/docs")
    print("=" * 50)
    print("\n按 Ctrl+C 停止服务...")

    try:
        # 等待进程结束
        while True:
            if backend_process.poll() is not None:
                print("后端服务已停止")
                break
            if frontend_process.poll() is not None:
                print("前端服务已停止")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
    finally:
        # 确保两个进程都被终止
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait(timeout=5)
        frontend_process.wait(timeout=5)
        print("服务已停止")


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
        "--backend-port",
        type=int,
        default=8000,
        help="后端服务端口"
    )
    gui_parser.add_argument(
        "--frontend-port",
        type=int,
        default=8501,
        help="前端服务端口"
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
        print("  - BOSS_USERNAME/BOSS_PASSWORD: BOSS直聘账号")
        print("  - LIEPIN_USERNAME/LIEPIN_PASSWORD: 猎聘账号")
        print("  - OPENAI_API_KEY: OpenAI API密钥(可选)")
        print("\n启动Web服务: python -m backend.cli web")
        print("启动GUI界面: python -m backend.cli gui")

    elif args.command == "gui":
        run_gui(
            backend_port=args.backend_port,
            frontend_port=args.frontend_port,
            no_browser=args.no_browser,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()