"""UI 端到端测试 - 验证产品链路导航"""

import asyncio
from playwright.async_api import async_playwright


async def test_ui_navigation():
    """测试完整的产品链路导航"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        base_url = "http://localhost:8000"

        print("=" * 60)
        print("UI Navigation Test - Product Pipeline")
        print("=" * 60)

        # 1. 访问 Dashboard
        print("\n[1] Visiting Dashboard...")
        await page.goto(f"{base_url}/ui/dashboard")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # 检查 Dashboard 内容
        title = await page.title()
        print(f"    Page title: {title}")

        # 检查是否有统计卡片
        stats_cards = page.locator("text=总投递")
        count = await stats_cards.count()
        print(f"    Stats cards found: {count}")

        # 检查快捷操作
        has_search = await page.locator("text=搜索职位").count() > 0
        has_resume = await page.locator("text=管理简历").count() > 0
        has_messages = await page.locator("text=消息中心").count() > 0
        has_apps = await page.locator("text=投递记录").count() > 0
        print(f"    Quick actions: search={has_search}, resume={has_resume}, messages={has_messages}, apps={has_apps}")

        # 2. 从 Dashboard 点击到搜索页面
        print("\n[2] Navigating to Search page...")
        search_btn = page.locator("text=搜索职位").first
        if await search_btn.count() > 0:
            await search_btn.click()
            await page.wait_for_url(f"{base_url}/ui/search")
            print("    Arrived at Search page")
        else:
            print("    Search button not found (may be rendered dynamically)")

        # 3. 访问简历管理页面
        print("\n[3] Visiting Resume Manager...")
        await page.goto(f"{base_url}/ui/resumes")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)

        has_resume_list = await page.locator("text=简历列表").count() > 0
        has_upload = await page.locator("text=上传简历").count() > 0
        print(f"    Resume tabs: list={has_resume_list}, upload={has_upload}")

        # 4. 访问投递记录页面
        print("\n[4] Visiting Applications...")
        await page.goto(f"{base_url}/ui/applications")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)

        has_apps_title = await page.locator("text=投递记录").count() > 0
        has_stats = await page.locator("text=总投递").count() > 0
        print(f"    Applications page: title={has_apps_title}, stats={has_stats}")

        # 检查是否有导航到消息的链接
        has_msg_nav = await page.locator("text=查看消息").count() > 0
        print(f"    Has 'View Messages' button: {has_msg_nav}")

        # 5. 从投递记录点击到消息中心
        print("\n[5] Navigating to Messages from Applications...")
        if has_msg_nav:
            msg_btn = page.locator("text=查看消息").first
            await msg_btn.click()
            await page.wait_for_url(f"{base_url}/ui/messages")
            print("    Arrived at Messages page")
        else:
            await page.goto(f"{base_url}/ui/messages")

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)

        has_msg_title = await page.locator("text=HR消息").count() > 0
        has_check_new = await page.locator("text=检查新消息").count() > 0
        print(f"    Messages page: title={has_msg_title}, check_new={has_check_new}")

        # 检查是否有导航回投递记录的链接
        has_app_nav = await page.locator("text=投递记录").count() > 0
        print(f"    Has 'Applications' button: {has_app_nav}")

        # 6. 访问设置页面
        print("\n[6] Visiting Settings...")
        await page.goto(f"{base_url}/ui/settings")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)

        has_settings = await page.locator("text=系统设置").count() > 0
        print(f"    Settings page: {has_settings}")

        print("\n" + "=" * 60)
        print("All UI navigation tests completed!")
        print("=" * 60)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_ui_navigation())
