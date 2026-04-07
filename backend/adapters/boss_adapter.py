"""BOSS直聘平台适配器"""

import asyncio
import re
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from playwright.async_api import Page, BrowserContext, Response

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
    """BOSS直聘平台适配器

    使用API拦截方式获取职位数据，绕过BOSS的动态字体渲染。
    API返回的salaryDesc已经是解码好的正确薪资。
    """

    platform = Platform.BOSS

    # 平台配置
    BASE_URL = "https://www.zhipin.com"
    LOGIN_URL = "https://www.zhipin.com/web/user/?ka=header-login"
    SEARCH_URL = "https://www.zhipin.com/web/geek/jobs"

    # API endpoints
    JOBLIST_API = "/wapi/zpgeek/search/joblist.json"
    JOB_DETAIL_API = "/wapi/zpgeek/job/detail.json"

    # 登录状态检查选择器
    LOGIN_INDICATOR = "//li[@class='nav-figure']"  # 登录后显示的头像

    # 职位列表选择器 (备用，当API拦截失败时使用)
    JOB_CARD_SELECTOR = "ul.rec-job-list li.job-card-box"

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
        self._api_data: Dict[str, Any] = {}  # 缓存API响应数据

    @property
    def name(self) -> str:
        return "BOSS直聘"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def _get_page(self, load_cookies: bool = True) -> Page:
        """获取页面对象

        Args:
            load_cookies: 是否自动加载已保存的 Cookie（登录时设为 False）
        """
        if not self._page or self._page.is_closed():
            await self.browser_manager.start()
            self._page = await self.browser_manager.new_page()

            # 自动加载已保存的 Cookie
            if load_cookies:
                context = self.browser_manager._context
                if context:
                    loaded = await self.cookie_manager.load_cookies(context, "boss")
                    if loaded:
                        logger.info("Auto-loaded saved cookies for BOSS")

        return self._page

    async def login(self, username: str, password: str) -> bool:
        """登录BOSS直聘

        用户手动在浏览器中输入手机号+验证码登录
        """
        try:
            # 清除旧的 Cookie 文件，确保干净的登录环境
            self.cookie_manager.delete_cookies("boss")
            logger.info("Cleared old cookies for fresh login")

            # 关闭旧页面
            if self._page and not self._page.is_closed():
                await self._page.close()
                self._page = None

            # 启动浏览器
            await self.browser_manager.start()
            self._page = await self.browser_manager.new_page()
            context = self.browser_manager._context

            # 直接跳转到登录页
            logger.info(f"Navigating to login page: {self.LOGIN_URL}")
            await self._page.goto(self.LOGIN_URL)
            await asyncio.sleep(2)

            logger.info("请在打开的浏览器中输入手机号+验证码完成登录")

            # 等待用户手动登录（最多等待5分钟）
            for i in range(150):  # 5分钟 = 150 * 2秒
                await asyncio.sleep(2)
                # 检查当前页面是否有登录后的头像
                avatar = await self._page.query_selector(self.LOGIN_INDICATOR)
                if avatar:
                    self._logged_in = True
                    # 保存Cookie
                    if context:
                        await self.cookie_manager.save_cookies(context, "boss")
                    logger.info("Login successful, cookies saved")
                    return True
                # 每30秒提示一下
                if i > 0 and i % 15 == 0:
                    logger.info(f"等待登录中... ({i * 2}秒)")

            logger.error("Login timeout")
            return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            page = await self._get_page()

            # 先访问首页 - 使用 load 而不是 networkidle，更快
            await page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(1)

            # 检查是否有用户头像（登录后显示）- 使用XPath
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
        """搜索职位 - 使用API拦截获取数据

        BOSS的API返回已解码的薪资数据，无需处理动态字体。
        即使未登录，API也能返回数据。
        """
        try:
            page_obj = await self._get_page()

            # 构建搜索URL
            url = f"{self.SEARCH_URL}?query={keywords}"

            if city:
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
                salary_code = self._get_salary_code(min_sal, max_sal)
                if salary_code:
                    url += f"&salary={salary_code}"

            if experience:
                exp_code = self._get_experience_code(experience)
                if exp_code:
                    url += f"&experience={exp_code}"

            url += f"&page={page}"

            logger.info(f"Navigating to: {url}")

            # 使用 expect_response 捕获 API 响应
            api_data = {}

            async with page_obj.expect_response(
                lambda r: self.JOBLIST_API in r.url,
                timeout=15000
            ) as response_info:
                await page_obj.goto(url, wait_until="domcontentloaded", timeout=30000)

            # 获取响应 - response_info.value 是协程
            try:
                response = await response_info.value
                data = await response.json()
                api_data['joblist'] = data
                logger.info("Captured joblist API via expect_response")
            except Exception as e:
                logger.warning(f"Failed to get joblist response: {e}")

            # 检查 API 数据
            if 'joblist' in api_data:
                jobs = self._parse_joblist_api(api_data['joblist'])
                logger.info(f"Parsed {len(jobs)} jobs from API")

                zpData = api_data['joblist'].get('zpData', {})
                has_more = zpData.get('hasMore', False)

                return SearchResult(
                    jobs=jobs,
                    total_count=len(jobs),
                    page=page,
                    page_size=page_size,
                    has_more=has_more,
                )

            # API 捕获失败，尝试 DOM 解析
            logger.warning("API data not captured, falling back to DOM parsing")

            # 等待页面加载
            await asyncio.sleep(3)

            jobs = await self._parse_job_list(page_obj)
            logger.info(f"Parsed {len(jobs)} jobs from DOM")

            return SearchResult(
                jobs=jobs,
                total_count=len(jobs),
                page=page,
                page_size=page_size,
                has_more=False,
            )

        except Exception as e:
            logger.error(f"Search jobs failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return SearchResult(error=str(e))

    def _parse_joblist_api(self, api_data: dict) -> List[JobInfo]:
        """解析API返回的职位列表数据

        API返回的数据结构:
        {
            "code": 0,
            "zpData": {
                "resCount": 450,
                "jobList": [
                    {
                        "jobName": "python",
                        "brandName": "华为技术有限公司",
                        "salaryDesc": "200-250元/天",  # 已解码的正确薪资
                        "cityName": "杭州",
                        ...
                    }
                ]
            }
        }
        """
        jobs = []

        zpData = api_data.get('zpData', {})
        job_list = zpData.get('jobList', [])

        for job_data in job_list:
            try:
                # 解析薪资
                salary_desc = job_data.get('salaryDesc', '')
                salary_min, salary_max = self._parse_salary(salary_desc)

                job = JobInfo(
                    id=job_data.get('encryptJobId', ''),
                    title=job_data.get('jobName', '').strip(),
                    company=job_data.get('brandName', '').strip(),
                    salary=salary_desc.strip(),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    city=job_data.get('cityName', '').strip(),
                    description=' '.join(job_data.get('skills', [])),
                    url=f"{self.BASE_URL}/job_detail/{job_data.get('encryptJobId', '')}.html",
                    platform="boss",
                    # 额外信息 - 使用正确的字段名
                    experience_required=job_data.get('jobExperience', ''),
                    hr_name=job_data.get('bossName', ''),
                )
                jobs.append(job)
            except Exception as e:
                logger.debug(f"Parse job from API error: {e}")
                continue

        return jobs

    async def _parse_job_list(self, page: Page) -> List[JobInfo]:
        """解析职位列表 - 备用的DOM解析方式"""
        jobs = []

        # 使用 get_jobs 项目的选择器
        job_cards = await page.query_selector_all("ul.rec-job-list li.job-card-box")

        if not job_cards:
            logger.warning("No job cards found in DOM")
            return jobs

        for card in job_cards:
            try:
                job = await self._parse_job_card(card)
                if job and job.title:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Parse job card error: {e}")
                continue

        return jobs

    async def _parse_job_card(self, card) -> Optional[JobInfo]:
        """解析单个职位卡片"""
        try:
            # 提取职位标题
            title_el = await card.query_selector("a.job-name")
            title = await title_el.inner_text() if title_el else ""

            # 提取链接和职位ID
            href = await title_el.get_attribute("href") if title_el else ""
            job_id = self._extract_job_id(href) if href else ""

            # 提取薪资 - 尝试多个选择器
            salary_text = ""
            salary_el = await card.query_selector(".job-salary")
            if salary_el:
                raw_salary = await salary_el.inner_text()
                salary_text = self._decode_salary(raw_salary)

            # 提取公司名称
            company_el = await card.query_selector("span.boss-name")
            company = await company_el.inner_text() if company_el else ""

            # 提取城市区域
            area_el = await card.query_selector("span.company-location")
            city = await area_el.inner_text() if area_el else ""

            # 提取职位标签
            tag_els = await card.query_selector_all("ul.tag-list li")
            tags = []
            for tag in tag_els:
                text = await tag.inner_text()
                if text.strip():
                    tags.append(text.strip())

            salary_min, salary_max = self._parse_salary(salary_text)

            return JobInfo(
                id=job_id,
                title=title.strip(),
                company=company.strip(),
                salary=salary_text.strip(),
                salary_min=salary_min,
                salary_max=salary_max,
                city=city.strip().split("·")[0] if city else "",
                description=" ".join(tags),
                url=f"{self.BASE_URL}{href}" if href else None,
                platform="boss",
            )
        except Exception as e:
            logger.debug(f"Parse job card error: {e}")
            return None

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
        """解析单个消息项

        BOSS直聘消息列表结构:
        .chat-item 包含:
        - .name: HR姓名
        - .company-text: 公司名称
        - .msg-text: 最新消息内容
        - .time: 时间
        - .unread: 未读标记
        - data-geek: 会话ID
        """
        try:
            # 获取会话ID
            chat_id = await item.get_attribute("data-geek")
            if not chat_id:
                # 尝试从其他属性获取
                chat_id = await item.get_attribute("data-id")

            # HR姓名
            name_el = await item.query_selector(".name")
            hr_name = await name_el.inner_text() if name_el else "HR"

            # 公司名称
            company_el = await item.query_selector(".company-text")
            if not company_el:
                company_el = await item.query_selector(".company-name")
            company = await company_el.inner_text() if company_el else ""

            # 最新消息内容
            msg_el = await item.query_selector(".msg-text")
            if not msg_el:
                msg_el = await item.query_selector(".msg")
            content = await msg_el.inner_text() if msg_el else ""

            # 时间
            time_el = await item.query_selector(".time")
            time_text = await time_el.inner_text() if time_el else ""
            timestamp = self._parse_message_time(time_text)

            # 未读标记
            unread_el = await item.query_selector(".unread")
            is_read = unread_el is None

            # 职位名称（可能在消息内容附近）
            job_el = await item.query_selector(".job-name")
            job_title = await job_el.inner_text() if job_el else None

            return Message(
                id=chat_id or "",
                hr_name=hr_name.strip(),
                company=company.strip(),
                content=content.strip(),
                timestamp=timestamp,
                is_read=is_read,
                job_title=job_title.strip() if job_title else None,
                platform="boss",
            )

        except Exception as e:
            logger.debug(f"Parse chat item error: {e}")
            return None

    def _parse_message_time(self, time_text: str) -> datetime:
        """解析消息时间

        支持格式:
        - HH:MM (今天)
        - 昨天 HH:MM
        - MM-DD HH:MM
        - YYYY-MM-DD
        """
        now = datetime.now()

        if not time_text:
            return now

        time_text = time_text.strip()

        # 格式: HH:MM (今天)
        if ":" in time_text and len(time_text) <= 5:
            try:
                hour, minute = time_text.split(":")
                return now.replace(hour=int(hour), minute=int(minute), second=0)
            except ValueError:
                pass

        # 格式: 昨天 HH:MM
        if "昨天" in time_text:
            time_part = time_text.replace("昨天", "").strip()
            try:
                hour, minute = time_part.split(":")
                yesterday = now.replace(day=now.day - 1)
                return yesterday.replace(hour=int(hour), minute=int(minute), second=0)
            except ValueError:
                return now.replace(day=now.day - 1)

        # 格式: MM-DD HH:MM
        if "-" in time_text and ":" in time_text:
            try:
                date_part, time_part = time_text.split(" ")
                month, day = date_part.split("-")
                hour, minute = time_part.split(":")
                return now.replace(
                    month=int(month),
                    day=int(day),
                    hour=int(hour),
                    minute=int(minute),
                    second=0,
                )
            except ValueError:
                pass

        # 格式: MM-DD
        if "-" in time_text and len(time_text) <= 5:
            try:
                month, day = time_text.split("-")
                return now.replace(month=int(month), day=int(day))
            except ValueError:
                pass

        return now

    async def reply_message(
        self,
        message_id: str,
        content: str,
    ) -> bool:
        """回复消息

        Args:
            message_id: 会话ID (data-geek)
            content: 回复内容

        Returns:
            是否成功
        """
        try:
            page = await self._get_page()

            # 访问消息页面
            await page.goto(f"{self.BASE_URL}/web/geek/chat")
            await asyncio.sleep(2)

            # 查找对应会话
            chat_item = await page.query_selector(f'.chat-item[data-geek="{message_id}"]')
            if not chat_item:
                # 尝试用 data-id
                chat_item = await page.query_selector(f'.chat-item[data-id="{message_id}"]')

            if not chat_item:
                logger.warning(f"Chat item not found: {message_id}")
                return False

            # 点击进入会话
            await chat_item.click()
            await asyncio.sleep(1)

            # 查找输入框
            input_el = await page.query_selector(".chat-input")
            if not input_el:
                # 尝试其他选择器
                input_el = await page.query_selector("textarea[placeholder]")
                if not input_el:
                    input_el = await page.query_selector(".input-box textarea")

            if not input_el:
                logger.error("Chat input not found")
                return False

            # 使用人机模拟输入
            await self.human_sim.human_type(page, ".chat-input", content)
            await asyncio.sleep(1)

            # 发送消息
            send_btn = await page.query_selector(".send-btn")
            if not send_btn:
                send_btn = await page.query_selector("button:has-text('发送')")

            if send_btn:
                await send_btn.click()
                await asyncio.sleep(1)
                logger.info(f"Message sent to {message_id}")
                return True
            else:
                # 尝试按 Enter 发送
                await input_el.press("Enter")
                await asyncio.sleep(1)
                logger.info(f"Message sent to {message_id} (via Enter)")
                return True

        except Exception as e:
            logger.error(f"Reply message failed: {e}")
            return False

    def _extract_job_id(self, href: str) -> str:
        """从URL提取职位ID"""
        match = re.search(r"job/(\d+)\.html", href)
        if match:
            return match.group(1)
        return ""

    def _decode_salary(self, text: str) -> str:
        """Decode BOSS dynamic font rendered salary.

        BOSS uses custom fonts to obfuscate numbers.
        Maps Unicode chars back to real numbers.
        Two encoding ranges used:
        - Old: U+E8Fx
        - New: U+E03x
        """
        if not text:
            return text

        # BOSS custom font mapping (old version)
        font_map = {
            '\uE8F0': '0', '\ue8f0': '0',
            '\uE8F1': '1', '\ue8f1': '1',
            '\uE8F2': '2', '\ue8f2': '2',
            '\uE8F3': '3', '\ue8f3': '3',
            '\uE8F4': '4', '\ue8f4': '4',
            '\uE8F5': '5', '\ue8f5': '5',
            '\uE8F6': '6', '\ue8f6': '6',
            '\uE8F7': '7', '\ue8f7': '7',
            '\uE8F8': '8', '\ue8f8': '8',
            '\uE8F9': '9', '\ue8f9': '9',
            # New version encoding
            '\uE030': '0', '\ue030': '0',
            '\uE031': '1', '\ue031': '1',
            '\uE032': '2', '\ue032': '2',
            '\uE033': '3', '\ue033': '3',
            '\uE034': '4', '\ue034': '4',
            '\uE035': '5', '\ue035': '5',
            '\uE036': '6', '\ue036': '6',
            '\uE037': '7', '\ue037': '7',
            '\uE038': '8', '\ue038': '8',
            '\uE039': '9', '\ue039': '9',
        }

        result = []
        for char in text:
            result.append(font_map.get(char, char))
        return ''.join(result)

    def _parse_salary(self, salary_text: str) -> tuple:
        """解析薪资文本，返回(min, max) K"""
        if not salary_text:
            return None, None

        # 先解码动态字体
        decoded = self._decode_salary(salary_text)

        # 示例: "15-25K" -> (15, 25)
        match = re.search(r"(\d+)-(\d+)K", decoded, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))

        match = re.search(r"(\d+)K以上", decoded, re.IGNORECASE)
        if match:
            return int(match.group(1)), 999

        # 也尝试解析"天"薪资
        match = re.search(r"(\d+)-(\d+)元/天", decoded)
        if match:
            return int(match.group(1)), int(match.group(2))

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