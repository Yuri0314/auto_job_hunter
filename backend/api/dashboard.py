"""仪表盘API"""

from fastapi import APIRouter
from datetime import datetime, timedelta

from backend.core.database import SessionLocal, Job, Application, UserProfile
from backend.adapters import Platform

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(user_id: int = 1):
    """获取仪表盘概览数据"""
    db = SessionLocal()
    try:
        # 今日投递数
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())

        today_applications = db.query(Application).filter(
            Application.created_at >= today_start
        ).count()

        # 平台登录状态
        platform_status = []
        for platform in [Platform.BOSS, Platform.LIEPIN]:
            platform_status.append({
                "platform": platform.value,
                "logged_in": False,  # 实际应检查Cookie
            })

        # 简历状态
        profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        has_resume = bool(profile and profile.resume_text)

        # 本周投递数
        week_start = today - timedelta(days=today.weekday())
        week_start_dt = datetime.combine(week_start, datetime.min.time())

        week_applications = db.query(Application).filter(
            Application.created_at >= week_start_dt
        ).count()

        # 最近投递
        recent_apps = db.query(Application).join(Job).order_by(
            Application.created_at.desc()
        ).limit(5).all()

        recent = []
        for app in recent_apps:
            recent.append({
                "id": app.id,
                "job_title": app.job.title if app.job else None,
                "company": app.job.company if app.job else None,
                "status": app.status.value if app.status else "pending",
                "created_at": app.created_at.isoformat() if app.created_at else None,
            })

        return {
            "today_applications": today_applications,
            "week_applications": week_applications,
            "platform_status": platform_status,
            "has_resume": has_resume,
            "recent_applications": recent,
        }

    finally:
        db.close()