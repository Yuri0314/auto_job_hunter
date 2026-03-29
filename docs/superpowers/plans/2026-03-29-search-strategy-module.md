# 搜索策略模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完善搜索策略模块，提供策略管理API、多关键词并行搜索执行、策略应用

**Architecture:** 搜索策略服务层 + 搜索执行器 + 策略管理API

**Tech Stack:** SQLAlchemy, FastAPI, asyncio

**依赖:** 计划1 (数据模型) + 计划2 (简历解析)

---

## Files Structure

```
backend/core/search/
├── __init__.py              # 新增: 模块导出
├── strategy_service.py      # 新增: 策略管理服务
├── search_executor.py       # 新增: 搜索执行器
└── aggregator.py            # 新增: 结果聚合器

backend/api/
└── search.py                # 新增: 搜索策略API

tests/unit/
└── test_search.py           # 新增: 搜索模块测试
```

---

## Task 1: 策略管理服务

**Files:**
- Create: `backend/core/search/__init__.py`
- Create: `backend/core/search/strategy_service.py`

- [ ] **Step 1: 创建搜索模块目录**

```bash
mkdir -p backend/core/search
```

- [ ] **Step 2: 创建策略管理服务**

创建 `backend/core/search/strategy_service.py`：

```python
"""搜索策略管理服务"""

from typing import Dict, Any, List, Optional
from loguru import logger

from backend.core.database import (
    SessionLocal,
    SearchStrategy,
    Resume,
    ResumeProfile,
)


class StrategyService:
    """搜索策略管理服务"""

    def get_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """获取搜索策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return None

            return self._to_dict(strategy)

        finally:
            db.close()

    def get_strategies_by_resume(self, resume_id: int) -> List[Dict[str, Any]]:
        """获取简历关联的所有搜索策略"""
        db = SessionLocal()
        try:
            strategies = db.query(SearchStrategy).filter(
                SearchStrategy.resume_id == resume_id
            ).order_by(SearchStrategy.priority.desc()).all()

            return [self._to_dict(s) for s in strategies]

        finally:
            db.close()

    def get_active_strategy(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """获取简历的激活策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.resume_id == resume_id,
                SearchStrategy.is_active == True,
            ).first()

            return self._to_dict(strategy) if strategy else None

        finally:
            db.close()

    def create_strategy(
        self,
        resume_id: int,
        primary_keywords: List[str],
        variant_keywords: List[str] = None,
        skill_combinations: List[str] = None,
        cities: List[str] = None,
        salary_min: int = None,
        salary_max: int = None,
        exclude_keywords: List[str] = None,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """创建搜索策略"""
        db = SessionLocal()
        try:
            strategy = SearchStrategy(
                resume_id=resume_id,
                primary_keywords=primary_keywords or [],
                variant_keywords=variant_keywords or [],
                skill_combinations=skill_combinations or [],
                cities=cities or [],
                salary_min=salary_min,
                salary_max=salary_max,
                exclude_keywords=exclude_keywords or [],
                priority=priority,
                is_active=True,
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)

            return self._to_dict(strategy)

        except Exception as e:
            logger.error(f"创建搜索策略失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def update_strategy(
        self,
        strategy_id: int,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """更新搜索策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return None

            # 可更新字段
            updatable = [
                "primary_keywords", "variant_keywords", "skill_combinations",
                "cities", "salary_min", "salary_max", "exclude_keywords",
                "priority", "is_active",
            ]

            for field in updatable:
                if field in kwargs:
                    setattr(strategy, field, kwargs[field])

            db.commit()
            return self._to_dict(strategy)

        except Exception as e:
            logger.error(f"更新搜索策略失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def delete_strategy(self, strategy_id: int) -> bool:
        """删除搜索策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return False

            db.delete(strategy)
            db.commit()
            return True

        finally:
            db.close()

    def set_active_strategy(self, strategy_id: int) -> bool:
        """设置激活策略（同一简历的其他策略设为非激活）"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return False

            # 取消同简历其他策略的激活状态
            db.query(SearchStrategy).filter(
                SearchStrategy.resume_id == strategy.resume_id,
                SearchStrategy.id != strategy_id,
            ).update({"is_active": False})

            # 激活当前策略
            strategy.is_active = True
            db.commit()

            return True

        except Exception as e:
            logger.error(f"设置激活策略失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_all_keywords(self, strategy_id: int) -> List[str]:
        """获取策略的所有关键词（用于搜索）"""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return []

        keywords = []
        keywords.extend(strategy.get("primary_keywords", []))
        keywords.extend(strategy.get("variant_keywords", []))
        keywords.extend(strategy.get("skill_combinations", []))

        # 去重
        seen = set()
        unique = []
        for k in keywords:
            if k and k not in seen:
                seen.add(k)
                unique.append(k)

        return unique

    def _to_dict(self, strategy: SearchStrategy) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": strategy.id,
            "resume_id": strategy.resume_id,
            "primary_keywords": strategy.primary_keywords or [],
            "variant_keywords": strategy.variant_keywords or [],
            "skill_combinations": strategy.skill_combinations or [],
            "cities": strategy.cities or [],
            "salary_min": strategy.salary_min,
            "salary_max": strategy.salary_max,
            "exclude_keywords": strategy.exclude_keywords or [],
            "priority": strategy.priority,
            "is_active": strategy.is_active,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
        }


# 单例
_strategy_service: Optional[StrategyService] = None


def get_strategy_service() -> StrategyService:
    """获取策略服务单例"""
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService()
    return _strategy_service
```

