"""Debug BOSS API - use wait_for_response concurrently"""

import asyncio
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def debug_concurrent():
    """Debug BOSS API using concurrent wait_for_response"""
    print("=" * 60)
    print("Debug BOSS API via concurrent wait_for_response")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)
    page = await adapter._get_page()

    url = "https://www.zhipin.com/web/geek/jobs?query=Python&page=1"
    print(f"\nNavigating to: {url}")

    # Run navigation and wait_for_response concurrently
    try:
        # Start waiting for response before navigating
        response_task = asyncio.create_task(
            page.wait_for_response(
                lambda r: "/wapi/zpgeek/search/joblist.json" in r.url(),
                timeout=30000
            )
        )

        # Navigate in parallel
        await page.goto(url, timeout=60000)

        # Wait for response task
        response = await response_task

        print(f"[Captured response]: {response.url}")
        body = await response.text()
        data = json.loads(body)

        print(f"\nTotal results: {data.get('resCount', 0)}")
        job_list = data.get('jobList', [])
        print(f"Jobs in response: {len(job_list)}")

        if job_list:
            print("\n" + "=" * 40)
            print("First 3 jobs:")
            print("=" * 40)
            for i, job in enumerate(job_list[:3]):
                print(f"\n[{i+1}]")
                print(f"  jobName: {job.get('jobName', 'N/A')}")
                print(f"  brandName: {job.get('brandName', 'N/A')}")
                print(f"  salaryDesc: {job.get('salaryDesc', 'N/A')}")
                print(f"  cityName: {job.get('cityName', 'N/A')}")
                print(f"  experienceName: {job.get('experienceName', 'N/A')}")
                print(f"  degreeName: {job.get('degreeName', 'N/A')}")

            print("\n" + "=" * 40)
            print("All keys in first job:")
            print("=" * 40)
            keys = list(job_list[0].keys())
            print(keys)
            print(f"\nTotal keys: {len(keys)}")

        else:
            print("\nNo jobs in API response")
            # Check DOM
            await asyncio.sleep(3)
            cards = await page.query_selector_all("ul.rec-job-list li.job-card-box")
            print(f"DOM cards: {len(cards)}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Close
    await adapter.browser_manager.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(debug_concurrent())