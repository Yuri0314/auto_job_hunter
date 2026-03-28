"""Debug BOSS API - use route to intercept response"""

import asyncio
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def debug_with_route():
    """Debug BOSS API using route interception"""
    print("=" * 60)
    print("Debug BOSS API via Route Interception")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)
    browser = await adapter.browser_manager.start()
    context = adapter.browser_manager._context

    # Create new page with route handler
    page = await context.new_page()

    # Intercept joblist API
    joblist_data = [None]

    async def intercept_route(route):
        request = route.request
        # Continue the request
        response = await route.fetch()

        if "/wapi/zpgeek/search/joblist.json" in request.url:
            try:
                body = await response.text()
                print(f"\n[Intercepted joblist.json]")
                joblist_data[0] = json.loads(body)
            except Exception as e:
                print(f"Parse error: {e}")

        await route.fulfill(response=response)

    await page.route("**/wapi/zpgeek/search/joblist.json**", intercept_route)

    # Load cookies
    await adapter.cookie_manager.load_cookies(context, "boss")

    # Navigate
    url = "https://www.zhipin.com/web/geek/jobs?query=Python&page=1"
    print(f"\nNavigating to: {url}")
    await page.goto(url, wait_until="networkidle", timeout=60000)

    # Check captured data
    if joblist_data[0]:
        data = joblist_data[0]
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
                print(f"  areaDistrict: {job.get('areaDistrict', 'N/A')}")
                print(f"  experienceName: {job.get('experienceName', 'N/A')}")
                print(f"  degreeName: {job.get('degreeName', 'N/A')}")

            # Print all keys
            print("\n" + "=" * 40)
            print("All keys in first job:")
            print("=" * 40)
            print(list(job_list[0].keys()))
    else:
        print("\nNo data captured")
        cards = await page.query_selector_all("ul.rec-job-list li.job-card-box")
        print(f"DOM cards: {len(cards)}")

    # Close
    await adapter.browser_manager.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(debug_with_route())