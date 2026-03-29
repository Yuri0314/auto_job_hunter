"""数据模型单元测试"""

import pytest
from datetime import datetime

from backend.core.database import (
    SessionLocal,
    Resume,
    ResumeProfile,
    SearchStrategy,
    Job,
    Application,
    UserProfile,
    Base,
    engine,
)


@pytest.fixture(scope="function")
def db_session():
    """每个测试创建独立的数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestResumeModel:
    """Resume 模型测试"""

    def test_create_resume(self, db_session):
        """测试创建简历"""
        resume = Resume(
            user_id=1,
            name="我的简历.pdf",
            file_type="pdf",
            parse_engine="rule",
        )
        db_session.add(resume)
        db_session.commit()

        assert resume.id is not None
        assert resume.name == "我的简历.pdf"
        assert resume.is_primary == False
        assert resume.created_at is not None

    def test_resume_with_profile(self, db_session):
        """测试简历与画像关联"""
        resume = Resume(name="测试简历")
        db_session.add(resume)
        db_session.commit()

        profile = ResumeProfile(
            resume_id=resume.id,
            name="张三",
            phone="13800138000",
            skills=["Python", "Django"],
        )
        db_session.add(profile)
        db_session.commit()

        # 验证关联
        saved_resume = db_session.query(Resume).filter(
            Resume.id == resume.id
        ).first()
        assert saved_resume.profile is not None
        assert saved_resume.profile.name == "张三"
        assert saved_resume.profile.skills == ["Python", "Django"]

    def test_delete_resume_cascade_profile(self, db_session):
        """测试删除简历时级联删除画像"""
        resume = Resume(name="待删除简历")
        db_session.add(resume)
        db_session.commit()

        profile = ResumeProfile(resume_id=resume.id, name="测试")
        db_session.add(profile)
        db_session.commit()

        resume_id = resume.id
        db_session.delete(resume)
        db_session.commit()

        # 验证画像也被删除
        saved_profile = db_session.query(ResumeProfile).filter(
            ResumeProfile.resume_id == resume_id
        ).first()
        assert saved_profile is None


class TestSearchStrategyModel:
    """SearchStrategy 模型测试"""

    def test_create_search_strategy(self, db_session):
        """测试创建搜索策略"""
        resume = Resume(name="测试简历")
        db_session.add(resume)
        db_session.commit()

        strategy = SearchStrategy(
            resume_id=resume.id,
            primary_keywords=["Python后端", "Django开发"],
            variant_keywords=["FastAPI工程师"],
            cities=["北京", "上海"],
            salary_min=20,
            salary_max=40,
        )
        db_session.add(strategy)
        db_session.commit()

        assert strategy.id is not None
        assert len(strategy.primary_keywords) == 2
        assert strategy.is_active == True


class TestJobModelExtension:
    """Job 模型扩展字段测试"""

    def test_job_pool_status(self, db_session):
        """测试职位池状态字段"""
        job = Job(
            job_id="test_job_001",
            platform="boss",
            title="Python工程师",
            company="测试公司",
            pool_status="starred",
        )
        db_session.add(job)
        db_session.commit()

        saved_job = db_session.query(Job).filter(
            Job.job_id == "test_job_001"
        ).first()
        assert saved_job.pool_status == "starred"


class TestApplicationModelExtension:
    """Application 模型扩展字段测试"""

    def test_application_delivery_status(self, db_session):
        """测试投递状态字段"""
        app = Application(
            job_id=1,
            platform="boss",
            delivery_status="replied",
            greeting_used="您好，我对这个职位很感兴趣",
        )
        db_session.add(app)
        db_session.commit()

        saved_app = db_session.query(Application).filter(
            Application.id == app.id
        ).first()
        assert saved_app.delivery_status == "replied"
        assert saved_app.greeting_used is not None


class TestUserProfileExtension:
    """UserProfile 模型扩展字段测试"""

    def test_user_run_mode(self, db_session):
        """测试运行模式字段"""
        profile = UserProfile(
            id=999,
            name="测试用户",
            run_mode="ai_assisted",
        )
        db_session.add(profile)
        db_session.commit()

        saved_profile = db_session.query(UserProfile).filter(
            UserProfile.id == 999
        ).first()
        assert saved_profile.run_mode == "ai_assisted"