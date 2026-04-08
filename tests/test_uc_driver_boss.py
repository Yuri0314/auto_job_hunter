"""测试 undetected_chromedriver 是否能正常访问 BOSS 直聘"""

import asyncio
from backend.automation.browser.uc_driver_manager import get_uc_driver_manager


async def test_uc_driver_boss():
    """测试 uc 浏览器访问 BOSS 直聘"""
    print("=" * 60)
    print("Testing undetected-chromedriver with BOSS Zhipin")
    print("=" * 60)

    uc = get_uc_driver_manager()

    try:
        print("\n[1] Starting browser...")
        await uc.start()
        print("    Browser started successfully")

        print("\n[2] Checking navigator.webdriver...")
        # 检查 webdriver 特征是否被隐藏
        script = "return navigator.webdriver"
        webdriver_value = uc._driver.execute_script(script)
        print(f"    navigator.webdriver = {webdriver_value}")
        if webdriver_value is None or webdriver_value == False:
            print("    [PASS] webdriver feature is hidden!")
        else:
            print("    [FAIL] webdriver feature is DETECTED!")

        print("\n[3] Navigating to BOSS Zhipin search page...")
        url = "https://www.zhipin.com/web/geek/jobs?query=Python&city=101010100&page=1"
        uc._driver.get(url)
        print(f"    Current URL: {uc._driver.current_url}")

        # 检查是否被重定向或白屏
        if "blank" in uc._driver.current_url:
            print("    [FAIL] Page is about:blank -可能被重定向!")
        elif "zhipin.com" in uc._driver.current_url:
            print("    [PASS] Still on zhipin.com - 正常访问!")
        else:
            print(f"    [WARN] Redirected to: {uc._driver.current_url}")

        print("\n[4] Waiting for page to load...")
        await asyncio.sleep(5)

        # 检查是否有职位列表
        try:
            job_cards = uc._driver.find_elements("xpath", "//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
            print(f"    Found {len(job_cards)} job cards")
            if len(job_cards) > 0:
                print("    [PASS] Job listings loaded successfully!")
            else:
                print("    [WARN] No job cards found - may need login")
        except Exception as e:
            print(f"    ✗ Error finding job cards: {e}")

        # 检查是否有错误信息
        try:
            error_text = uc._driver.page_source
            if "检测到异常" in error_text or "访问受限" in error_text:
                print("    [FAIL] Detected anti-bot message!")
            else:
                print("    [PASS] No anti-bot messages detected")
        except Exception:
            pass

        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await uc.close()


if __name__ == "__main__":
    asyncio.run(test_uc_driver_boss())
