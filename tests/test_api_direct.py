"""直接测试API内部逻辑"""

import asyncio
import sys
sys.path.insert(0, '.')

from backend.adapters import Platform
from backend.services import Orchestrator


async def test_direct():
    """直接测试搜索逻辑"""
    print("=" * 60)
    print("直接测试搜索逻辑")
    print("=" * 60)

    # 创建orchestrator
    orchestrator = Orchestrator(use_ai=False)
    await orchestrator.initialize()

    # 搜索职位
    print("\n开始搜索...")
    jobs = await orchestrator.search_jobs(
        platforms=[Platform.BOSS],
        keywords="Python",
        city=None,
    )

    print(f"\n搜索结果: {len(jobs)} 个职位")

    if jobs:
        print("\n前5个职位:")
        for job in jobs[:5]:
            print(f"  - {job.title} | {job.company} | {job.salary} | {job.city}")
    else:
        print("\n未找到职位")

    # 关闭浏览器
    from backend.automation.browser import get_browser_manager
    browser = get_browser_manager()
    await browser.close()

    return jobs


if __name__ == "__main__":
    jobs = asyncio.run(test_direct())
    print(f"\n最终结果: {len(jobs)} 个职位")