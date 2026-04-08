"""BOSS直聘平台适配器

使用 undetected_chromedriver 绕过 BOSS 直聘反爬检测。
uc 修改 Chrome 内存特征，比 playwright_stealth 更有效。

参考:
- https://github.com/EnterIen/boss-job-spider
- https://github.com/ultrafunkamsterdam/undetected-chromedriver
"""

import asyncio
import re
import json
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

from backend.adapters.base_adapter import (
    BasePlatformAdapter,
    Platform,
    SearchResult,
    ApplicationResult,
    Message,
)
from backend.core.filter.simple_filter import JobInfo
from backend.automation.browser.uc_driver_manager import get_uc_driver_manager, UCDriverManager
from backend.automation.browser.cookie_manager import CookieManager, get_cookie_manager
from backend.automation.interaction import HumanSimulator


class BossAdapter(BasePlatformAdapter):
    """BOSS直聘平台适配器

    使用 undetected_chromedriver 进行浏览器自动化，
    有效绕过 BOSS 直聘的反爬检测（history.back, location.reload 等）。
    """

    platform = Platform.BOSS

    # 平台配置
    BASE_URL = "https://www.zhipin.com"
    LOGIN_URL = "https://www.zhipin.com/web/user/?ka=header-login"
    SEARCH_URL = "https://www.zhipin.com/web/geek/jobs"

    # API endpoints
    JOBLIST_API = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
    JOB_DETAIL_API = "/wapi/zpgeek/job/detail.json"

    # 登录状态检查选择器
    LOGIN_INDICATOR = "//li[@class='nav-figure']"

    # 职位列表选择器
    JOB_CARD_SELECTOR = "//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]"

    def __init__(
        self,
        uc_driver_manager: Optional[UCDriverManager] = None,
        cookie_manager: Optional[CookieManager] = None,
    ):
        super().__init__()
        self.uc_driver = uc_driver_manager or get_uc_driver_manager()
        self.cookie_manager = cookie_manager or get_cookie_manager()
        self.human_sim = HumanSimulator()
        self._logged_in = False

    @property
    def name(self) -> str:
        return "BOSS直聘"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def _ensure_browser_started(self) -> None:
        """确保浏览器已启动"""
        await self.uc_driver.start()

    async def login(self, username: str, password: str) -> bool:
        """登录BOSS直聘

        使用 undetected_chromedriver 启动浏览器，
        用户手动完成登录后自动保存 Cookie。
        """
        try:
            await self._ensure_browser_started()

            logger.info(f"Navigating to login page: {self.LOGIN_URL}")
            await self.uc_driver.get(self.LOGIN_URL)

            logger.info("=" * 50)
            logger.info("请在打开的浏览器窗口中完成登录：")
            logger.info("  1. 输入手机号获取验证码")
            logger.info("  2. 完成登录后系统会自动保存 Cookie")
            logger.info("=" * 50)

            # 等待用户手动登录（最多等待5分钟）
            for i in range(150):
                await asyncio.sleep(2)

                try:
                    # 检查登录指示器
                    avatar = await self.uc_driver.find_element("xpath", self.LOGIN_INDICATOR)
                    if avatar:
                        self._logged_in = True
                        # 保存 cookies
                        cookies = await self.uc_driver.get_cookies()
                        if cookies:
                            cookie_dict = {c['name']: c['value'] for c in cookies}
                            # 保存到文件
                            cookie_file = Path("./cookies/boss_cookies.json")
                            cookie_file.parent.mkdir(parents=True, exist_ok=True)
                            with open(cookie_file, "w", encoding="utf-8") as f:
                                json.dump({
                                    "cookies": cookies,
                                    "saved_at": datetime.now().isoformat(),
                                    "platform": "boss",
                                }, f, ensure_ascii=False, indent=2)
                            logger.info(f"Login successful, {len(cookies)} cookies saved")
                        return True

                    # 检查 URL 变化
                    current_url = self.uc_driver._driver.current_url
                    if "zhipin.com/web/geek" in current_url or (
                        "zhipin.com" in current_url and "user" not in current_url
                    ):
                        avatar = await self.uc_driver.find_element("xpath", self.LOGIN_INDICATOR)
                        if avatar:
                            self._logged_in = True
                            cookies = await self.uc_driver.get_cookies()
                            if cookies:
                                cookie_file = Path("./cookies/boss_cookies.json")
                                cookie_file.parent.mkdir(parents=True, exist_ok=True)
                                with open(cookie_file, "w", encoding="utf-8") as f:
                                    json.dump({
                                        "cookies": cookies,
                                        "saved_at": datetime.now().isoformat(),
                                        "platform": "boss",
                                    }, f, ensure_ascii=False, indent=2)
                                logger.info(f"Login successful (URL change), {len(cookies)} cookies saved")
                            return True

                except Exception:
                    pass

                if i > 0 and i % 15 == 0:
                    logger.info(f"等待登录中... ({i * 2}秒)")

            logger.error("Login timeout")
            return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def check_login_status(self) -> bool:
        """检查登录状态 - 优先使用 API 方式"""
        # 先尝试 API 检查
        try:
            cookies = await self._load_cookies_from_file()
            if cookies:
                headers = {
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
                }
                async with httpx.AsyncClient(http2=False, trust_env=False, timeout=10.0) as client:
                    response = await client.get(
                        "https://www.zhipin.com/wapi/zpgeek/user/info.json",
                        headers=headers,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("code") == 0:
                            return True
        except Exception as e:
            logger.debug(f"API login check failed: {e}")

        # 降级到浏览器检查
        try:
            await self._ensure_browser_started()
            await self.uc_driver.get(self.BASE_URL)
            await asyncio.sleep(1)
            avatar = await self.uc_driver.find_element("xpath", self.LOGIN_INDICATOR)
            return avatar is not None
        except Exception as e:
            logger.debug(f"Check login status error: {e}")
            return False

    async def _load_cookies_from_file(self) -> Dict[str, str]:
        """从文件加载 cookies"""
        cookie_file = Path("./cookies/boss_cookies.json")
        if not cookie_file.exists():
            return {}

        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cookies = data.get("cookies", [])
            return {c['name']: c['value'] for c in cookies if 'name' in c and 'value' in c}
        except Exception:
            return {}

    async def _load_cookies_to_browser(self) -> None:
        """加载 cookies 到浏览器"""
        cookie_file = Path("./cookies/boss_cookies.json")
        if not cookie_file.exists():
            return

        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cookies = data.get("cookies", [])
            if cookies:
                await self.uc_driver.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies to browser")
        except Exception as e:
            logger.debug(f"Load cookies to browser error: {e}")

    async def search_jobs(
        self,
        keywords: str,
        city: Optional[str] = None,
        salary_range: Optional[tuple] = None,
        experience: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResult:
        """搜索职位 - 使用 undetected_chromedriver"""
        try:
            await self._ensure_browser_started()
            await self._load_cookies_to_browser()

            # 构建搜索 URL
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

            import random
            await asyncio.sleep(random.uniform(2, 4))

            # 导航到搜索页
            await self.uc_driver.get(url)
            await asyncio.sleep(3)

            # 等待职位列表出现
            try:
                await self.uc_driver.find_element("xpath", "//ul[contains(@class, 'rec-job-list')]")
            except Exception:
                logger.warning("Job list did not load")
                return SearchResult(jobs=[], total_count=0, page=page, page_size=page_size, has_more=False)

            # 滚动到底部，触发懒加载
            await self._scroll_to_load_all_jobs()

            # 获取所有职位卡片
            job_cards = await self.uc_driver.find_elements("xpath", self.JOB_CARD_SELECTOR)

            if not job_cards:
                logger.warning("No job cards found")
                return SearchResult(jobs=[], total_count=0, page=page, page_size=page_size, has_more=False)

            logger.info(f"Found {len(job_cards)} job cards on page {page}")

            # 解析职位信息
            jobs = await self._parse_job_cards(job_cards)

            return SearchResult(
                jobs=jobs,
                total_count=len(jobs),
                page=page,
                page_size=page_size,
                has_more=len(job_cards) >= page_size,
            )

        except Exception as e:
            logger.error(f"Search jobs failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return SearchResult(error=str(e))

    async def _scroll_to_load_all_jobs(self, max_iterations: int = 50) -> None:
        """滚动到底部加载所有职位"""
        last_count = -1
        stable_tries = 0

        for i in range(max_iterations):
            # 检查是否到达底部
            try:
                footer = await self.uc_driver.find_element("xpath", "div#footer, #footer")
                if footer:
                    break
            except Exception:
                pass

            # 滚动
            await self.uc_driver.execute_script("window.scrollBy(0, Math.floor(window.innerHeight * 1.5))")
            await asyncio.sleep(0.5)

            # 检查卡片数量变化
            cards = await self.uc_driver.find_elements("xpath", self.JOB_CARD_SELECTOR)
            current_count = len(cards)

            if current_count == last_count:
                stable_tries += 1
            else:
                stable_tries = 0

            last_count = current_count

            if stable_tries >= 3:
                await self.uc_driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

        logger.info(f"Loaded {last_count} jobs after scrolling")

    async def _parse_job_cards(self, job_cards: list) -> List[JobInfo]:
        """解析职位卡片列表"""
        jobs = []

        for card in job_cards[:20]:  # 限制每页最多20个
            try:
                job = await self._parse_single_job_card(card)
                if job and job.title:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Parse job card error: {e}")
                continue

        return jobs

    async def _parse_single_job_card(self, card) -> Optional[JobInfo]:
        """解析单个职位卡片"""
        try:
            # 使用 card 对象的 find_element 方法
            # 注意：Selenium 的 WebElement 没有 query_selector，需要用 find_element

            # 提取职位标题
            try:
                title_el = card.find_element("xpath", ".//a[contains(@class, 'job-name')]")
                title = title_el.text.strip()
                href = title_el.get_attribute("href") or ""
            except Exception:
                title = ""
                href = ""

            if not title:
                return None

            job_id = self._extract_job_id(href)

            # 提取薪资
            salary_text = ""
            try:
                salary_el = card.find_element("xpath", ".//span[contains(@class, 'job-salary')]")
                raw_salary = salary_el.text
                salary_text = self._decode_salary(raw_salary)
            except Exception:
                pass

            # 提取公司名称
            company = ""
            try:
                company_el = card.find_element("xpath", ".//span[contains(@class, 'company-name')]")
                company = company_el.text.strip()
            except Exception:
                try:
                    company_el = card.find_element("xpath", ".//span[contains(@class, 'boss-name')]")
                    company = company_el.text.strip()
                except Exception:
                    pass

            # 提取城市
            city = ""
            try:
                city_el = card.find_element("xpath", ".//span[contains(@class, 'company-location')]")
                city = city_el.text.strip().split("·")[0]
            except Exception:
                pass

            # 提取标签
            tags = []
            try:
                tag_els = card.find_elements("xpath", ".//ul[contains(@class, 'tag-list')]//li")
                for tag in tag_els[:5]:
                    text = tag.text.strip()
                    if text:
                        tags.append(text)
            except Exception:
                pass

            salary_min, salary_max = self._parse_salary(salary_text)

            return JobInfo(
                id=job_id,
                title=title,
                company=company,
                salary=salary_text.strip(),
                salary_min=salary_min,
                salary_max=salary_max,
                city=city,
                description=" ".join(tags),
                url=f"{self.BASE_URL}{href}" if href else None,
                platform="boss",
            )
        except Exception as e:
            logger.debug(f"Parse single job card error: {e}")
            return None

    async def get_job_detail(self, job_id: str) -> Optional[JobInfo]:
        """获取职位详情"""
        try:
            await self._ensure_browser_started()
            await self._load_cookies_to_browser()

            url = f"{self.BASE_URL}/web/geek/job?query=&page=1&ka=job-{job_id}"
            await self.uc_driver.get(url)
            await asyncio.sleep(2)

            # 简单解析
            title = await self.uc_driver.get_text("xpath", "//h1")
            salary = await self.uc_driver.get_text("xpath", "//span[contains(@class, 'salary')]")
            company = await self.uc_driver.get_text("xpath", "//span[contains(@class, 'company-name')]")
            city = await self.uc_driver.get_text("xpath", "//span[contains(@class, 'area')]")
            experience = await self.uc_driver.get_text("xpath", "//span[contains(@class, 'experience')]")
            description = await self.uc_driver.get_text("xpath", "//div[contains(@class, 'detail-content')]")

            salary_min, salary_max = self._parse_salary(salary or "")

            return JobInfo(
                id=job_id,
                title=(title or "").strip(),
                company=(company or "").strip(),
                salary=(salary or "").strip(),
                salary_min=salary_min,
                salary_max=salary_max,
                city=(city or "").strip().split("·")[0],
                description=(description or "").strip(),
                experience_required=(experience or "").strip(),
                platform="boss",
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
            await self._ensure_browser_started()
            await self._load_cookies_to_browser()

            detail_url = f"{self.BASE_URL}/web/geek/job?query=&page=1&ka=job-{job_id}"

            # 使用 httpx API 获取职位详情，减少浏览器直接访问
            # 先通过 API 获取职位信息，确认职位存在
            try:
                cookies = await self._load_cookies_from_file()
                if cookies:
                    headers = {
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
                        "Referer": f"{self.BASE_URL}/web/geek/jobs",
                    }
                    async with httpx.AsyncClient(http2=False, trust_env=False, timeout=10.0) as client:
                        resp = await client.get(
                            f"{self.BASE_URL}/wapi/zpgeek/job/detail.json?jobId={job_id}",
                            headers=headers,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("code") != 0:
                                logger.warning(f"Job {job_id} not available via API: {data.get('zpData', {}).get('msg', '')}")
                                return ApplicationResult(
                                    success=False,
                                    job_id=job_id,
                                    error="职位已下架或不可投递",
                                )
            except Exception as e:
                logger.debug(f"API job detail check failed: {e}")

            # 导航到职位详情页
            await self.uc_driver.get(detail_url)
            await asyncio.sleep(3)  # 等待页面加载

            # 检查是否被反爬（页面回退或重定向）
            current_url = self.uc_driver._driver.current_url
            if "about:blank" in current_url or current_url == "data:," :
                logger.warning(f"Page blocked, got: {current_url}")
                return ApplicationResult(
                    success=False,
                    job_id=job_id,
                    error="页面被拦截",
                )

            # 检查是否仍在正确的页面
            if job_id not in current_url and "job" not in current_url:
                logger.warning(f"Redirected away from job page to: {current_url}")
                return ApplicationResult(
                    success=False,
                    job_id=job_id,
                    error="页面被重定向",
                )

            # 查找"立即沟通"按钮
            try:
                chat_btn = await self.uc_driver.find_element("xpath", "//a[contains(@class, 'op-btn-chat')]")
            except Exception:
                try:
                    chat_btn = await self.uc_driver.find_element("xpath", "//a[contains(@class, 'op-btn-start')]")
                except Exception:
                    chat_btn = None

            if chat_btn:
                # 模拟人类行为：先移动到按钮位置，稍等片刻再点击
                await self.uc_driver.execute_script("""
                    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                """, chat_btn)
                await asyncio.sleep(1.5)

                # 点击按钮
                chat_btn.click()
                await asyncio.sleep(3)  # 等待弹窗或页面反应

                # 检查是否有"交换微信"、"发送简历"等后续弹窗，关闭它们
                try:
                    close_btn = await self.uc_driver.find_element("xpath", "//button[contains(@class, 'close')] | //span[text()='关闭'] | //i[contains(@class, 'close')]")
                    if close_btn:
                        close_btn.click()
                        await asyncio.sleep(1)
                except Exception:
                    pass

                if greeting:
                    try:
                        input_el = await self.uc_driver.find_element("xpath", "//textarea[contains(@class, 'chat-input')]")
                        input_el.clear()
                        input_el.send_keys(greeting)
                        await asyncio.sleep(1.5)

                        send_btn = await self.uc_driver.find_element("xpath", "//button[contains(@class, 'send-btn')]")
                        send_btn.click()
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.debug(f"Send greeting failed: {e}")

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
            await self._ensure_browser_started()
            await self._load_cookies_to_browser()

            await self.uc_driver.get(f"{self.BASE_URL}/web/geek/chat")
            await asyncio.sleep(2)

            messages = []

            # 解析消息列表
            chat_items = await self.uc_driver.find_elements("xpath", "//div[contains(@class, 'chat-item')]")
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
        try:
            chat_id = item.get_attribute("data-geek") or item.get_attribute("data-id") or ""

            hr_name = "HR"
            try:
                name_el = item.find_element("xpath", ".//span[contains(@class, 'name')]")
                hr_name = name_el.text.strip()
            except Exception:
                pass

            company = ""
            try:
                company_el = item.find_element("xpath", ".//span[contains(@class, 'company-text') or contains(@class, 'company-name')]")
                company = company_el.text.strip()
            except Exception:
                pass

            content = ""
            try:
                msg_el = item.find_element("xpath", ".//span[contains(@class, 'msg-text') or contains(@class, 'msg')]")
                content = msg_el.text.strip()
            except Exception:
                pass

            time_text = ""
            try:
                time_el = item.find_element("xpath", ".//span[contains(@class, 'time')]")
                time_text = time_el.text.strip()
            except Exception:
                pass

            timestamp = self._parse_message_time(time_text)

            is_read = True
            try:
                unread_el = item.find_element("xpath", ".//span[contains(@class, 'unread')]")
                is_read = False
            except Exception:
                pass

            job_title = None
            try:
                job_el = item.find_element("xpath", ".//span[contains(@class, 'job-name')]")
                job_title = job_el.text.strip()
            except Exception:
                pass

            return Message(
                id=chat_id,
                hr_name=hr_name,
                company=company,
                content=content,
                timestamp=timestamp,
                is_read=is_read,
                job_title=job_title,
                platform="boss",
            )

        except Exception as e:
            logger.debug(f"Parse chat item error: {e}")
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
            time_part = time_text.replace("昨天", "").strip()
            try:
                hour, minute = time_part.split(":")
                yesterday = now.replace(day=now.day - 1)
                return yesterday.replace(hour=int(hour), minute=int(minute), second=0)
            except ValueError:
                return now.replace(day=now.day - 1)

        if "-" in time_text and ":" in time_text:
            try:
                date_part, time_part = time_text.split(" ")
                month, day = date_part.split("-")
                hour, minute = time_part.split(":")
                return now.replace(month=int(month), day=int(day), hour=int(hour), minute=int(minute), second=0)
            except ValueError:
                pass

        # MM-DD 格式（无时间）
        if "-" in time_text and ":" not in time_text and len(time_text) <= 5:
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
        """回复消息"""
        try:
            await self._ensure_browser_started()
            await self._load_cookies_to_browser()

            await self.uc_driver.get(f"{self.BASE_URL}/web/geek/chat")
            await asyncio.sleep(2)

            # 查找对应会话
            chat_item = None
            try:
                chat_item = await self.uc_driver.find_element("xpath", f'//div[contains(@class, "chat-item") and @data-geek="{message_id}"]')
            except Exception:
                try:
                    chat_item = await self.uc_driver.find_element("xpath", f'//div[contains(@class, "chat-item") and @data-id="{message_id}"]')
                except Exception:
                    pass

            if not chat_item:
                logger.warning(f"Chat item not found: {message_id}")
                return False

            chat_item.click()
            await asyncio.sleep(1)

            # 查找输入框
            input_el = None
            try:
                input_el = await self.uc_driver.find_element("xpath", "//textarea[contains(@class, 'chat-input')]")
            except Exception:
                try:
                    input_el = await self.uc_driver.find_element("xpath", "//textarea[@placeholder]")
                except Exception:
                    pass

            if not input_el:
                logger.error("Chat input not found")
                return False

            input_el.clear()
            input_el.send_keys(content)
            await asyncio.sleep(1)

            # 发送
            try:
                send_btn = await self.uc_driver.find_element("xpath", "//button[contains(@class, 'send-btn')]")
                send_btn.click()
            except Exception:
                input_el.send_keys("\n")  # Enter 发送

            await asyncio.sleep(1)
            logger.info(f"Message sent to {message_id}")
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
        """解码 BOSS 动态字体薪资"""
        if not text:
            return text

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

        decoded = self._decode_salary(salary_text)

        match = re.search(r"(\d+)-(\d+)K", decoded, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))

        match = re.search(r"(\d+)K以上", decoded, re.IGNORECASE)
        if match:
            return int(match.group(1)), 999

        match = re.search(r"(\d+)-(\d+)元/天", decoded)
        if match:
            return int(match.group(1)), int(match.group(2))

        return None, None

    def _get_salary_code(self, min_sal: int, max_sal: int) -> Optional[str]:
        """获取BOSS薪资代码"""
        salary_map = {
            (0, 3): "401",
            (3, 5): "402",
            (5, 10): "403",
            (10, 20): "404",
            (20, 30): "405",
            (30, 50): "406",
            (50, 999): "407",
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
