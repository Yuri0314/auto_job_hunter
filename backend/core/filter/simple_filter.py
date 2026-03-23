"""简单模式过滤器 - 基于规则的职位筛选"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class FilterConfig:
    """过滤器配置"""
    keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    salary_range: Optional[tuple] = None  # (min, max) in K
    cities: List[str] = field(default_factory=list)
    company_size_range: Optional[tuple] = None  # (min, max) employee count
    job_types: List[str] = field(default_factory=list)
    experience_range: Optional[tuple] = None  # (min, max) years

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterConfig":
        """从字典创建配置"""
        return cls(
            keywords=data.get("keywords", []),
            exclude_keywords=data.get("exclude_keywords", []),
            salary_range=tuple(data["salary_range"]) if data.get("salary_range") else None,
            cities=data.get("cities", []),
            company_size_range=tuple(data["company_size_range"]) if data.get("company_size_range") else None,
            job_types=data.get("job_types", []),
            experience_range=tuple(data["experience_range"]) if data.get("experience_range") else None,
        )


@dataclass
class JobInfo:
    """职位信息"""
    id: str
    title: str
    company: str
    salary: Optional[str] = None
    salary_min: Optional[int] = None  # K
    salary_max: Optional[int] = None  # K
    city: Optional[str] = None
    company_size: Optional[str] = None
    company_size_min: Optional[int] = None
    company_size_max: Optional[int] = None
    job_type: Optional[str] = None
    experience_required: Optional[str] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    description: Optional[str] = None
    hr_name: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobInfo":
        """从字典创建"""
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            company=data.get("company", ""),
            salary=data.get("salary"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            city=data.get("city"),
            company_size=data.get("company_size"),
            company_size_min=data.get("company_size_min"),
            company_size_max=data.get("company_size_max"),
            job_type=data.get("job_type"),
            experience_required=data.get("experience_required"),
            experience_min=data.get("experience_min"),
            experience_max=data.get("experience_max"),
            description=data.get("description"),
            hr_name=data.get("hr_name"),
            url=data.get("url"),
            platform=data.get("platform"),
        )


class SimpleFilter:
    """简单模式过滤器"""

    def __init__(self, config: FilterConfig):
        self.config = config

    def filter(self, job: JobInfo) -> tuple[bool, List[str]]:
        """过滤职位

        Returns:
            (是否通过, 原因列表)
        """
        reasons = []

        # 1. 关键词匹配
        if self.config.keywords:
            if not self._match_keywords(job):
                reasons.append("关键词不匹配")
                return False, reasons

        # 2. 排除关键词
        if self.config.exclude_keywords:
            if self._match_exclude_keywords(job):
                reasons.append("包含排除关键词")
                return False, reasons

        # 3. 薪资过滤
        if self.config.salary_range:
            if not self._match_salary(job):
                reasons.append("薪资不符合要求")
                return False, reasons

        # 4. 城市过滤
        if self.config.cities:
            if not self._match_city(job):
                reasons.append("城市不符合要求")
                return False, reasons

        # 5. 公司规模过滤
        if self.config.company_size_range:
            if not self._match_company_size(job):
                reasons.append("公司规模不符合要求")
                return False, reasons

        # 6. 职位类型过滤
        if self.config.job_types:
            if not self._match_job_type(job):
                reasons.append("职位类型不符合要求")
                return False, reasons

        # 7. 经验要求过滤
        if self.config.experience_range:
            if not self._match_experience(job):
                reasons.append("经验要求不符合")
                return False, reasons

        reasons.append("符合所有条件")
        return True, reasons

    def _match_keywords(self, job: JobInfo) -> bool:
        """检查关键词匹配"""
        text_to_check = f"{job.title} {job.description or ''}".lower()

        for keyword in self.config.keywords:
            if keyword.lower() in text_to_check:
                return True

        return False

    def _match_exclude_keywords(self, job: JobInfo) -> bool:
        """检查排除关键词"""
        text_to_check = f"{job.title} {job.description or ''} {job.company}".lower()

        for keyword in self.config.exclude_keywords:
            if keyword.lower() in text_to_check:
                return True

        return False

    def _match_salary(self, job: JobInfo) -> bool:
        """检查薪资匹配"""
        min_salary, max_salary = self.config.salary_range

        # 如果职位没有薪资信息，默认通过
        if job.salary_min is None and job.salary_max is None:
            return True

        # 检查薪资范围是否有交集
        job_min = job.salary_min or 0
        job_max = job.salary_max or 999

        # 用户期望范围与职位范围有交集即通过
        return not (job_max < min_salary or job_min > max_salary)

    def _match_city(self, job: JobInfo) -> bool:
        """检查城市匹配"""
        if not job.city:
            return True

        job_city_lower = job.city.lower().replace("市", "")

        for city in self.config.cities:
            city_lower = city.lower().replace("市", "")
            if city_lower in job_city_lower or job_city_lower in city_lower:
                return True

        return False

    def _match_company_size(self, job: JobInfo) -> bool:
        """检查公司规模匹配"""
        min_size, max_size = self.config.company_size_range

        if job.company_size_min is None and job.company_size_max is None:
            return True

        job_min = job.company_size_min or 0
        job_max = job.company_size_max or 999999

        return not (job_max < min_size or job_min > max_size)

    def _match_job_type(self, job: JobInfo) -> bool:
        """检查职位类型匹配"""
        if not job.job_type:
            return True

        return job.job_type in self.config.job_types

    def _match_experience(self, job: JobInfo) -> bool:
        """检查经验要求匹配"""
        min_exp, max_exp = self.config.experience_range

        if job.experience_min is None and job.experience_max is None:
            return True

        job_min = job.experience_min or 0
        job_max = job.experience_max or 99

        return not (job_max < min_exp or job_min > max_exp)


class SimpleModeService:
    """简单模式服务"""

    def __init__(self, config: Optional[FilterConfig] = None):
        self.config = config or FilterConfig()
        self.filter = SimpleFilter(self.config)

    def update_config(self, config: FilterConfig) -> None:
        """更新配置"""
        self.config = config
        self.filter = SimpleFilter(config)

    def filter_job(self, job: JobInfo) -> tuple[bool, List[str]]:
        """过滤单个职位"""
        return self.filter.filter(job)

    def filter_jobs(self, jobs: List[JobInfo]) -> List[tuple[JobInfo, bool, List[str]]]:
        """批量过滤职位"""
        results = []
        for job in jobs:
            passed, reasons = self.filter_job(job)
            results.append((job, passed, reasons))

            if passed:
                logger.info(f"Job passed: {job.title} at {job.company}")
            else:
                logger.debug(f"Job filtered: {job.title} at {job.company} - {reasons}")

        return results

    def get_passing_jobs(self, jobs: List[JobInfo]) -> List[JobInfo]:
        """获取通过过滤的职位"""
        results = self.filter_jobs(jobs)
        return [job for job, passed, _ in results if passed]