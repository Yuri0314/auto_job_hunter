"""Debug BOSS API - use response handler with body caching"""

import asyncio
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def debug_with_cdp():
    """Debug BOSS API using CDP-style response capture"""
    print("=" * 60)
    print("Debug BOSS API via Response Handler")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)
    browser = await adapter.browser_manager.start()
    context = adapter.browser_manager._context

    # Load cookies
    await adapter.cookie_manager.load_cookies(context, "boss")

    # Create new page
    page = await context.new_page()

    # Cache responses by URL
    response_bodies = {}

    async def capture_response(response):
        url = response.url
        if "/wapi/zpgeek/search/joblist.json" in url:
            print(f"[Found joblist API]: {url}")
            try:
                # Get body immediately in the handler
                body = await response.body()
                response_bodies[url] = body.decode('utf-8')
                print(f"[Body length: {len(body)} bytes]")
            except Exception as e:
                print(f"[Body capture error: {e}]")

    page.on("response", capture_response)

    url = "https://www.zhipin.com/web/geek/jobs?query=Python&page=1"
    print(f"\nNavigating to: {url}")

    # Navigate and wait for network to settle
    await page.goto(url, wait_until="load", timeout=60000)

    # Wait additional time for API calls
    print("Waiting for API calls...")
    await asyncio.sleep(10)

    # Check captured bodies
    print(f"\nCaptured {len(response_bodies)} responses")

    for url_key, body in response_bodies.items():
        print(f"\nParsing: {url_key[:80]}...")
        try:
            data = json.loads(body)
            # The data structure is: { code, message, zpData: { resCount, jobList, ... } }
            zpData = data.get('zpData', {})
            print(f"Total results: {zpData.get('resCount', 0)}")
            job_list = zpData.get('jobList', [])
            print(f"Jobs: {len(job_list)}")

            if job_list:
                print("\n" + "=" * 40)
                print("First 3 jobs from API:")
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
                print("All keys in job object:")
                print("=" * 40)
                keys = list(job_list[0].keys())
                print(keys)
                print(f"\nTotal keys: {len(keys)}")

            else:
                print("No jobs in zpData.jobList")

        except Exception as e:
            print(f"Parse error: {e}")
            import traceback
            traceback.print_exc()

    # Also check DOM
    cards = await page.query_selector_all("ul.rec-job-list li.job-card-box")
    print(f"\nDOM job cards: {len(cards)}")

    # Close
    await adapter.browser_manager.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(debug_with_cdp())