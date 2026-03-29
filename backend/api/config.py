"""过滤配置相关API"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.core.database import FilterRule, get_db


router = APIRouter()


class FilterRuleResponse(BaseModel):
    """过滤规则响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    salary_range: Optional[List[int]] = None
    cities: Optional[List[str]] = None
    company_size_range: Optional[List[int]] = None
    experience_range: Optional[List[int]] = None
    is_active: bool
    priority: int


class FilterRuleCreate(BaseModel):
    """创建过滤规则请求"""
    name: str
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    salary_range: Optional[List[int]] = None
    cities: Optional[List[str]] = None
    company_size_range: Optional[List[int]] = None
    experience_range: Optional[List[int]] = None
    priority: int = 0


class FilterRuleUpdate(BaseModel):
    """更新过滤规则请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    salary_range: Optional[List[int]] = None
    cities: Optional[List[str]] = None
    company_size_range: Optional[List[int]] = None
    experience_range: Optional[List[int]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


@router.get("/rules", response_model=List[FilterRuleResponse])
async def list_filter_rules(
    db: Session = Depends(get_db),
):
    """获取所有过滤规则"""
    rules = db.query(FilterRule).order_by(FilterRule.priority).all()

    return [
        FilterRuleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            keywords=r.keywords,
            exclude_keywords=r.exclude_keywords,
            salary_range=r.salary_range,
            cities=r.cities,
            company_size_range=r.company_size_range,
            experience_range=r.experience_range,
            is_active=r.is_active,
            priority=r.priority,
        )
        for r in rules
    ]


@router.post("/rules", response_model=FilterRuleResponse)
async def create_filter_rule(
    request: FilterRuleCreate,
    db: Session = Depends(get_db),
):
    """创建过滤规则"""
    rule = FilterRule(
        name=request.name,
        description=request.description,
        keywords=request.keywords,
        exclude_keywords=request.exclude_keywords,
        salary_range=request.salary_range,
        cities=request.cities,
        company_size_range=request.company_size_range,
        experience_range=request.experience_range,
        priority=request.priority,
        is_active=True,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return FilterRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        keywords=rule.keywords,
        exclude_keywords=rule.exclude_keywords,
        salary_range=rule.salary_range,
        cities=rule.cities,
        company_size_range=rule.company_size_range,
        experience_range=rule.experience_range,
        is_active=rule.is_active,
        priority=rule.priority,
    )


@router.put("/rules/{rule_id}", response_model=FilterRuleResponse)
async def update_filter_rule(
    rule_id: int,
    request: FilterRuleUpdate,
    db: Session = Depends(get_db),
):
    """更新过滤规则"""
    rule = db.query(FilterRule).filter(FilterRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)

    return FilterRuleResponse(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        keywords=rule.keywords,
        exclude_keywords=rule.exclude_keywords,
        salary_range=rule.salary_range,
        cities=rule.cities,
        company_size_range=rule.company_size_range,
        experience_range=rule.experience_range,
        is_active=rule.is_active,
        priority=rule.priority,
    )


@router.delete("/rules/{rule_id}")
async def delete_filter_rule(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """删除过滤规则"""
    rule = db.query(FilterRule).filter(FilterRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()

    return {"message": "Rule deleted"}


@router.post("/rules/{rule_id}/toggle")
async def toggle_filter_rule(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """启用/禁用过滤规则"""
    rule = db.query(FilterRule).filter(FilterRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.is_active = not rule.is_active
    db.commit()

    return {"message": f"Rule {'enabled' if rule.is_active else 'disabled'}"}