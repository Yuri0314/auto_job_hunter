"""投递相关API"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from backend.core.database import (
    Application,
    ApplicationStatus,
    Job,
    JobStatus,
    get_db,
)


router = APIRouter()


class ApplicationResponse(BaseModel):
    """投递响应模型"""
    id: int
    job_id: int
    platform: str
    greeting: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    submitted_at: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """投递列表响应"""
    total: int
    items: List[ApplicationResponse]


class SearchSubmitRequest(BaseModel):
    """搜索投递请求"""
    keywords: str
    platforms: List[str] = ["boss", "liepin"]
    city: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    max_count: int = 20
    auto_apply: bool = False
    greeting_template: Optional[str] = None


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    status: Optional[str] = Query(None, description="按状态过滤"),
    platform: Optional[str] = Query(None, description="按平台过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取投递记录列表"""
    query = db.query(Application)

    if status:
        try:
            status_enum = ApplicationStatus(status)
            query = query.filter(Application.status == status_enum)
        except ValueError:
            pass

    if platform:
        query = query.filter(Application.platform == platform)

    total = query.count()
    items = query.order_by(Application.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ApplicationListResponse(
        total=total,
        items=[
            ApplicationResponse(
                id=item.id,
                job_id=item.job_id,
                platform=item.platform,
                greeting=item.greeting,
                status=item.status.value,
                error_message=item.error_message,
                submitted_at=item.submitted_at.isoformat() if item.submitted_at else None,
            )
            for item in items
        ],
    )


@router.post("/search-and-apply")
async def search_and_apply(
    request: SearchSubmitRequest,
    db: Session = Depends(get_db),
):
    """搜索并投递职位"""
    from backend.services import Orchestrator
    from backend.adapters import Platform
    from loguru import logger

    try:
        logger.info(f"收到搜索请求: keywords={request.keywords}, platforms={request.platforms}")

        # 转换平台
        platforms = [Platform(p) for p in request.platforms]
        logger.info(f"平台转换完成: {platforms}")

        # 创建新的 orchestrator 实例（不使用单例）
        orchestrator = Orchestrator(use_ai=False)
        await orchestrator.initialize()
        logger.info("Orchestrator初始化成功")

        # 搜索职位
        salary_range = None
        if request.salary_min and request.salary_max:
            salary_range = (request.salary_min, request.salary_max)

        logger.info(f"开始搜索职位...")
        jobs = await orchestrator.search_jobs(
            platforms=platforms,
            keywords=request.keywords,
            city=request.city,
            salary_range=salary_range,
        )
        logger.info(f"搜索完成，找到 {len(jobs)} 个职位")

        # Debug: 打印第一个job的字段
        if jobs:
            logger.info(f"第一个job: id={jobs[0].id}, title={jobs[0].title}, salary={jobs[0].salary}")

        # 过滤职位
        filtered_jobs = await orchestrator.filter_jobs(jobs)
        logger.info(f"过滤完成，剩余 {len(filtered_jobs)} 个职位")

        result = {
            "total_found": len(jobs),
            "filtered": len(filtered_jobs),
            "applied": 0,
            "jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "salary": j.salary,
                    "city": j.city,
                }
                for j in filtered_jobs[:request.max_count]
            ],
        }

        # 自动投递
        if request.auto_apply and filtered_jobs:
            apply_results = await orchestrator.apply_jobs(
                jobs=filtered_jobs[:request.max_count],
                greeting_template=request.greeting_template,
            )
            result["applied"] = sum(1 for r in apply_results if r.success)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{application_id}/retry")
async def retry_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    """重试失败的投递"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status != ApplicationStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed applications can be retried")

    # TODO: 实际重试逻辑
    application.status = ApplicationStatus.RETRY
    application.retry_count += 1
    db.commit()

    return {"message": "Retry initiated", "application_id": application_id}


@router.get("/statistics")
async def get_statistics(
    days: int = Query(7, description="统计天数"),
    db: Session = Depends(get_db),
):
    """获取投递统计"""
    from datetime import timedelta

    start_date = datetime.now() - timedelta(days=days)

    total = db.query(Application).filter(Application.created_at >= start_date).count()
    success = db.query(Application).filter(
        Application.created_at >= start_date,
        Application.status == ApplicationStatus.SUCCESS,
    ).count()
    failed = db.query(Application).filter(
        Application.created_at >= start_date,
        Application.status == ApplicationStatus.FAILED,
    ).count()

    # 按平台统计
    platforms = db.query(Application.platform, db.func.count(Application.id)).filter(
        Application.created_at >= start_date,
    ).group_by(Application.platform).all()

    return {
        "period_days": days,
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": round(success / total * 100, 2) if total > 0 else 0,
        "by_platform": {p: c for p, c in platforms},
    }