- [ ] **Step 3: 创建模块导出**

创建 `backend/core/search/__init__.py`：

```python
"""搜索模块"""

from .strategy_service import StrategyService, get_strategy_service

__all__ = [
    "StrategyService",
    "get_strategy_service",
]
```

- [ ] **Step 4: 验证策略服务**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.search import get_strategy_service
service = get_strategy_service()
print('StrategyService initialized')
"
```

- [ ] **Step 5: Commit**

```bash
git add backend/core/search/
git commit -m "feat: 添加搜索策略管理服务"
```

---

## Task 2: 搜索执行器

**Files:**
- Create: `backend/core/search/search_executor.py`

- [ ] **Step 1: 创建搜索执行器**

创建 `backend/core/search/search_executor.py`：

```python
"""多关键词并行搜索执行器"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from backend.adapters import Platform, get_adapter, SearchResult
from backend.core.database import SessionLocal, Job, JobStatus


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
        """
        使用搜索策略执行搜索

        Args:
            strategy_id: 搜索策略ID
            platforms: 平台列表
            max_pages: 每个关键词的最大页数
            delay: 请求间隔

        Returns:
            {
                "total_jobs": int,
                "jobs": List[JobInfo],
                "by_keyword": Dict[str, int],
                "by_platform": Dict[str, int],
            }
        """
        from backend.core.search import get_strategy_service

        strategy_service = get_strategy_service()
        strategy = strategy_service.get_strategy(strategy_id)

        if not strategy:
            return {"error": "搜索策略不存在", "total_jobs": 0, "jobs": []}

        keywords = strategy_service.get_all_keywords(strategy_id)
        cities = strategy.get("cities", [])
        city = cities[0] if cities else None

        return await self.search_multi_keywords(
            keywords=keywords,
            platforms=platforms,
            city=city,
            max_pages=max_pages,
            delay=delay,
        )

    async def search_multi_keywords(
        self,
        keywords: List[str],
        platforms: List[str] = None,
        city: str = None,
        salary_range: tuple = None,
        max_pages: int = 2,
        delay: float = 2.0,
    ) -> Dict[str, Any]:
        """
        多关键词并行搜索

        Args:
            keywords: 关键词列表
            platforms: 平台列表 (默认 ["boss"])
            city: 城市
            salary_range: 薪资范围
            max_pages: 每个关键词的最大页数
            delay: 请求间隔

        Returns:
            搜索结果
        """
        platforms = platforms or ["boss"]
        platform_enums = [Platform(p) for p in platforms]

        logger.info(f"开始多关键词搜索: {len(keywords)} 个关键词, 平台: {platforms}")

        all_jobs = []
        stats = {
            "by_keyword": {},
            "by_platform": {},
        }

        # 按关键词搜索
        for keyword in keywords:
            keyword_jobs = await self._search_single_keyword(
                keyword=keyword,
                platforms=platform_enums,
                city=city,
                salary_range=salary_range,
                max_pages=max_pages,
                delay=delay,
            )

            stats["by_keyword"][keyword] = len(keyword_jobs)
            all_jobs.extend(keyword_jobs)

            # 控制频率
            await asyncio.sleep(delay)

        # 去重
        unique_jobs = self._deduplicate_jobs(all_jobs)

        # 统计平台分布
        for job in unique_jobs:
            platform = job.get("platform", "unknown")
            stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1

        logger.info(f"搜索完成: 共找到 {len(unique_jobs)} 个职位 (去重前 {len(all_jobs)} 个)")

        return {
            "total_jobs": len(unique_jobs),
            "jobs": unique_jobs,
            "by_keyword": stats["by_keyword"],
            "by_platform": stats["by_platform"],
        }

    async def _search_single_keyword(
        self,
        keyword: str,
        platforms: List[Platform],
        city: str,
        salary_range: tuple,
        max_pages: int,
        delay: float,
    ) -> List[Dict[str, Any]]:
        """搜索单个关键词"""
        jobs = []

        for platform in platforms:
            try:
                adapter = self.get_adapter(platform)

                # 检查登录状态
                if not await adapter.check_login_status():
                    logger.warning(f"{platform.value} 未登录，跳过")
                    continue

                # 搜索
                for page in range(1, max_pages + 1):
                    result: SearchResult = await adapter.search_jobs(
                        keywords=keyword,
                        city=city,
                        salary_range=salary_range,
                        page=page,
                    )

                    if result.error:
                        logger.error(f"搜索失败 [{platform.value}][{keyword}]: {result.error}")
                        break

                    jobs.extend([self._job_to_dict(j) for j in result.jobs])

                    if not result.has_more:
                        break

                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"搜索异常 [{platform.value}][{keyword}]: {e}")

        return jobs

    def _job_to_dict(self, job) -> Dict[str, Any]:
        """JobInfo 转字典"""
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "salary": job.salary,
            "salary_min": getattr(job, "salary_min", None),
            "salary_max": getattr(job, "salary_max", None),
            "city": job.city,
            "description": getattr(job, "description", None),
            "hr_name": getattr(job, "hr_name", None),
            "url": getattr(job, "url", None),
            "platform": job.platform,
            "match_score": getattr(job, "match_score", None),
        }

    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """职位去重"""
        seen = set()
        unique = []

        for job in jobs:
            # 使用 职位ID 或 公司+职位 作为去重键
            key = job.get("id") or f"{job.get('company')}_{job.get('title')}"

            if key and key not in seen:
                seen.add(key)
                unique.append(job)

        return unique


# 单例
_search_executor: Optional[SearchExecutor] = None


def get_search_executor() -> SearchExecutor:
    """获取搜索执行器单例"""
    global _search_executor
    if _search_executor is None:
        _search_executor = SearchExecutor()
    return _search_executor
```

- [ ] **Step 2: 更新模块导出**

修改 `backend/core/search/__init__.py`：

```python
"""搜索模块"""

from .strategy_service import StrategyService, get_strategy_service
from .search_executor import SearchExecutor, get_search_executor

__all__ = [
    "StrategyService",
    "get_strategy_service",
    "SearchExecutor",
    "get_search_executor",
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/core/search/
git commit -m "feat: 添加多关键词并行搜索执行器"
```

---

## Task 3: 搜索策略API

**Files:**
- Create: `backend/api/search.py`

- [ ] **Step 1: 创建搜索策略API**

创建 `backend/api/search.py`：

```python
"""搜索策略API路由"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.core.search import (
    get_strategy_service,
    get_search_executor,
)
from loguru import logger


