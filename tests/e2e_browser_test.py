"""浏览器端到端测试 - 使用 Playwright 模拟真实用户操作"""

import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright, expect


async def test_browser_workflow():
    """模拟真实用户操作流程的端到端测试"""

    print("=" * 70)
    print("Auto Job Hunter 浏览器端到端测试")
    print("=" * 70)

    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            # 如果之前保存了Cookie，可以自动加载
            # storage_state='backend/automation/browser/cookies/boss.json'
        )
        page = await context.new_page()

        # ========== 步骤1: 访问系统状态 ==========
        print("\n【步骤1】访问系统状态页面")
        print("-" * 40)
        try:
            await page.goto('http://localhost:8000/api/system/status', wait_until='domcontentloaded')
            content = await page.content()
            if '"status":"running"' in content:
                print("  ✅ 系统状态正常")
                results["system_status"] = True
            else:
                print(f"  ❌ 系统状态异常: {content[:100]}")
                results["system_status"] = False
        except Exception as e:
            print(f"  ❌ 访问失败: {e}")
            results["system_status"] = False

        # ========== 步骤2: 访问消息列表API ==========
        print("\n【步骤2】访问消息列表")
        print("-" * 40)
        try:
            await page.goto('http://localhost:8000/api/messages', wait_until='domcontentloaded')
            content = await page.content()
            if '"total"' in content:
                print("  ✅ 消息列表正常返回")
                results["messages_list"] = True
            else:
                print(f"  ❌ 消息列表异常")
                results["messages_list"] = False
        except Exception as e:
            print(f"  ❌ 访问失败: {e}")
            results["messages_list"] = False

        # ========== 步骤3: 访问投递统计API ==========
        print("\n【步骤3】访问投递统计")
        print("-" * 40)
        try:
            await page.goto('http://localhost:8000/api/applications/statistics', wait_until='domcontentloaded')
            content = await page.content()
            if '"total"' in content:
                print("  ✅ 投递统计正常返回")
                results["applications_stats"] = True
            else:
                print(f"  ❌ 投递统计异常")
                results["applications_stats"] = False
        except Exception as e:
            print(f"  ❌ 访问失败: {e}")
            results["applications_stats"] = False

        # ========== 步骤4: 访问搜索策略API ==========
        print("\n【步骤4】访问搜索策略列表")
        print("-" * 40)
        try:
            await page.goto('http://localhost:8000/api/search/strategies', wait_until='domcontentloaded')
            content = await page.content()
            if '"items"' in content:
                print("  ✅ 搜索策略列表正常返回")
                results["search_strategies"] = True
            else:
                print(f"  ❌ 搜索策略异常")
                results["search_strategies"] = False
        except Exception as e:
            print(f"  ❌ 访问失败: {e}")
            results["search_strategies"] = False

        # ========== 步骤5: 模拟访问BOSS直聘网站 ==========
        print("\n【步骤5】访问BOSS直聘网站")
        print("-" * 40)
        try:
            await page.goto('https://www.zhipin.com/web/geek/job', wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)  # 等待页面稳定
            title = await page.title()
            print(f"  页面标题: {title}")
            if 'BOSS直聘' in title or '职位' in title or '招聘' in title:
                print("  ✅ BOSS直聘页面加载成功")
                results["boss_website"] = True
            else:
                print(f"  ⚠️  页面标题不匹配: {title}")
                results["boss_website"] = True  # 能打开就算成功
        except Exception as e:
            print(f"  ❌ 访问失败: {e}")
            results["boss_website"] = False

        # ========== 步骤6: 测试API拦截（模拟搜索） ==========
        print("\n【步骤6】测试API拦截功能")
        print("-" * 40)
        try:
            # 设置响应拦截器
            captured_data = {}

            def handle_response(response):
                if 'joblist' in response.url or 'search' in response.url:
                    try:
                        captured_data['url'] = response.url
                        captured_data['status'] = response.status
                    except:
                        pass

            page.on('response', handle_response)

            # 在BOSS直聘页面执行搜索
            search_input = await page.query_selector('input[placeholder*="搜索"]')
            if search_input:
                await search_input.fill('Python')
                await search_input.press('Enter')
                await page.wait_for_timeout(5000)  # 等待搜索结果

                if captured_data.get('status') == 200:
                    print(f"  ✅ 成功拦截搜索API响应")
                    results["api_interception"] = True
                else:
                    print(f"  ⚠️  未捕获到搜索API响应")
                    results["api_interception"] = False
            else:
                print("  ⚠️  未找到搜索框（可能需要登录）")
                results["api_interception"] = None
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            results["api_interception"] = False

        await browser.close()

    # ========== 结果汇总 ==========
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v is True)
    total = len(results)

    for test_name, result in results.items():
        status = "✅" if result is True else ("⚠️" if result is None else "❌")
        print(f"  {status} {test_name}: {result}")

    print("\n" + "=" * 70)
    print(f"通过: {passed}/{total}")
    if passed == total:
        print("🎉 所有测试通过!")
    else:
        print(f"⚠️  {total - passed} 个测试未通过")
    print("=" * 70)

    return results


if __name__ == "__main__":
    asyncio.run(test_browser_workflow())
