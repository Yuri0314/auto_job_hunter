"""Debug BOSS API - get full joblist.json structure"""

import asyncio
import sys
import os
import json

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform
from playwright.async_api import Response


async def debug_joblist_api():
    """Debug BOSS joblist API structure"""
    print("=" * 60)
    print("Debug BOSS Joblist API Structure")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)
    page = await adapter._get_page()

    # Navigate and wait for joblist API
    url = "https://www.zhipin.com/web/geek/jobs?query=Python&page=1"
    print(f"\nNavigating to: {url}")

    # Use route to intercept and capture response
    joblist_data = None

    async def handle_route(route):
        response = await route.fetch()
        if "/wapi/zpgeek/search/joblist.json" in route.request.url:
            body = await response.text()
            print(f"[Captured joblist.json via route]")
            try:
                joblist_data = json.loads(body)
            except:
                pass
        await route.fulfill(response=response)

    # This approach doesn't work well, let's use page.on_response with finished check
    captured_urls = []

    async def log_response(response: Response):
        url = response.url
        if "/wapi/zpgeek/search/joblist.json" in url:
            captured_urls.append(url)
            print(f"[Found joblist.json API]: {url}")

    page.on("response", log_response)

    # Navigate
    await page.goto(url, wait_until="networkidle", timeout=60000)

    # Check if we captured the URL
    print(f"\nCaptured URLs: {captured_urls}")

    # Alternative: Use page.evaluate to get data from window object
    # BOSS might store data in window.__INITIAL_STATE__ or similar

    try:
        # Try to get job data from page's JavaScript context
        job_data_script = await page.evaluate("""
            () => {
                // Try multiple possible storage locations
                if (window.__INITIAL_STATE__) return JSON.stringify(window.__INITIAL_STATE__);
                if (window.__NUXT__) return JSON.stringify(window.__NUXT__);
                if (window.__PRELOADED_STATE__) return JSON.stringify(window.__PRELOADED_STATE__);
                return null;
            }
        """)
        if job_data_script:
            print("\n[Found data in window object]")
            # Parse and display
            data = json.loads(job_data_script)
            print(f"Keys in __INITIAL_STATE__: {list(data.keys())[:10]}")
    except Exception as e:
        print(f"No data in window: {e}")

    # Also check DOM for job cards
    cards = await page.query_selector_all("ul.rec-job-list li.job-card-box")
    print(f"\nFound {len(cards)} job cards in DOM")

    if cards:
        print("\n" + "=" * 40)
        print("Testing alternative: get salary from detail API")
        print("=" * 40)

        # Get the securityId from first card for detail API
        first_card = cards[0]
        link = await first_card.query_selector("a.job-name")
        if link:
            href = await link.get_attribute("href")
            print(f"Link href: {href}")

        # Hover over first card to trigger detail API
        await first_card.hover()
        await asyncio.sleep(2)

    # Close browser
    from backend.automation.browser import get_browser_manager
    browser = get_browser_manager()
    await browser.close()

    print("\nDebug completed!")


if __name__ == "__main__":
    asyncio.run(debug_joblist_api())