"""平台适配器基类"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backend.core.filter.simple_filter import JobInfo


class Platform(Enum):
    """支持的平台枚举"""
    BOSS = "boss"
    LIEPIN = "liepin"
    MAIMAI = "maimai"


@dataclass
class SearchResult:
    """搜索结果"""
    jobs: List[JobInfo] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    error: Optional[str] = None


@dataclass
class ApplicationResult:
    """投递结果"""
    success: bool
    job_id: str
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Message:
    """HR消息"""
    id: str
    hr_name: str
    company: str
    content: str
    timestamp: datetime
    is_read: bool = False
    job_title: Optional[str] = None
    platform: Optional[str] = None


class BasePlatformAdapter(ABC):
    """平台适配器基类"""

    platform: Platform = None

    def __init__(self):
        self._logged_in = False

    @property
    @abstractmethod
    def name(self) -> str:
        """平台名称"""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """平台基础URL"""
        pass

    @abstractmethod
    async def login(self, username: str, password: str) -> bool:
        """登录平台

        Args:
            username: 用户名/手机号
            password: 密码

        Returns:
            是否登录成功
        """
        pass

    @abstractmethod
    async def check_login_status(self) -> bool:
        """检查登录状态"""
        pass

    @abstractmethod
    async def search_jobs(
        self,
        keywords: str,
        city: Optional[str] = None,
        salary_range: Optional[tuple] = None,
        experience: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResult:
        """搜索职位

        Args:
            keywords: 搜索关键词
            city: 城市
            salary_range: 薪资范围 (min, max)
            experience: 经验要求
            page: 页码
            page_size: 每页数量

        Returns:
            SearchResult
        """
        pass

    @abstractmethod
    async def get_job_detail(self, job_id: str) -> Optional[JobInfo]:
        """获取职位详情

        Args:
            job_id: 职位ID

        Returns:
            JobInfo 或 None
        """
        pass

    @abstractmethod
    async def apply_job(
        self,
        job_id: str,
        greeting: Optional[str] = None,
        resume_id: Optional[str] = None,
    ) -> ApplicationResult:
        """投递职位

        Args:
            job_id: 职位ID
            greeting: 打招呼语
            resume_id: 简历ID（如果需要指定）

        Returns:
            ApplicationResult
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Message]:
        """获取HR消息列表

        Args:
            unread_only: 仅获取未读消息
            limit: 最大数量

        Returns:
            Message列表
        """
        pass

    @abstractmethod
    async def reply_message(
        self,
        message_id: str,
        content: str,
    ) -> bool:
        """回复消息

        Args:
            message_id: 消息ID
            content: 回复内容

        Returns:
            是否成功
        """
        pass

    async def batch_apply(
        self,
        jobs: List[JobInfo],
        greeting_template: Optional[str] = None,
        delay: float = 3.0,
    ) -> List[ApplicationResult]:
        """批量投递

        Args:
            jobs: 职位列表
            greeting_template: 打招呼语模板
            delay: 每次投递间隔（秒）

        Returns:
            ApplicationResult列表
        """
        import asyncio

        results = []
        for job in jobs:
            greeting = None
            if greeting_template:
                greeting = greeting_template.format(
                    company=job.company,
                    position=job.title,
                )

            result = await self.apply_job(job.id, greeting)
            results.append(result)

            await asyncio.sleep(delay)

        return results

    def is_logged_in(self) -> bool:
        """是否已登录"""
        return self._logged_in