"""BOSS直聘平台适配器"""

import asyncio
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from playwright.async_api import Page, BrowserContext

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


class BossAdapter(BasePlatformAdapter):
    """BOSS直聘平台适配器"""

    platform = Platform.BOSS

    # 平台配置
    BASE_URL = "https://www.zhipin.com"
    LOGIN_URL = "https://www.zhipin.com/web/user/?ka=header-login"
    SEARCH_URL = "https://www.zhipin.com/web/geek/job"

    # 登录状态检查选择器
    LOGIN_INDICATOR = ".nav-figure"  # 登录后显示的头像

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
        return "BOSS直聘"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def _get_page(self) -> Page:
        """获取页面对象"""
        if not self._page or self._page.is_closed():
            await self.browser_manager.start()
            self._page = await self.browser_manager.new_page()
        return self._page

    async def login(self, username: str, password: str) -> bool:
        """登录BOSS直聘

        注意: BOSS直聘通常需要扫码登录或短信验证码
        此方法提供自动登录框架，但主要依赖Cookie持久化
        """
        try:
            page = await self._get_page()
            context = self.browser_manager._context

            # 尝试加载已保存的Cookie
            if context:
                loaded = await self.cookie_manager.load_cookies(context, "boss")
                if loaded:
                    logger.info("Loaded saved cookies for BOSS")
                    await page.goto(self.BASE_URL)
                    await asyncio.sleep(2)

                    if await self.check_login_status():
                        self._logged_in = True
                        return True

            # 跳转到登录页
            await page.goto(self.LOGIN_URL)
            await asyncio.sleep(2)

            logger.warning(
                "BOSS直聘通常需要扫码登录或短信验证码。"
                "请手动完成登录，登录成功后程序将自动保存Cookie。"
            )

            # 等待用户手动登录（最多等待5分钟）
            for _ in range(150):  # 5分钟 = 150 * 2秒
                await asyncio.sleep(2)
                if await self.check_login_status():
                    self._logged_in = True
                    # 保存Cookie
                    if context:
                        await self.cookie_manager.save_cookies(context, "boss")
                    logger.info("Login successful, cookies saved")
                    return True

            logger.error("Login timeout")
            return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            page = await self._get_page()

            # 检查是否有用户头像（登录后显示）
            avatar = await page.query_selector(self.LOGIN_INDICATOR)
            return avatar is not None

        except Exception as e:
            logger.debug(f"Check login status error: {e}")
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
            url = f"{self.SEARCH_URL}?query={keywords}"

            if city:
                # 城市代码映射
                city_codes = {
                    "北京": "101010100",
                    "上海": "101020100",
                    "广州": "101280100",
                    "深圳": "101280600",
                    "杭州": "101210100",
                    "成都": "101270100",
                }
                city_code = city_codes.get(city, "101010100")
                url += f"&city={city_code}"

            if salary_range:
                min_sal, max_sal = salary_range
                # BOSS薪资代码映射
                salary_code = self._get_salary_code(min_sal, max_sal)
                if salary_code:
                    url += f"&salary={salary_code}"

            if experience:
                exp_code = self._get_experience_code(experience)
                if exp_code:
                    url += f"&experience={exp_code}"

            url += f"&page={page}"

            # 访问搜索页
            await page_obj.goto(url)
            await asyncio.sleep(2)

            # 等待职位列表加载
            await page_obj.wait_for_selector(".job-list-box", timeout=10000)

            # 解析职位列表
            jobs = await self._parse_job_list(page_obj)

            # 检查是否有更多
            next_btn = await page_obj.query_selector(".options-pages a[ka='page-next']")
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

        job_cards = await page.query_selector_all(".job-card-wrapper")

        for card in job_cards:
            try:
                # 提取职位ID
                job_link = await card.query_selector(".job-card-left")
                href = await job_link.get_attribute("href") if job_link else ""
                job_id = self._extract_job_id(href) if href else ""

                # 提取职位标题
                title_el = await card.query_selector(".job-name")
                title = await title_el.inner_text() if title_el else ""

                # 提取薪资
                salary_el = await card.query_selector(".salary")
                salary_text = await salary_el.inner_text() if salary_el else ""
                salary_min, salary_max = self._parse_salary(salary_text)

                # 提取公司名称
                company_el = await card.query_selector(".company-name a")
                company = await company_el.inner_text() if company_el else ""

                # 提取公司信息标签
                tags = await card.query_selector_all(".company-tag-list li")
                company_info = []
                for tag in tags:
                    text = await tag.inner_text()
                    company_info.append(text)

                # 提取城市
                area_el = await card.query_selector(".job-area")
                city = await area_el.inner_text() if area_el else ""

                # 提取职位标签
                job_tags = await card.query_selector_all(".tag-list li")
                job_tag_texts = []
                for tag in job_tags:
                    text = await tag.inner_text()
                    job_tag_texts.append(text)

                job = JobInfo(
                    id=job_id,
                    title=title.strip(),
                    company=company.strip(),
                    salary=salary_text.strip(),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    city=city.strip().split("·")[0],  # 去掉区县
                    description=" ".join(job_tag_texts),
                    url=f"{self.BASE_URL}{href}" if href else None,
                    platform="boss",
                )
                jobs.append(job)

            except Exception as e:
                logger.debug(f"Parse job card error: {e}")
                continue

        return jobs

    async def get_job_detail(self, job_id: str) -> Optional[JobInfo]:
        """获取职位详情"""
        try:
            page = await self._get_page()
            url = f"{self.BASE_URL}/web/geek/job?query=&page=1&ka=job-{job_id}"

            await page.goto(url)
            await asyncio.sleep(2)

            # 解析职位详情
            detail = await self._parse_job_detail(page)
            if detail:
                detail.id = job_id
            return detail

        except Exception as e:
            logger.error(f"Get job detail failed: {e}")
            return None

    async def _parse_job_detail(self, page: Page) -> Optional[JobInfo]:
        """解析职位详情页"""
        # TODO: 实现详情页解析
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

            # 先访问职位详情页
            detail_url = f"{self.BASE_URL}/web/geek/job?query=&page=1&ka=job-{job_id}"
            await page.goto(detail_url)
            await asyncio.sleep(2)

            # 查找"立即沟通"按钮
            chat_btn = await page.query_selector(".op-btn.op-btn-chat")
            if not chat_btn:
                # 可能已经沟通过
                chat_btn = await page.query_selector(".op-btn.op-btn-start")

            if chat_btn:
                await chat_btn.click()
                await asyncio.sleep(2)

                # 如果需要输入打招呼语
                if greeting:
                    input_el = await page.query_selector(".chat-input")
                    if input_el:
                        await self.human_sim.human_type(page, ".chat-input", greeting)
                        await asyncio.sleep(1)

                        # 发送
                        send_btn = await page.query_selector(".send-btn")
                        if send_btn:
                            await send_btn.click()

                return ApplicationResult(
                    success=True,
                    job_id=job_id,
                    message="投递成功",
                )
            else:
                return ApplicationResult(
                    success=False,
                    job_id=job_id,
                    error="未找到沟通按钮",
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
        """获取HR消息列表"""
        try:
            page = await self._get_page()

            # 访问消息页面
            await page.goto(f"{self.BASE_URL}/web/geek/chat")
            await asyncio.sleep(2)

            messages = []

            # 解析消息列表
            chat_items = await page.query_selector_all(".chat-item")
            for item in chat_items[:limit]:
                try:
                    msg = await self._parse_chat_item(item)
                    if msg:
                        if not unread_only or not msg.is_read:
                            messages.append(msg)
                except Exception as e:
                    logger.debug(f"Parse chat item error: {e}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"Get messages failed: {e}")
            return []

    async def _parse_chat_item(self, item) -> Optional[Message]:
        """解析单个消息项"""
        # TODO: 实现消息解析
        return None

    async def reply_message(
        self,
        message_id: str,
        content: str,
    ) -> bool:
        """回复消息"""
        try:
            page = await self._get_page()

            # 访问消息页面并找到对应会话
            await page.goto(f"{self.BASE_URL}/web/geek/chat")
            await asyncio.sleep(2)

            # TODO: 实现消息回复
            return False

        except Exception as e:
            logger.error(f"Reply message failed: {e}")
            return False

    def _extract_job_id(self, href: str) -> str:
        """从URL提取职位ID"""
        match = re.search(r"job/(\d+)\.html", href)
        if match:
            return match.group(1)
        return ""

    def _parse_salary(self, salary_text: str) -> tuple:
        """解析薪资文本，返回(min, max) K"""
        # 示例: "15-25K" -> (15, 25)
        match = re.search(r"(\d+)-(\d+)K", salary_text)
        if match:
            return int(match.group(1)), int(match.group(2))

        match = re.search(r"(\d+)K以上", salary_text)
        if match:
            return int(match.group(1)), 999

        return None, None

    def _get_salary_code(self, min_sal: int, max_sal: int) -> Optional[str]:
        """获取BOSS薪资代码"""
        # BOSS薪资代码映射
        salary_map = {
            (0, 3): "401",    # 3K以下
            (3, 5): "402",    # 3-5K
            (5, 10): "403",   # 5-10K
            (10, 20): "404",  # 10-20K
            (20, 30): "405",  # 20-30K
            (30, 50): "406",  # 30-50K
            (50, 999): "407", # 50K以上
        }

        for (min_v, max_v), code in salary_map.items():
            if min_sal >= min_v and max_sal <= max_v:
                return code

        return None

    def _get_experience_code(self, experience: str) -> Optional[str]:
        """获取经验代码"""
        exp_map = {
            "应届": "101",
            "1年": "102",
            "1-3年": "103",
            "3-5年": "104",
            "5-10年": "105",
            "10年以上": "106",
        }
        return exp_map.get(experience)