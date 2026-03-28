"""Debug BOSS page structure - deeper investigation"""

import asyncio
import sys
import os
import json

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def debug_api_interception():
    """Debug BOSS API interception"""
    print("=" * 60)
    print("Debug BOSS API Interception")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)
    page = await adapter._get_page()

    # Capture API responses
    api_data = []

    async def handle_response(response):
        url = response.url
        if "/wapi/zpgeek/" in url and ".json" in url:
            try:
                body = await response.text()
                if body:
                    data = json.loads(body)
                    api_data.append({
                        "url": url,
                        "data": data
                    })
                    print(f"\n[API] {url}")
                    if "zpData" in data:
                        zpData = data.get("zpData", {})
                        jobInfo = zpData.get("jobInfo", {})
                        if jobInfo:
                            print(f"  Job: {jobInfo.get('jobName', '')}")
                            print(f"  Salary: {jobInfo.get('salaryDesc', '')}")
            except Exception as e:
                pass

    page.on("response", handle_response)

    # Navigate to search page
    url = "https://www.zhipin.com/web/geek/jobs?query=Python&page=1"
    print(f"\nNavigating to: {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)

    # Get job cards and click first one
    cards = await page.query_selector_all("ul.rec-job-list li.job-card-box")
    print(f"Found {len(cards)} job cards")

    if cards:
        print("\nClicking first card to trigger API...")
        # Use waitForResponse to capture the API call
        try:
            async def click_card():
                await cards[0].click()

            detail_resp = await page.wait_for_response(
                lambda r: "/wapi/zpgeek/job/detail.json" in r.url() and r.request().method == "GET",
                click_card,
                timeout=10000
            )
            body = await detail_resp.text()
            data = json.loads(body)
            print(f"\n[Detail API Response]")
            zpData = data.get("zpData", {})
            jobInfo = zpData.get("jobInfo", {})
            print(f"  Job: {jobInfo.get('jobName', '')}")
            print(f"  Salary: {jobInfo.get('salaryDesc', '')}")
            print(f"  Location: {jobInfo.get('locationName', '')}")
            print(f"  Experience: {jobInfo.get('experienceName', '')}")
            print(f"  Degree: {jobInfo.get('degreeName', '')}")
        except Exception as e:
            print(f"  Click response capture failed: {e}")
        await asyncio.sleep(3)

    print(f"\nCaptured {len(api_data)} other API responses")

    for item in api_data:
        print(f"\n{'='*40}")
        print(f"URL: {item['url']}")
        if "zpData" in item['data']:
            print(json.dumps(item['data']['zpData'], indent=2, ensure_ascii=False)[:500])

    # Close browser
    from backend.automation.browser import get_browser_manager
    browser = get_browser_manager()
    await browser.close()

    print("\nDebug completed!")


if __name__ == "__main__":
    asyncio.run(debug_api_interception())