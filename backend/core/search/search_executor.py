"""多关键词并行搜索执行器"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from backend.adapters import Platform, get_adapter, SearchResult
from backend.adapters.base_adapter import JobInfo
from backend.core.database import SessionLocal, Job, JobStatus
from backend.core.search.strategy_service import get_strategy_service


class SearchExecutor:
    """多关键词并行搜索执行器"""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self._adapters: Dict[Platform, Any] = {}

    def get_adapter(self, platform: Platform):
        """获取平台适配器"""
        if platform not in self._adapters:
            self._adapters[platform] = get_adapter(platform)
        return self._adapters[platform]

    async def search_with_strategy(
        self,
        strategy_id: int,
        platforms: List[str] = None,
        max_pages: int = 2,
        delay: float = 2.0,
    ) -> Dict[str, Any]:
        """使用搜索策略执行搜索

        Args:
            strategy_id: 策略ID
            platforms: 平台列表，如 ["boss", "liepin"]
            max_pages: 每个关键词最大搜索页数
            delay: 请求间隔（秒）

        Returns:
            搜索结果统计
        """
        strategy_service = get_strategy_service()
        strategy = strategy_service.get_strategy(strategy_id)

        if not strategy:
            logger.error(f"策略不存在: {strategy_id}")
            return {
                "success": False,
                "error": f"策略不存在: {strategy_id}",
                "total_jobs": 0,
                "jobs": [],
            }

        # 获取所有关键词
        keywords = strategy_service.get_all_keywords(strategy_id)
        if not keywords:
            logger.warning(f"策略 {strategy_id} 没有关键词")
            return {
                "success": False,
                "error": "策略没有关键词",
                "total_jobs": 0,
                "jobs": [],
            }

        # 解析平台
        platform_enums = self._parse_platforms(platforms)
        if not platform_enums:
            logger.error("没有有效的平台")
            return {
                "success": False,
                "error": "没有有效的平台",
                "total_jobs": 0,
                "jobs": [],
            }

        # 获取搜索条件
        cities = strategy.get("cities", [])
        city = cities[0] if cities else None
        salary_range = None
        if strategy.get("salary_min") and strategy.get("salary_max"):
            salary_range = (strategy["salary_min"], strategy["salary_max"])

        # 执行多关键词搜索
        result = await self.search_multi_keywords(
            keywords=keywords,
            platforms=[p.value for p in platform_enums],
            city=city,
            salary_range=salary_range,
            max_pages=max_pages,
            delay=delay,
        )

        # 添加策略信息
        result["strategy_id"] = strategy_id
        result["strategy_name"] = f"策略#{strategy_id}"

        return result

    async def search_multi_keywords(
        self,
        keywords: List[str],
        platforms: List[str] = None,
        city: str = None,
        salary_range: tuple = None,
        max_pages: int = 2,
        delay: float = 2.0,
    ) -> Dict[str, Any]:
        """多关键词并行搜索

        Args:
            keywords: 关键词列表
            platforms: 平台列表，如 ["boss", "liepin"]
            city: 城市
            salary_range: 薪资范围 (min, max) in K
            max_pages: 每个关键词最大搜索页数
            delay: 请求间隔（秒）

        Returns:
            搜索结果统计
        """
        start_time = datetime.now()
        logger.info(f"开始多关键词搜索: {keywords}")

        # 解析平台
        platform_enums = self._parse_platforms(platforms)
        if not platform_enums:
            return {
                "success": False,
                "error": "没有有效的平台",
                "total_jobs": 0,
                "jobs": [],
                "keywords": keywords,
            }

        # 创建搜索任务
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        for keyword in keywords:
            for platform in platform_enums:
                task = self._search_single_keyword(
                    platform=platform,
                    keyword=keyword,
                    city=city,
                    salary_range=salary_range,
                    max_pages=max_pages,
                    delay=delay,
                    semaphore=semaphore,
                )
                tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 聚合结果
        all_jobs = []
        errors = []
        stats = {
            "total_searches": len(tasks),
            "successful": 0,
            "failed": 0,
        }

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                stats["failed"] += 1
            elif isinstance(result, list):
                all_jobs.extend(result)
                stats["successful"] += 1
            else:
                errors.append(f"未知结果类型: {type(result)}")
                stats["failed"] += 1

        # 去重
        unique_jobs = self._deduplicate_jobs(all_jobs)

        # 保存到数据库
        saved_count = self._save_jobs_to_db(unique_jobs)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(
            f"搜索完成: 关键词={len(keywords)}, "
            f"原始职位={len(all_jobs)}, 去重后={len(unique_jobs)}, "
            f"保存={saved_count}, 耗时={duration:.2f}s"
        )

        return {
            "success": True,
            "total_jobs": len(unique_jobs),
            "saved_jobs": saved_count,
            "jobs": unique_jobs,
            "keywords": keywords,
            "platforms": [p.value for p in platform_enums],
            "stats": stats,
            "errors": errors if errors else None,
            "duration_seconds": duration,
        }

    async def _search_single_keyword(
        self,
        platform: Platform,
        keyword: str,
        city: str = None,
        salary_range: tuple = None,
        max_pages: int = 2,
        delay: float = 2.0,
        semaphore: asyncio.Semaphore = None,
    ) -> List[Dict[str, Any]]:
        """搜索单个关键词

        Args:
            platform: 平台枚举
            keyword: 搜索关键词
            city: 城市
            salary_range: 薪资范围
            max_pages: 最大页数
            delay: 请求间隔
            semaphore: 并发控制信号量

        Returns:
            职位列表
        """
        jobs = []

        async def _search():
            adapter = self.get_adapter(platform)
            logger.debug(f"开始搜索: {platform.value} - {keyword}")

            for page in range(1, max_pages + 1):
                try:
                    result: SearchResult = await adapter.search_jobs(
                        keywords=keyword,
                        city=city,
                        salary_range=salary_range,
                        page=page,
                        page_size=20,
                    )

                    if result.error:
                        logger.warning(
                            f"搜索错误: {platform.value} - {keyword} - 第{page}页: {result.error}"
                        )
                        break

                    for job in result.jobs:
                        jobs.append(self._job_to_dict(job))

                    logger.debug(
                        f"搜索结果: {platform.value} - {keyword} - "
                        f"第{page}页 - {len(result.jobs)}个职位"
                    )

                    if not result.has_more:
                        break

                    if page < max_pages:
                        await asyncio.sleep(delay)

                except Exception as e:
                    logger.error(
                        f"搜索异常: {platform.value} - {keyword} - 第{page}页: {e}"
                    )
                    break

            return jobs

        if semaphore:
            async with semaphore:
                return await _search()
        else:
            return await _search()

    def _job_to_dict(self, job: JobInfo) -> Dict[str, Any]:
        """JobInfo 转字典"""
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "salary": job.salary,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "city": job.city,
            "company_size": job.company_size,
            "company_size_min": job.company_size_min,
            "company_size_max": job.company_size_max,
            "job_type": job.job_type,
            "experience_required": job.experience_required,
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "description": job.description,
            "hr_name": job.hr_name,
            "url": job.url,
            "platform": job.platform,
        }

    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """职位去重

        基于 ID 或 公司+职位 去重
        """
        seen = set()
        unique_jobs = []

        for job in jobs:
            # 优先使用 ID
            job_id = job.get("id")
            if job_id:
                key = f"{job.get('platform', '')}_{job_id}"
            else:
                # 使用公司+职位作为key
                key = f"{job.get('company', '')}_{job.get('title', '')}"

            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    def _save_jobs_to_db(self, jobs: List[Dict[str, Any]]) -> int:
        """保存职位到数据库"""
        db = SessionLocal()
        saved_count = 0

        try:
            for job_data in jobs:
                # 检查是否已存在
                existing = (
                    db.query(Job)
                    .filter(Job.job_id == job_data.get("id"))
                    .first()
                )

                if existing:
                    continue

                # 创建新职位记录
                job = Job(
                    job_id=job_data.get("id"),
                    platform=job_data.get("platform"),
                    title=job_data.get("title"),
                    company=job_data.get("company"),
                    salary=job_data.get("salary"),
                    salary_min=job_data.get("salary_min"),
                    salary_max=job_data.get("salary_max"),
                    city=job_data.get("city"),
                    company_size=job_data.get("company_size"),
                    description=job_data.get("description"),
                    experience_required=job_data.get("experience_required"),
                    hr_name=job_data.get("hr_name"),
                    url=job_data.get("url"),
                    status=JobStatus.NEW,
                )
                db.add(job)
                saved_count += 1

            db.commit()
            logger.info(f"保存 {saved_count} 个新职位到数据库")

        except Exception as e:
            logger.error(f"保存职位失败: {e}")
            db.rollback()
        finally:
            db.close()

        return saved_count

    def _parse_platforms(self, platforms: List[str] = None) -> List[Platform]:
        """解析平台列表"""
        if not platforms:
            # 默认使用所有支持的平台
            return [Platform.BOSS, Platform.LIEPIN]

        platform_enums = []
        for p in platforms:
            try:
                platform_enums.append(Platform(p.lower()))
            except ValueError:
                logger.warning(f"不支持的平台: {p}")

        return platform_enums if platform_enums else [Platform.BOSS, Platform.LIEPIN]


# 单例
_search_executor: Optional[SearchExecutor] = None


def get_search_executor() -> SearchExecutor:
    """获取搜索执行器单例"""
    global _search_executor
    if _search_executor is None:
        _search_executor = SearchExecutor()
    return _search_executor