router = APIRouter()


# ========== Pydantic Models ==========

class CreateStrategyRequest(BaseModel):
    """创建搜索策略请求"""
    resume_id: int
    primary_keywords: List[str]
    variant_keywords: Optional[List[str]] = None
    skill_combinations: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    exclude_keywords: Optional[List[str]] = None
    priority: Optional[int] = 0


class UpdateStrategyRequest(BaseModel):
    """更新搜索策略请求"""
    primary_keywords: Optional[List[str]] = None
    variant_keywords: Optional[List[str]] = None
    skill_combinations: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    exclude_keywords: Optional[List[str]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class SearchRequest(BaseModel):
    """搜索请求"""
    strategy_id: Optional[int] = None
    keywords: Optional[List[str]] = None
    platforms: Optional[List[str]] = ["boss"]
    city: Optional[str] = None
    max_pages: Optional[int] = 2


# ========== 策略管理 API ==========

@router.get("/strategies/{strategy_id}")
async def get_strategy(strategy_id: int):
    """获取搜索策略"""
    service = get_strategy_service()
    strategy = service.get_strategy(strategy_id)

    if not strategy:
        raise HTTPException(404, "搜索策略不存在")

    return strategy


@router.get("/strategies/by-resume/{resume_id}")
async def get_strategies_by_resume(resume_id: int):
    """获取简历关联的所有搜索策略"""
    service = get_strategy_service()
    strategies = service.get_strategies_by_resume(resume_id)

    return {"items": strategies, "total": len(strategies)}


@router.post("/strategies")
async def create_strategy(request: CreateStrategyRequest):
    """创建搜索策略"""
    service = get_strategy_service()

    try:
        strategy = service.create_strategy(
            resume_id=request.resume_id,
            primary_keywords=request.primary_keywords,
            variant_keywords=request.variant_keywords,
            skill_combinations=request.skill_combinations,
            cities=request.cities,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
            exclude_keywords=request.exclude_keywords,
            priority=request.priority,
        )

        return {"success": True, "strategy": strategy}

    except Exception as e:
        logger.error(f"创建搜索策略失败: {e}")
        raise HTTPException(500, str(e))


@router.put("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    request: UpdateStrategyRequest,
):
    """更新搜索策略"""
    service = get_strategy_service()

    strategy = service.update_strategy(
        strategy_id=strategy_id,
        **request.dict(exclude_unset=True),
    )

    if not strategy:
        raise HTTPException(404, "搜索策略不存在")

    return {"success": True, "strategy": strategy}


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int):
    """删除搜索策略"""
    service = get_strategy_service()

    success = service.delete_strategy(strategy_id)

    if not success:
        raise HTTPException(404, "搜索策略不存在")

    return {"success": True, "message": "搜索策略已删除"}


