"""Direct test of adapter search"""

import asyncio
import sys
sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def test_direct_search():
    print("Direct search test...")

    adapter = get_adapter(Platform.BOSS)
    result = await adapter.search_jobs(keywords="Python")

    print(f"Jobs found: {len(result.jobs) if result.jobs else 0}")
    print(f"Error: {result.error}")

    if result.jobs:
        for job in result.jobs[:5]:
            print(f"\n  Title: {job.title}")
            print(f"  Company: {job.company}")
            print(f"  Salary: {job.salary}")
            print(f"  City: {job.city}")

    # Close browser
    from backend.automation.browser import get_browser_manager
    browser = get_browser_manager()
    await browser.close()


if __name__ == "__main__":
    asyncio.run(test_direct_search())