"""职位相关API"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.core.database import (
    Job,
    JobStatus,
    get_db,
)


router = APIRouter()


class JobResponse(BaseModel):
    """职位响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    platform: str
    title: str
    company: str
    salary: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    city: Optional[str] = None
    description: Optional[str] = None
    match_score: Optional[int] = None
    status: str
    applied_at: Optional[str] = None


class JobListResponse(BaseModel):
    """职位列表响应"""
    total: int
    items: List[JobResponse]


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = Query(None, description="按状态过滤"),
    platform: Optional[str] = Query(None, description="按平台过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """获取职位列表"""
    query = db.query(Job)

    if status:
        try:
            status_enum = JobStatus(status)
            query = query.filter(Job.status == status_enum)
        except ValueError:
            pass

    if platform:
        query = query.filter(Job.platform == platform)

    if keyword:
        query = query.filter(
            (Job.title.contains(keyword)) |
            (Job.company.contains(keyword))
        )

    total = query.count()
    items = query.order_by(Job.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return JobListResponse(
        total=total,
        items=[
            JobResponse(
                id=item.id,
                job_id=item.job_id,
                platform=item.platform,
                title=item.title,
                company=item.company,
                salary=item.salary,
                salary_min=item.salary_min,
                salary_max=item.salary_max,
                city=item.city,
                description=item.description,
                match_score=item.match_score,
                status=item.status.value,
                applied_at=item.applied_at.isoformat() if item.applied_at else None,
            )
            for item in items
        ],
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """获取职位详情"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=job.id,
        job_id=job.job_id,
        platform=job.platform,
        title=job.title,
        company=job.company,
        salary=job.salary,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        city=job.city,
        description=job.description,
        match_score=job.match_score,
        status=job.status.value,
        applied_at=job.applied_at.isoformat() if job.applied_at else None,
    )


@router.post("/{job_id}/apply")
async def apply_job(
    job_id: int,
    greeting: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """手动投递职位"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # TODO: 实际投递逻辑
    return {"message": "Application submitted", "job_id": job_id}


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """删除职位"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()

    return {"message": "Job deleted"}