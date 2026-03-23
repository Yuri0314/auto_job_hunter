"""人机交互模拟模块"""

import asyncio
import random
from typing import Optional, Tuple
from loguru import logger
from playwright.async_api import Page


class HumanSimulator:
    """模拟真实用户的交互行为"""

    def __init__(
        self,
        min_delay: float = 0.5,
        max_delay: float = 2.0,
        typing_speed: Tuple[float, float] = (0.05, 0.15),
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.typing_speed = typing_speed

    async def random_delay(self) -> None:
        """随机延迟"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def human_type(
        self,
        page: Page,
        selector: str,
        text: str,
        clear_first: bool = True
    ) -> None:
        """模拟人类打字输入

        Args:
            page: Playwright页面对象
            selector: 输入框选择器
            text: 要输入的文本
            clear_first: 是否先清空输入框
        """
        element = await page.wait_for_selector(selector)

        if clear_first:
            await element.click(click_count=3)
            await page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.1, 0.3))

        # 逐字符输入，带有随机延迟
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.uniform(*self.typing_speed))

        await self.random_delay()

    async def human_click(
        self,
        page: Page,
        selector: str,
        scroll_to_view: bool = True
    ) -> None:
        """模拟人类点击

        Args:
            page: Playwright页面对象
            selector: 点击目标选择器
            scroll_to_view: 是否滚动到可见位置
        """
        element = await page.wait_for_selector(selector)

        if scroll_to_view:
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.2, 0.5))

        # 随机移动到元素附近
        box = await element.bounding_box()
        if box:
            x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
            y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.05, 0.15))

        await element.click()
        await self.random_delay()

    async def human_scroll(
        self,
        page: Page,
        distance: int = 500,
        direction: str = "down"
    ) -> None:
        """模拟人类滚动

        Args:
            page: Playwright页面对象
            distance: 滚动距离（像素）
            direction: 滚动方向 (up/down)
        """
        delta = distance if direction == "down" else -distance
        steps = random.randint(5, 10)
        step_size = delta // steps

        for _ in range(steps):
            await page.mouse.wheel(0, step_size)
            await asyncio.sleep(random.uniform(0.05, 0.2))

        await self.random_delay()

    async def human_mouse_move(
        self,
        page: Page,
        target_x: float,
        target_y: float
    ) -> None:
        """模拟人类鼠标移动（贝塞尔曲线轨迹）

        Args:
            page: Playwright页面对象
            target_x: 目标X坐标
            target_y: 目标Y坐标
        """
        # 获取当前鼠标位置（简化处理，从屏幕中心开始）
        current_x = random.randint(400, 800)
        current_y = random.randint(200, 400)

        # 生成随机控制点，模拟人类鼠标轨迹
        steps = random.randint(10, 20)

        for i in range(steps):
            # 线性插值
            t = i / steps
            x = current_x + (target_x - current_x) * t
            y = current_y + (target_y - current_y) * t

            # 添加随机偏移
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)

            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))

    async def read_page_like_human(
        self,
        page: Page,
        min_time: float = 3.0,
        max_time: float = 8.0
    ) -> None:
        """模拟人类阅读页面的行为

        Args:
            page: Playwright页面对象
            min_time: 最小阅读时间
            max_time: 最大阅读时间
        """
        read_time = random.uniform(min_time, max_time)

        # 随机滚动
        scroll_times = random.randint(1, 3)
        for _ in range(scroll_times):
            await self.human_scroll(page)
            await asyncio.sleep(read_time / scroll_times)

    async def avoid_detection(self, page: Page) -> None:
        """执行反检测行为

        Args:
            page: Playwright页面对象
        """
        # 随机移动鼠标
        await page.mouse.move(
            random.randint(100, 1800),
            random.randint(100, 900)
        )

        # 随机滚动
        if random.random() > 0.7:
            await self.human_scroll(page, random.randint(100, 300))


class CaptchaSolver:
    """验证码处理（基础实现）"""

    @staticmethod
    async def detect_captcha(page: Page) -> Optional[str]:
        """检测页面是否存在验证码

        Args:
            page: Playwright页面对象

        Returns:
            验证码类型或None
        """
        # 检测滑块验证码
        slider = await page.query_selector(".slide-verify-slider")
        if slider:
            return "slider"

        # 检测点选验证码
        click_captcha = await page.query_selector(".click-captcha")
        if click_captcha:
            return "click"

        # 检测图形验证码
        image_captcha = await page.query_selector("img[src*='captcha']")
        if image_captcha:
            return "image"

        return None

    async def solve_slider_captcha(self, page: Page) -> bool:
        """处理滑块验证码（基础实现，需要配合第三方服务）

        Args:
            page: Playwright页面对象
        """
        logger.warning("Slider captcha detected, manual intervention may be required")
        # TODO: 集成第三方验证码服务
        return False

    async def solve_click_captcha(self, page: Page) -> bool:
        """处理点选验证码

        Args:
            page: Playwright页面对象
        """
        logger.warning("Click captcha detected, manual intervention may be required")
        # TODO: 集成第三方验证码服务
        return False