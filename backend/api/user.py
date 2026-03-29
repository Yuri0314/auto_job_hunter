"""用户配置相关API"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.core.database import UserProfile, get_db


router = APIRouter()


class UserProfileResponse(BaseModel):
    """用户画像响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    target_positions: Optional[List[str]] = None
    target_cities: Optional[List[str]] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    skills: Optional[List[str]] = None
    strategy: Optional[str] = None
    auto_reply_enabled: bool = False
    daily_application_limit: int = 50


class UserProfileUpdate(BaseModel):
    """用户画像更新请求"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    target_positions: Optional[List[str]] = None
    target_cities: Optional[List[str]] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    skills: Optional[List[str]] = None
    strategy: Optional[str] = None
    auto_reply_enabled: Optional[bool] = None
    daily_application_limit: Optional[int] = None


class ResumeUpdate(BaseModel):
    """简历更新请求"""
    resume_text: str


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """获取用户画像"""
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    if not profile:
        # 创建默认画像
        profile = UserProfile(id=user_id, name="默认用户")
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return UserProfileResponse(
        id=profile.id,
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        city=profile.city,
        experience_years=profile.experience_years,
        education=profile.education,
        school=profile.school,
        major=profile.major,
        target_positions=profile.target_positions,
        target_cities=profile.target_cities,
        expected_salary_min=profile.expected_salary_min,
        expected_salary_max=profile.expected_salary_max,
        skills=profile.skills,
        strategy=profile.strategy,
        auto_reply_enabled=profile.auto_reply_enabled or False,
        daily_application_limit=profile.daily_application_limit or 50,
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: UserProfileUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """更新用户画像"""
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    if not profile:
        profile = UserProfile(id=user_id)
        db.add(profile)

    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return UserProfileResponse(
        id=profile.id,
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        city=profile.city,
        experience_years=profile.experience_years,
        education=profile.education,
        school=profile.school,
        major=profile.major,
        target_positions=profile.target_positions,
        target_cities=profile.target_cities,
        expected_salary_min=profile.expected_salary_min,
        expected_salary_max=profile.expected_salary_max,
        skills=profile.skills,
        strategy=profile.strategy,
        auto_reply_enabled=profile.auto_reply_enabled or False,
        daily_application_limit=profile.daily_application_limit or 50,
    )


@router.get("/resume")
async def get_resume(
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """获取简历"""
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "resume_text": profile.resume_text,
        "resume_file": profile.resume_file,
    }


@router.put("/resume")
async def update_resume(
    request: ResumeUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """更新简历"""
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    if not profile:
        profile = UserProfile(id=user_id)
        db.add(profile)

    profile.resume_text = request.resume_text
    db.commit()

    return {"message": "Resume updated"}


@router.post("/resume/optimize")
async def optimize_resume(
    user_id: int = 1,
    target_position: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """使用AI优化简历"""
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    if not profile or not profile.resume_text:
        raise HTTPException(status_code=400, detail="No resume to optimize")

    # TODO: AI优化简历
    return {
        "message": "Resume optimization initiated",
        "original_length": len(profile.resume_text),
    }