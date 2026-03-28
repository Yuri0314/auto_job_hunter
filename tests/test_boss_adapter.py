"""测试BOSS直聘适配器"""

import asyncio
import sys
sys.path.insert(0, '.')

from backend.adapters import BossAdapter, Platform, get_adapter
from backend.automation.browser import get_browser_manager
from backend.automation.browser.cookie_manager import get_cookie_manager


async def test_boss_adapter():
    """测试BOSS适配器核心功能"""
    print("=" * 60)
    print("测试 BOSS直聘适配器")
    print("=" * 60)

    # 测试1: 使用get_adapter创建适配器（模拟API调用流程）
    print("\n[测试1] 模拟API调用流程...")
    adapter = get_adapter(Platform.BOSS)
    print(f"  适配器创建成功: {adapter}")

    # 测试2: 检查登录状态
    print("\n[测试2] 检查登录状态...")
    try:
        is_logged_in = await adapter.check_login_status()
        print(f"  登录状态: {'已登录' if is_logged_in else '未登录'}")

        if not is_logged_in:
            print("  ❌ 未登录，跳过后续测试")
            return []
    except Exception as e:
        print(f"  ❌ 检查登录状态失败: {e}")
        import traceback
        traceback.print_exc()
        return []

    # 测试3: 搜索职位
    print("\n[测试3] 搜索职位 'Python'...")
    try:
        result = await adapter.search_jobs(
            keywords="Python",
            city=None,
            page=1,
        )

        print(f"  搜索结果: {len(result.jobs)} 个职位")
        print(f"  错误信息: {result.error}")

        if result.jobs:
            print("\n  前5个职位:")
            for job in result.jobs[:5]:
                print(f"    - {job.title} | {job.company} | {job.salary} | {job.city}")
        else:
            print("  ⚠️ 没有找到职位")
    except Exception as e:
        print(f"  ❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()

    # 关闭浏览器
    print("\n[清理] 关闭浏览器...")
    browser_manager = get_browser_manager()
    await browser_manager.close()
    print("完成!")

    return result.jobs if 'result' in dir() else []


async def test_full_api_flow():
    """测试完整API流程"""
    print("\n" + "=" * 60)
    print("测试完整API流程（orchestrator）")
    print("=" * 60)

    from backend.services import get_orchestrator
    from backend.adapters import Platform

    try:
        orchestrator = await get_orchestrator(use_ai=False)
        print(f"  Orchestrator创建成功")

        jobs = await orchestrator.search_jobs(
            platforms=[Platform.BOSS],
            keywords="Python",
            city=None,
        )

        print(f"  搜索结果: {len(jobs)} 个职位")

        if jobs:
            print("\n  前3个职位:")
            for job in jobs[:3]:
                print(f"    - {job.title} | {job.company} | {job.salary}")

        return jobs
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("开始测试...\n")

    # 测试适配器
    jobs1 = asyncio.run(test_boss_adapter())

    print("\n" + "-" * 60 + "\n")

    # 测试完整流程
    jobs2 = asyncio.run(test_full_api_flow())

    print("\n" + "=" * 60)
    print(f"测试完成!")
    print(f"  适配器测试: {len(jobs1)} 个职位")
    print(f"  API流程测试: {len(jobs2)} 个职位")