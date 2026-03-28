"""Debug API response parsing"""

import asyncio
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def debug_parsing():
    """Debug the API parsing"""
    print("=" * 60)
    print("Debug API Parsing")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)
    browser = await adapter.browser_manager.start()
    context = adapter.browser_manager._context
    await adapter.cookie_manager.load_cookies(context, "boss")

    page = await context.new_page()

    # Capture API response
    captured = [None]

    async def capture(response):
        if "/wapi/zpgeek/search/joblist.json" in response.url:
            try:
                body = await response.body()
                captured[0] = json.loads(body.decode('utf-8'))
                print(f"Captured: {len(body)} bytes")
            except Exception as e:
                print(f"Capture error: {e}")

    page.on("response", capture)

    # Navigate
    await page.goto("https://www.zhipin.com/web/geek/jobs?query=Python", wait_until="load", timeout=60000)
    await asyncio.sleep(8)

    if captured[0]:
        # Parse the data
        jobs = adapter._parse_joblist_api(captured[0])
        print(f"\nParsed {len(jobs)} jobs")

        for job in jobs[:5]:
            print(f"\n--- Job ---")
            print(f"  id: {job.id}")
            print(f"  title: {job.title}")
            print(f"  company: {job.company}")
            print(f"  salary: '{job.salary}'")  # Use quotes to see if empty
            print(f"  salary_min: {job.salary_min}")
            print(f"  salary_max: {job.salary_max}")
            print(f"  city: {job.city}")

    # Close
    await adapter.browser_manager.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(debug_parsing())