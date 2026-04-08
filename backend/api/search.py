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

@router.get("/strategies")
async def list_strategies():
    """获取所有搜索策略"""
    service = get_strategy_service()
    strategies = service.get_all_strategies()
    return {"items": strategies, "total": len(strategies)}


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