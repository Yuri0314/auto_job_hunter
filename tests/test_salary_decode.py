"""Test BOSS salary decoding"""

import asyncio
import sys
sys.path.insert(0, '.')

from backend.adapters import get_adapter, Platform


async def test_salary_decode():
    """Test salary decoding"""
    print("=" * 60)
    print("Test BOSS Salary Decode")
    print("=" * 60)

    adapter = get_adapter(Platform.BOSS)

    # Test decode method
    print("\n[Test 1] Salary decode method...")
    test_cases = [
        ("15-25K", "15-25K"),  # normal text
        ("\ue8f1\ue8f5-\ue8f2\ue8f5K", "15-25K"),  # dynamic font
        ("\uE8F2\uE8F0-\uE8F3\uE8F0K", "20-30K"),  # uppercase Unicode
    ]

    for raw, expected in test_cases:
        decoded = adapter._decode_salary(raw)
        status = "OK" if decoded == expected else "FAIL"
        print(f"  [{status}] '{repr(raw)}' -> '{decoded}' (expected: '{expected}')")

    # Test actual search
    print("\n[Test 2] Search jobs...")
    try:
        result = await adapter.search_jobs(
            keywords="Python",
            city=None,
            page=1,
        )

        print(f"  Found: {len(result.jobs)} jobs")

        if result.jobs:
            print("\n  Top 5 jobs:")
            for job in result.jobs[:5]:
                print(f"    - {job.title}")
                print(f"      Company: {job.company}")
                print(f"      Salary: {job.salary}")
                print(f"      City: {job.city}")
                print()
        else:
            print("  WARNING: No jobs found")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Close browser
    from backend.automation.browser import get_browser_manager
    browser = get_browser_manager()
    await browser.close()

    print("\nTest completed!")
    return result.jobs if 'result' in dir() else []


if __name__ == "__main__":
    jobs = asyncio.run(test_salary_decode())
    print(f"\nResult: {len(jobs)} jobs found")