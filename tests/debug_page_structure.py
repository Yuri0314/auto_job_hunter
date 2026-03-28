"""Debug BOSS page structure"""

import asyncio
import sys
import os

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def debug_page_structure():
    """Debug page structure to find salary elements"""
    print("=" * 60)
    print("Debug BOSS Page Structure")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)
    page = await adapter._get_page()

    # Navigate to search page
    url = "https://www.zhipin.com/web/geek/jobs?query=Python&page=1"
    print(f"\nNavigating to: {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5)

    # Get job cards
    cards = await page.query_selector_all("ul.rec-job-list li.job-card-box")
    print(f"Found {len(cards)} job cards")

    if cards:
        first_card = cards[0]

        # Try different salary selectors
        print("\n" + "=" * 40)
        print("Testing salary selectors:")
        print("=" * 40)

        selectors = [
            "span.salary",
            ".salary",
            "[class*='salary']",
            "span[class*='sal']",
            ".job-salary",
            "span.red",
            ".money",
            "span.money",
        ]

        for sel in selectors:
            el = await first_card.query_selector(sel)
            if el:
                text = await el.inner_text()
                decoded = adapter._decode_salary(text)
                # Use repr to handle special chars
                print(f"  {sel}: decoded='{decoded}' raw={repr(text)[:50]}")

        # Get all span elements and their classes
        print("\n" + "=" * 40)
        print("All spans with text in first card:")
        print("=" * 40)
        spans = await first_card.query_selector_all("span")
        for i, span in enumerate(spans[:15]):
            try:
                class_name = await span.get_attribute("class") or ""
                text = await span.inner_text()
                if text.strip():
                    decoded = adapter._decode_salary(text)
                    print(f"  [{i}] class='{class_name}' decoded='{decoded[:30]}'")
            except Exception as e:
                print(f"  [{i}] error: {e}")

    # Close browser
    from backend.automation.browser import get_browser_manager
    browser = get_browser_manager()
    await browser.close()

    print("\nDebug completed!")


if __name__ == "__main__":
    asyncio.run(debug_page_structure())