"""猎聘平台适配器"""

import asyncio
import re
from typing import List, Optional
from datetime import datetime
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

            # 自动加载已保存的 Cookie
            context = self.browser_manager._context
            if context:
                loaded = await self.cookie_manager.load_cookies(context, "liepin")
                if loaded:
                    logger.info("Auto-loaded saved cookies for Liepin")

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

            # 先访问首页，使用 domcontentloaded 避免 networkidle 无限等待
            await page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # 检查多个可能的登录指示器
            login_indicators = [
                ".user-info",  # 原有选择器
                ".user-name",  # 新版可能的用户名选择器
                ".header-user-info",  # header中的用户信息
                "a[href*='/resume/']",  # 简历链接（登录后才可见）
                ".so-signin-btn",  # 如果存在登录按钮说明未登录
            ]

            # 检查是否存在登录按钮（如果有说明未登录）
            login_btn = await page.query_selector(".so-signin-btn")
            if login_btn:
                logger.info("Liepin: Login button found - not logged in")
                return False

            # 检查用户信息元素
            for selector in login_indicators[:-1]:  # 排除登录按钮选择器
                user_info = await page.query_selector(selector)
                if user_info:
                    logger.info(f"Liepin: Found login indicator '{selector}' - logged in")
                    return True

            # 尝试检查页面URL是否包含登录相关路径
            current_url = page.url
            if "login" in current_url.lower():
                logger.info("Liepin: On login page - not logged in")
                return False

            logger.warning("Liepin: Could not determine login status, assuming logged in")
            return True
        except Exception as e:
            logger.error(f"Liepin check_login_status error: {e}")
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

            # 构建搜索URL - 猎聘新版URL格式
            # 参考: https://www.liepin.com/zhaopin/?key=Python&city=北京
            url = f"{self.SEARCH_URL}?key={keywords}"

            if city:
                # 猎聘城市参数可能需要城市编码，先尝试直接传城市名
                url += f"&city={city}"

            if salary_range:
                min_sal, max_sal = salary_range
                # 猎聘薪资参数格式
                url += f"&salary={min_sal}-{max_sal}"

            if experience:
                url += f"&workYear={experience}"

            # 猎聘分页参数 - 使用正确的参数名
            # 猎聘新版使用 pageNum 或 curPage，需要测试
            if page > 1:
                # 尝试两种分页参数格式
                url += f"&curPage={page}"  # 原有格式
                # 或者使用 pageNum
                # url += f"&pageNum={page}"

            logger.info(f"Liepin: Navigating to search URL: {url}")
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # 尝试多个可能的职位列表选择器
            job_list_selectors = [
                ".sojob-list",  # 原有选择器
                ".job-list-box",  # 新版可能的选择器
                ".left-list-box .sojob-list",  # 左侧列表区域
                "div[data-selector='sojob-list']",  # data属性选择器
            ]

            job_list_found = False
            for selector in job_list_selectors:
                try:
                    await page_obj.wait_for_selector(selector, timeout=10000)
                    logger.info(f"Liepin: Found job list with selector: {selector}")
                    job_list_found = True
                    break
                except Exception:
                    logger.debug(f"Liepin: Selector '{selector}' not found, trying next...")
                    continue

            if not job_list_found:
                logger.warning("Liepin: Could not find job list container, attempting direct parsing")
                # 尝试直接解析页面内容
                jobs = await self._parse_job_list_fallback(page_obj)
                return SearchResult(
                    jobs=jobs,
                    total_count=len(jobs),
                    page=page,
                    page_size=page_size,
                    has_more=False,
                )

            jobs = await self._parse_job_list(page_obj)
            logger.info(f"Liepin: Parsed {len(jobs)} jobs from page {page}")

            # 检查是否有更多 - 使用JavaScript检测更可靠
            has_more = await self._check_has_more(page_obj)
            logger.info(f"Liepin: Has more pages: {has_more}")

            return SearchResult(
                jobs=jobs,
                total_count=len(jobs),
                page=page,
                page_size=page_size,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(f"Liepin search_jobs failed: {e}")
            return SearchResult(error=str(e))

    async def _parse_job_list(self, page: Page) -> List[JobInfo]:
        """解析职位列表"""
        jobs = []

        # 尝试多个选择器组合
        job_item_selectors = [
            ".sojob-list .job-info",
            ".sojob-list .sojob-item",
            ".job-list-box .job-item",
            ".left-list-box .sojob-item",
        ]

        items = []
        for selector in job_item_selectors:
            try:
                items = await page.query_selector_all(selector)
                if items:
                    logger.info(f"Liepin: Found {len(items)} items with selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Liepin: Error with selector {selector}: {e}")
                continue

        if not items:
            logger.warning("Liepin: No job items found with any selector")
            return jobs

        for item in items:
            try:
                # 提取职位ID - 多种方式
                job_id = ""
                link = await item.query_selector("a[data-jobid]")
                if link:
                    job_id = await link.get_attribute("data-jobid") or ""
                else:
                    # 尝试从链接href提取
                    link = await item.query_selector("a[href*='/job/']")
                    if link:
                        href = await link.get_attribute("href") or ""
                        # 从 /job/19123.shtml 提取ID
                        match = re.search(r"/job/(\d+)", href)
                        if match:
                            job_id = match.group(1)

                # 职位标题 - 多个选择器
                title_selectors = [".job-title", ".job-name", "a[data-jobid]", ".title"]
                title = ""
                for sel in title_selectors:
                    title_el = await item.query_selector(sel)
                    if title_el:
                        title = await title_el.inner_text()
                        if title:
                            break

                # 薪资 - 多个选择器
                salary_selectors = [".text-warning", ".salary", ".job-salary", ".item-warning"]
                salary_text = ""
                for sel in salary_selectors:
                    salary_el = await item.query_selector(sel)
                    if salary_el:
                        salary_text = await salary_el.inner_text()
                        if salary_text:
                            break
                salary_min, salary_max = self._parse_salary(salary_text)

                # 公司 - 多个选择器
                company_selectors = [".company-name a", ".company-name", ".cname a", ".company"]
                company = ""
                for sel in company_selectors:
                    company_el = await item.query_selector(sel)
                    if company_el:
                        company = await company_el.inner_text()
                        if company:
                            break

                # 城市 - 多个选择器
                city_selectors = [".area", ".city", ".location", ".work-city"]
                city = ""
                for sel in city_selectors:
                    area_el = await item.query_selector(sel)
                    if area_el:
                        city = await area_el.inner_text()
                        if city:
                            break

                # 构建URL
                job_url = ""
                if job_id:
                    job_url = f"{self.BASE_URL}/job/{job_id}.shtml"

                job = JobInfo(
                    id=job_id or f"liepin-{hash(title + company)}",
                    title=title.strip(),
                    company=company.strip(),
                    salary=salary_text.strip(),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    city=city.strip(),
                    platform="liepin",
                    url=job_url,
                )
                jobs.append(job)

            except Exception as e:
                logger.debug(f"Liepin parse job error: {e}")
                continue

        return jobs

    async def _parse_job_list_fallback(self, page: Page) -> List[JobInfo]:
        """备用解析方法 - 直接从页面HTML解析"""
        jobs = []
        try:
            # 获取页面内容并尝试解析
            content = await page.content()
            logger.debug(f"Liepin fallback: Page content length: {len(content)}")

            # 使用JavaScript直接提取数据
            job_data = await page.evaluate("""
                () => {
                    const jobs = [];
                    // 尝试查找所有可能的职位卡片
                    const cards = document.querySelectorAll('.sojob-item, .job-item, [class*="job"]');
                    cards.forEach(card => {
                        try {
                            const titleEl = card.querySelector('[class*="title"], [class*="name"], a');
                            const salaryEl = card.querySelector('[class*="salary"], [class*="warning"]');
                            const companyEl = card.querySelector('[class*="company"], [class*="cname"]');
                            const cityEl = card.querySelector('[class*="area"], [class*="city"]');

                            if (titleEl && titleEl.innerText) {
                                jobs.push({
                                    title: titleEl.innerText.trim(),
                                    salary: salaryEl ? salaryEl.innerText.trim() : '',
                                    company: companyEl ? companyEl.innerText.trim() : '',
                                    city: cityEl ? cityEl.innerText.trim() : ''
                                });
                            }
                        } catch(e) {}
                    });
                    return jobs;
                }
            """)

            for i, data in enumerate(job_data or []):
                if data.get('title'):
                    salary_min, salary_max = self._parse_salary(data.get('salary', ''))
                    job = JobInfo(
                        id=f"liepin-fallback-{i}",
                        title=data.get('title', '').strip(),
                        company=data.get('company', '').strip(),
                        salary=data.get('salary', '').strip(),
                        salary_min=salary_min,
                        salary_max=salary_max,
                        city=data.get('city', '').strip(),
                        platform="liepin",
                    )
                    jobs.append(job)

            logger.info(f"Liepin fallback: Found {len(jobs)} jobs via JavaScript extraction")

        except Exception as e:
            logger.error(f"Liepin fallback parsing error: {e}")

        return jobs

    async def _check_has_more(self, page: Page) -> bool:
        """检查是否有更多页面"""
        try:
            # 使用JavaScript检测分页状态
            has_more = await page.evaluate("""
                () => {
                    // 检查各种可能的分页元素
                    const selectors = [
                        '.pagerbar a.next',
                        '.pagination a.next',
                        'a[data-page="next"]',
                        '.page-next',
                        '.sojob-pager a.next',
                        '.pager a.next',
                        '[class*="next"]',
                    ];

                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && !el.classList.contains('disabled') && !el.classList.contains('hide')) {
                            // 检查是否是有效的下一页链接
                            const href = el.getAttribute('href') || '';
                            const text = el.innerText || '';
                            if (text.includes('下一页') || text.includes('Next') || href.includes('curPage') || href.includes('pageNum')) {
                                return true;
                            }
                        }
                    }

                    // 检查是否有总页数信息
                    const totalPageEl = document.querySelector('.pagerbar .total, .pagination .total, [class*="total"]');
                    if (totalPageEl) {
                        const totalText = totalPageEl.innerText;
                        const currentPage = document.querySelector('.pagerbar .current, .pagination .current, [class*="current"]');
                        if (currentPage) {
                            const currentNum = parseInt(currentPage.innerText) || 1;
                            const match = totalText.match(/\\d+/);
                            if (match) {
                                const totalNum = parseInt(match[0]);
                                return currentNum < totalNum;
                            }
                        }
                    }

                    // 检查是否还有职位卡片（如果有职位且没到最后一页）
                    const jobCount = document.querySelectorAll('.sojob-item, .job-item, [class*="job-card"]').length;
                    if (jobCount > 0) {
                        // 简单假设有职位就可能有更多（保守策略）
                        // 但要看是否有禁用的下一页按钮
                        const disabledNext = document.querySelector('.pagerbar a.next.disabled, .pagination a.next.disabled');
                        if (disabledNext) {
                            return false;
                        }
                        return true;
                    }

                    return false;
                }
            """)
            return bool(has_more)
        except Exception as e:
            logger.error(f"Liepin _check_has_more error: {e}")
            return False

    async def get_job_detail(self, job_id: str) -> Optional[JobInfo]:
        """获取职位详情"""
        try:
            page = await self._get_page()
            url = f"{self.BASE_URL}/job/{job_id}.shtml"

            await page.goto(url)
            await asyncio.sleep(2)

            # 提取职位标题
            title_el = await page.query_selector(".job-title")
            title = await title_el.inner_text() if title_el else ""

            # 提取薪资
            salary_el = await page.query_selector(".salary")
            salary_text = await salary_el.inner_text() if salary_el else ""
            salary_min, salary_max = self._parse_salary(salary_text)

            # 提取公司名称
            company_el = await page.query_selector(".company-name")
            company = await company_el.inner_text() if company_el else ""

            # 提取城市
            location_el = await page.query_selector(".location")
            city = await location_el.inner_text() if location_el else ""

            # 提取职位描述
            desc_el = await page.query_selector(".job-description")
            description = await desc_el.inner_text() if desc_el else ""

            return JobInfo(
                id=job_id,
                title=title.strip(),
                company=company.strip(),
                salary=salary_text.strip(),
                salary_min=salary_min,
                salary_max=salary_max,
                city=city.strip(),
                description=description.strip(),
                platform="liepin",
            )

        except Exception as e:
            logger.error(f"Get job detail failed: {e}")
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
        try:
            page = await self._get_page()

            # 访问消息页面
            await page.goto(f"{self.BASE_URL}/message/")
            await asyncio.sleep(2)

            messages = []

            # 解析消息列表
            chat_items = await page.query_selector_all(".message-item")
            for item in chat_items[:limit]:
                try:
                    msg = await self._parse_message_item(item)
                    if msg:
                        if not unread_only or not msg.is_read:
                            messages.append(msg)
                except Exception as e:
                    logger.debug(f"Parse message item error: {e}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"Get messages failed: {e}")
            return []

    async def _parse_message_item(self, item) -> Optional[Message]:
        """解析单个消息项"""
        try:
            # 获取会话ID
            chat_id = await item.get_attribute("data-id") or ""

            # HR姓名
            name_el = await item.query_selector(".sender-name")
            hr_name = await name_el.inner_text() if name_el else "HR"

            # 公司名称
            company_el = await item.query_selector(".company-name")
            company = await company_el.inner_text() if company_el else ""

            # 消息内容
            msg_el = await item.query_selector(".message-content")
            content = await msg_el.inner_text() if msg_el else ""

            # 时间
            time_el = await item.query_selector(".message-time")
            time_text = await time_el.inner_text() if time_el else ""
            timestamp = self._parse_message_time(time_text)

            # 未读标记
            unread_el = await item.query_selector(".unread-mark")
            is_read = unread_el is None

            return Message(
                id=chat_id,
                hr_name=hr_name.strip(),
                company=company.strip(),
                content=content.strip(),
                timestamp=timestamp,
                is_read=is_read,
                platform="liepin",
            )

        except Exception as e:
            logger.debug(f"Parse message item error: {e}")
            return None

    def _parse_message_time(self, time_text: str) -> datetime:
        """解析消息时间"""
        now = datetime.now()
        if not time_text:
            return now

        time_text = time_text.strip()

        if ":" in time_text and len(time_text) <= 5:
            try:
                hour, minute = time_text.split(":")
                return now.replace(hour=int(hour), minute=int(minute), second=0)
            except ValueError:
                pass

        if "昨天" in time_text:
            try:
                time_part = time_text.replace("昨天", "").strip()
                hour, minute = time_part.split(":")
                return now.replace(day=now.day - 1, hour=int(hour), minute=int(minute), second=0)
            except ValueError:
                return now.replace(day=now.day - 1)

        return now

    async def reply_message(
        self,
        message_id: str,
        content: str,
    ) -> bool:
        """回复消息"""
        try:
            page = await self._get_page()

            # 访问消息页面
            await page.goto(f"{self.BASE_URL}/message/")
            await asyncio.sleep(2)

            # 查找对应会话
            chat_item = await page.query_selector(f'.message-item[data-id="{message_id}"]')
            if not chat_item:
                logger.warning(f"Chat item not found: {message_id}")
                return False

            # 点击进入会话
            await chat_item.click()
            await asyncio.sleep(1)

            # 查找输入框
            input_el = await page.query_selector(".message-input")
            if not input_el:
                input_el = await page.query_selector("textarea[placeholder]")

            if not input_el:
                logger.error("Message input not found")
                return False

            # 输入消息
            await self.human_sim.human_type(page, ".message-input", content)
            await asyncio.sleep(1)

            # 发送
            send_btn = await page.query_selector(".send-btn")
            if send_btn:
                await send_btn.click()
                await asyncio.sleep(1)
                logger.info(f"Message sent to {message_id}")
                return True
            else:
                await input_el.press("Enter")
                await asyncio.sleep(1)
                logger.info(f"Message sent to {message_id} (via Enter)")
                return True

        except Exception as e:
            logger.error(f"Reply message failed: {e}")
            return False

    def _parse_salary(self, salary_text: str) -> tuple:
        """解析薪资"""
        # 示例: "15-25万" -> (15, 25) 猎聘是年薪
        match = re.search(r"(\d+)-(\d+)万", salary_text)
        if match:
            # 转换为月薪K
            return int(int(match.group(1)) / 12 * 10), int(int(match.group(2)) / 12 * 10)

        return None, None