@router.post("/strategies/{strategy_id}/activate")
async def activate_strategy(strategy_id: int):
    """激活搜索策略"""
    service = get_strategy_service()

    success = service.set_active_strategy(strategy_id)

    if not success:
        raise HTTPException(404, "搜索策略不存在")

    return {"success": True, "message": "搜索策略已激活"}


# ========== 搜索执行 API ==========

@router.post("/execute")
async def execute_search(request: SearchRequest):
    """
    执行搜索

    可以使用策略ID搜索，也可以直接传入关键词列表搜索
    """
    executor = get_search_executor()

    try:
        if request.strategy_id:
            # 使用策略搜索
            result = await executor.search_with_strategy(
                strategy_id=request.strategy_id,
                platforms=request.platforms,
                max_pages=request.max_pages,
            )
        elif request.keywords:
            # 使用关键词搜索
            result = await executor.search_multi_keywords(
                keywords=request.keywords,
                platforms=request.platforms,
                city=request.city,
                max_pages=request.max_pages,
            )
        else:
            raise HTTPException(400, "请提供策略ID或关键词列表")

        return result

    except Exception as e:
        logger.error(f"搜索执行失败: {e}")
        raise HTTPException(500, str(e))


@router.get("/keywords/{strategy_id}")
async def get_strategy_keywords(strategy_id: int):
    """获取策略的所有搜索关键词"""
    service = get_strategy_service()
    keywords = service.get_all_keywords(strategy_id)

    return {"keywords": keywords}
```

- [ ] **Step 2: 注册路由**

修改 `backend/api/routes.py`，添加搜索路由：

```python
from .search import router as search_router

api_router.include_router(search_router, prefix="/search", tags=["Search"])
```

- [ ] **Step 3: 测试API**

```bash
cd /d E:\Code\auto_job_hunter && python run.py web &
```

访问 http://localhost:8000/docs 验证新增API。

- [ ] **Step 4: Commit**

```bash
git add backend/api/search.py backend/api/routes.py
git commit -m "feat: 添加搜索策略管理API和搜索执行API"
```

---

## Verification

- [ ] **运行测试**

```bash
cd /d E:\Code\auto_job_hunter && pytest tests/unit/ -v
```

- [ ] **验证API**

```bash
curl -X GET "http://localhost:8000/api/search/strategies/by-resume/1"
```

---

## Summary

完成本计划后：

1. **策略管理服务**: 创建、更新、删除、激活搜索策略
2. **搜索执行器**: 多关键词并行搜索、去重、统计
3. **搜索策略API**: 完整的CRUD接口和搜索执行接口

这些功能为仪表盘的一键求职功能提供后端支持。