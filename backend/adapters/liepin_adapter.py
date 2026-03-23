"""猎聘平台适配器"""

import asyncio
import re
from typing import List, Optional
from loguru import logger
from playwright.async_api import Page

from backend.adapters.base_adapter import (
    BasePlatformAdapter,
    Platform,
    SearchResult,
    ApplicationResult,
    Message,
)
from backend.core.filter.simple_filter import JobInfo
from backend.automation.browser import PlaywrightManager, get_browser_manager
from backend.automation.browser.cookie_manager import CookieManager, get_cookie_manager
from backend.automation.interaction import HumanSimulator


class LiepinAdapter(BasePlatformAdapter):
    """猎聘平台适配器"""

    platform = Platform.LIEPIN

    BASE_URL = "https://www.liepin.com"
    LOGIN_URL = "https://www.liepin.com/normal/login"
    SEARCH_URL = "https://www.liepin.com/zhaopin/"

    LOGIN_INDICATOR = ".user-info"  # 登录后显示的用户信息

    def __init__(
        self,
        browser_manager: Optional[PlaywrightManager] = None,
        cookie_manager: Optional[CookieManager] = None,
    ):
        super().__init__()
        self.browser_manager = browser_manager or get_browser_manager()
        self.cookie_manager = cookie_manager or get_cookie_manager()
        self.human_sim = HumanSimulator()
        self._page: Optional[Page] = None

    @property
    def name(self) -> str:
        return "猎聘"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def _get_page(self) -> Page:
        if not self._page or self._page.is_closed():
            await self.browser_manager.start()
            self._page = await self.browser_manager.new_page()
        return self._page

    async def login(self, username: str, password: str) -> bool:
        """登录猎聘"""
        try:
            page = await self._get_page()
            context = self.browser_manager._context

            # 尝试加载Cookie
            if context:
                loaded = await self.cookie_manager.load_cookies(context, "liepin")
                if loaded:
                    await page.goto(self.BASE_URL)
                    await asyncio.sleep(2)
                    if await self.check_login_status():
                        self._logged_in = True
                        return True

            # 跳转登录页
            await page.goto(self.LOGIN_URL)
            await asyncio.sleep(2)

            # 尝试账号密码登录
            # 切换到密码登录
            pwd_tab = await page.query_selector(".login-title-password")
            if pwd_tab:
                await pwd_tab.click()
                await asyncio.sleep(1)

            # 输入账号密码
            await self.human_sim.human_type(page, "input[name='login']", username)
            await self.human_sim.human_type(page, "input[name='pwd']", password)

            # 点击登录
            login_btn = await page.query_selector(".btn-login")
            if login_btn:
                await login_btn.click()
                await asyncio.sleep(3)

                # 检查是否需要验证码
                captcha = await page.query_selector(".captcha-container")
                if captcha:
                    logger.warning("需要验证码，请手动完成")
                    await asyncio.sleep(30)

                if await self.check_login_status():
                    self._logged_in = True
                    if context:
                        await self.cookie_manager.save_cookies(context, "liepin")
                    return True

            return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def check_login_status(self) -> bool:
        try:
            page = await self._get_page()
            user_info = await page.query_selector(self.LOGIN_INDICATOR)
            return user_info is not None
        except Exception:
            return False

    async def search_jobs(
        self,
        keywords: str,
        city: Optional[str] = None,
        salary_range: Optional[tuple] = None,
        experience: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResult:
        """搜索职位"""
        try:
            page_obj = await self._get_page()

            # 构建搜索URL
            url = f"{self.SEARCH_URL}?key={keywords}"

            if city:
                url += f"&city={city}"

            if salary_range:
                min_sal, max_sal = salary_range
                url += f"&salary={min_sal}-{max_sal}"

            if experience:
                url += f"&workYear={experience}"

            url += f"&curPage={page}"

            await page_obj.goto(url)
            await asyncio.sleep(2)

            # 等待职位列表
            await page_obj.wait_for_selector(".sojob-list", timeout=10000)

            jobs = await self._parse_job_list(page_obj)

            # 检查是否有更多
            next_btn = await page_obj.query_selector(".pagerbar a.next")
            has_more = next_btn is not None

            return SearchResult(
                jobs=jobs,
                total_count=len(jobs),
                page=page,
                page_size=page_size,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(f"Search jobs failed: {e}")
            return SearchResult(error=str(e))

    async def _parse_job_list(self, page: Page) -> List[JobInfo]:
        """解析职位列表"""
        jobs = []

        items = await page.query_selector_all(".sojob-list .job-info")

        for item in items:
            try:
                # 提取职位ID
                link = await item.query_selector("a[data-jobid]")
                job_id = await link.get_attribute("data-jobid") if link else ""

                # 职位标题
                title_el = await item.query_selector(".job-title")
                title = await title_el.inner_text() if title_el else ""

                # 薪资
                salary_el = await item.query_selector(".text-warning")
                salary_text = await salary_el.inner_text() if salary_el else ""
                salary_min, salary_max = self._parse_salary(salary_text)

                # 公司
                company_el = await item.query_selector(".company-name a")
                company = await company_el.inner_text() if company_el else ""

                # 城市
                area_el = await item.query_selector(".area")
                city = await area_el.inner_text() if area_el else ""

                job = JobInfo(
                    id=job_id,
                    title=title.strip(),
                    company=company.strip(),
                    salary=salary_text.strip(),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    city=city.strip(),
                    platform="liepin",
                )
                jobs.append(job)

            except Exception as e:
                logger.debug(f"Parse job error: {e}")
                continue

        return jobs

    async def get_job_detail(self, job_id: str) -> Optional[JobInfo]:
        """获取职位详情"""
        # TODO: 实现
        return None

    async def apply_job(
        self,
        job_id: str,
        greeting: Optional[str] = None,
        resume_id: Optional[str] = None,
    ) -> ApplicationResult:
        """投递职位"""
        try:
            page = await self._get_page()

            # 猎聘投递需要访问职位详情页
            detail_url = f"{self.BASE_URL}/job/{job_id}.shtml"
            await page.goto(detail_url)
            await asyncio.sleep(2)

            # 查找投递按钮
            apply_btn = await page.query_selector(".btn-apply")
            if apply_btn:
                await apply_btn.click()
                await asyncio.sleep(2)

                return ApplicationResult(
                    success=True,
                    job_id=job_id,
                    message="投递成功",
                )

            return ApplicationResult(
                success=False,
                job_id=job_id,
                error="未找到投递按钮",
            )

        except Exception as e:
            logger.error(f"Apply job failed: {e}")
            return ApplicationResult(
                success=False,
                job_id=job_id,
                error=str(e),
            )

    async def get_messages(
        self,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Message]:
        """获取HR消息"""
        # TODO: 实现
        return []

    async def reply_message(
        self,
        message_id: str,
        content: str,
    ) -> bool:
        """回复消息"""
        # TODO: 实现
        return False

    def _parse_salary(self, salary_text: str) -> tuple:
        """解析薪资"""
        # 示例: "15-25万" -> (15, 25) 猎聘是年薪
        match = re.search(r"(\d+)-(\d+)万", salary_text)
        if match:
            # 转换为月薪K
            return int(int(match.group(1)) / 12 * 10), int(int(match.group(2)) / 12 * 10)

        return None, None