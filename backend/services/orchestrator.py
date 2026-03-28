"""主协调器服务 - 编排所有Agent"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from backend.core.database import (
    Job,
    Application,
    Message,
    UserProfile,
    FilterRule,
    JobStatus,
    ApplicationStatus,
    SessionLocal,
    init_db,
)
from backend.core.filter import SimpleModeService, FilterConfig, JobInfo
from backend.agents.ai import AIService, MatchResult, get_ai_service
from backend.adapters import (
    Platform,
    BasePlatformAdapter,
    BossAdapter,
    LiepinAdapter,
    get_adapter,
    SearchResult,
    ApplicationResult,
)


class Orchestrator:
    """主协调器 - 编排所有Agent"""

    def __init__(
        self,
        user_id: int = 1,
        use_ai: bool = False,
    ):
        self.user_id = user_id
        self.use_ai = use_ai

        self._adapters: Dict[Platform, BasePlatformAdapter] = {}
        self._simple_mode: Optional[SimpleModeService] = None
        self._ai_service: Optional[AIService] = None
        self._user_profile: Optional[UserProfile] = None
        self._running = False

    async def initialize(self) -> None:
        """初始化服务"""
        logger.info("Initializing orchestrator...")

        # 初始化数据库
        init_db()

        # 加载用户配置
        await self._load_user_profile()

        # 初始化简单模式过滤器
        await self._init_simple_mode()

        # 初始化AI服务（如果启用）
        if self.use_ai:
            self._ai_service = get_ai_service()

        logger.info("Orchestrator initialized successfully")

    async def _load_user_profile(self) -> None:
        """加载用户画像"""
        db = SessionLocal()
        try:
            self._user_profile = db.query(UserProfile).filter(
                UserProfile.id == self.user_id
            ).first()

            if not self._user_profile:
                # 创建默认用户画像
                self._user_profile = UserProfile(
                    id=self.user_id,
                    name="默认用户",
                    strategy="simple",
                )
                db.add(self._user_profile)
                db.commit()
                logger.info("Created default user profile")
        finally:
            db.close()

    async def _init_simple_mode(self) -> None:
        """初始化简单模式过滤"""
        db = SessionLocal()
        try:
            rules = db.query(FilterRule).filter(
                FilterRule.is_active == True
            ).order_by(FilterRule.priority).all()

            if rules:
                # 使用第一条规则
                rule = rules[0]
                config = FilterConfig(
                    keywords=rule.keywords or [],
                    exclude_keywords=rule.exclude_keywords or [],
                    salary_range=tuple(rule.salary_range) if rule.salary_range else None,
                    cities=rule.cities or [],
                    company_size_range=tuple(rule.company_size_range) if rule.company_size_range else None,
                    experience_range=tuple(rule.experience_range) if rule.experience_range else None,
                )
            else:
                # 默认配置
                config = FilterConfig()

            self._simple_mode = SimpleModeService(config)

        finally:
            db.close()

    def get_adapter(self, platform: Platform) -> BasePlatformAdapter:
        """获取平台适配器"""
        if platform not in self._adapters:
            self._adapters[platform] = get_adapter(platform)
        return self._adapters[platform]

    async def search_jobs(
        self,
        platforms: List[Platform],
        keywords: str,
        city: Optional[str] = None,
        salary_range: Optional[tuple] = None,
        max_pages: int = 3,
    ) -> List[JobInfo]:
        """搜索职位"""
        all_jobs = []

        for platform in platforms:
            try:
                logger.info(f"开始搜索 {platform.value} 平台...")
                adapter = self.get_adapter(platform)

                # 检查登录状态
                logged_in = await adapter.check_login_status()
                logger.info(f"{platform.value} 登录状态: {logged_in}")

                if not logged_in:
                    logger.warning(f"Not logged in to {platform.value}, skipping...")
                    continue

                # 搜索职位
                for page in range(1, max_pages + 1):
                    result: SearchResult = await adapter.search_jobs(
                        keywords=keywords,
                        city=city,
                        salary_range=salary_range,
                        page=page,
                    )

                    if result.error:
                        logger.error(f"Search error on {platform.value}: {result.error}")
                        break

                    all_jobs.extend(result.jobs)

                    if not result.has_more:
                        break

                    # 控制请求频率
                    await asyncio.sleep(3)

                logger.info(f"Found {len(all_jobs)} jobs from {platform.value}")

            except Exception as e:
                logger.error(f"Search jobs error on {platform.value}: {e}")

        return all_jobs

    async def filter_jobs(self, jobs: List[JobInfo]) -> List[JobInfo]:
        """过滤职位"""
        if self.use_ai and self._ai_service:
            return await self._ai_filter_jobs(jobs)
        else:
            return self._simple_filter_jobs(jobs)

    def _simple_filter_jobs(self, jobs: List[JobInfo]) -> List[JobInfo]:
        """简单模式过滤"""
        if not self._simple_mode:
            return jobs

        return self._simple_mode.get_passing_jobs(jobs)

    async def _ai_filter_jobs(self, jobs: List[JobInfo]) -> List[JobInfo]:
        """AI模式过滤"""
        passed_jobs = []
        min_score = 70  # 最低匹配分数

        resume = self._user_profile.resume_text if self._user_profile else ""

        for job in jobs:
            try:
                # 先进行简单过滤
                simple_passed, _ = self._simple_mode.filter_job(job) if self._simple_mode else (True, [])
                if not simple_passed:
                    continue

                # AI匹配分析
                if resume:
                    match_result = await self._ai_service.analyze_job_match(
                        resume=resume,
                        job_description=f"{job.title}\n{job.description or ''}",
                    )

                    if match_result.total_score >= min_score:
                        job.match_score = match_result.total_score
                        passed_jobs.append(job)

                        # 保存到数据库
                        await self._save_job_with_match(job, match_result)
                else:
                    passed_jobs.append(job)

            except Exception as e:
                logger.error(f"AI filter error for job {job.id}: {e}")

        return passed_jobs

    async def _save_job_with_match(self, job: JobInfo, match_result: MatchResult) -> None:
        """保存职位和匹配结果"""
        db = SessionLocal()
        try:
            db_job = Job(
                job_id=job.id,
                platform=job.platform,
                title=job.title,
                company=job.company,
                salary=job.salary,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                city=job.city,
                description=job.description,
                hr_name=job.hr_name,
                url=job.url,
                match_score=match_result.total_score,
                match_points=match_result.match_points,
                gap_points=match_result.gap_points,
                status=JobStatus.NEW,
            )
            db.add(db_job)
            db.commit()
        except Exception as e:
            logger.error(f"Save job error: {e}")
            db.rollback()
        finally:
            db.close()

    async def apply_jobs(
        self,
        jobs: List[JobInfo],
        greeting_template: Optional[str] = None,
        delay: float = 5.0,
    ) -> List[ApplicationResult]:
        """投递职位"""
        results = []

        for job in jobs:
            try:
                platform = Platform(job.platform)
                adapter = self.get_adapter(platform)

                # 生成打招呼语
                greeting = None
                if self.use_ai and self._ai_service and greeting_template:
                    # AI生成个性化打招呼
                    greeting = await self._generate_greeting(job)
                elif greeting_template:
                    greeting = greeting_template.format(
                        company=job.company,
                        position=job.title,
                    )

                # 投递
                result = await adapter.apply_job(job.id, greeting)
                results.append(result)

                # 记录投递
                await self._record_application(job, result)

                # 控制投递频率
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Apply job error: {e}")
                results.append(ApplicationResult(
                    success=False,
                    job_id=job.id,
                    error=str(e),
                ))

        return results

    async def _generate_greeting(self, job: JobInfo) -> str:
        """生成个性化打招呼语"""
        if not self._ai_service or not self._user_profile:
            return f"您好，我对贵公司的{job.title}职位很感兴趣，期待您的回复。"

        try:
            match_result = MatchResult(
                total_score=job.match_score or 80,
                skill_score=80,
                experience_score=80,
                salary_score=80,
                career_score=80,
                match_points=[],
                gap_points=[],
                recommendation="",
            )

            greeting = await self._ai_service.generate_greeting(
                match_result=match_result,
                user_name=self._user_profile.name or "求职者",
                experience_years=self._user_profile.experience_years or 3,
                style="professional",
            )
            return greeting

        except Exception as e:
            logger.error(f"Generate greeting error: {e}")
            return f"您好，我对贵公司的{job.title}职位很感兴趣。"

    async def _record_application(self, job: JobInfo, result: ApplicationResult) -> None:
        """记录投递结果"""
        db = SessionLocal()
        try:
            # 查找或创建职位记录
            db_job = db.query(Job).filter(Job.job_id == job.id).first()
            if not db_job:
                db_job = Job(
                    job_id=job.id,
                    platform=job.platform,
                    title=job.title,
                    company=job.company,
                    status=JobStatus.APPLIED,
                )
                db.add(db_job)

            db_job.status = JobStatus.APPLIED
            db_job.applied_at = datetime.now()

            # 创建投递记录
            application = Application(
                job_id=db_job.id,
                platform=job.platform,
                status=ApplicationStatus.SUCCESS if result.success else ApplicationStatus.FAILED,
                error_message=result.error,
                submitted_at=datetime.now() if result.success else None,
            )
            db.add(application)
            db.commit()

        except Exception as e:
            logger.error(f"Record application error: {e}")
            db.rollback()
        finally:
            db.close()

    async def check_messages(self, platforms: List[Platform]) -> List[Message]:
        """检查新消息"""
        all_messages = []

        for platform in platforms:
            try:
                adapter = self.get_adapter(platform)

                if not await adapter.check_login_status():
                    continue

                messages = await adapter.get_messages(unread_only=True)
                all_messages.extend(messages)

            except Exception as e:
                logger.error(f"Check messages error on {platform.value}: {e}")

        return all_messages

    async def auto_reply(self, messages: List[Message]) -> None:
        """自动回复消息"""
        if not self.use_ai:
            logger.info("Auto reply requires AI mode")
            return

        for message in messages:
            try:
                # TODO: AI生成回复
                pass
            except Exception as e:
                logger.error(f"Auto reply error: {e}")

    async def run_job_search_cycle(
        self,
        platforms: List[Platform] = None,
        keywords: str = None,
        city: str = None,
        apply_filtered: bool = True,
    ) -> Dict[str, Any]:
        """运行一次完整的求职搜索周期"""
        platforms = platforms or [Platform.BOSS, Platform.LIEPIN]
        keywords = keywords or self._user_profile.target_positions[0] if self._user_profile else "Python"

        logger.info(f"Starting job search cycle: keywords={keywords}, platforms={[p.value for p in platforms]}")

        # 1. 搜索职位
        jobs = await self.search_jobs(
            platforms=platforms,
            keywords=keywords,
            city=city,
        )
        logger.info(f"Found {len(jobs)} jobs")

        # 2. 过滤职位
        filtered_jobs = await self.filter_jobs(jobs)
        logger.info(f"Filtered to {len(filtered_jobs)} jobs")

        # 3. 投递职位
        results = []
        if apply_filtered and filtered_jobs:
            results = await self.apply_jobs(filtered_jobs[:10])  # 限制每次投递数量
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Applied {success_count}/{len(results)} jobs successfully")

        return {
            "total_jobs": len(jobs),
            "filtered_jobs": len(filtered_jobs),
            "applied_jobs": len(results),
            "success_count": sum(1 for r in results if r.success),
        }

    async def start_scheduled(self, interval_minutes: int = 60) -> None:
        """启动定时任务"""
        self._running = True

        while self._running:
            try:
                await self.run_job_search_cycle()
            except Exception as e:
                logger.error(f"Scheduled task error: {e}")

            await asyncio.sleep(interval_minutes * 60)

    def stop(self) -> None:
        """停止运行"""
        self._running = False


# 全局协调器实例
_orchestrator: Optional[Orchestrator] = None


async def get_orchestrator(use_ai: bool = False) -> Orchestrator:
    """获取协调器单例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(use_ai=use_ai)
        await _orchestrator.initialize()
    return _orchestrator