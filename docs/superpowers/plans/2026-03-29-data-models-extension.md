# 数据模型扩展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 扩展数据库模型，支持多简历管理、搜索策略存储、投递状态追踪

**Architecture:** 新增 Resume/ResumeProfile/SearchStrategy 模型，扩展现有 Job/Application/UserProfile 模型字段，保持向后兼容

**Tech Stack:** SQLAlchemy, Alembic (数据库迁移), FastAPI, Pydantic

---

## Files Structure

```
backend/core/database/
├── models.py              # 修改: 新增模型 + 扩展字段
├── migrations/            # 新增: Alembic迁移脚本
│   └── versions/
│       └── 001_add_resume_models.py
└── __init__.py            # 修改: 导出新模型

backend/api/
├── resume.py              # 修改: 调整API适配新模型
└── dashboard.py           # 新增: 仪表盘API

tests/unit/
└── test_models.py         # 新增: 模型单元测试
```

---

## Task 1: 新增 Resume 数据模型

**Files:**
- Modify: `backend/core/database/models.py`

- [ ] **Step 1: 定义 Resume 模型**

在 `models.py` 中 `UserProfile` 类之前添加：

```python
class Resume(Base):
    """简历表 - 支持多简历管理"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=1, comment="用户ID")
    name = Column(String(200), nullable=False, comment="简历名称")
    file_path = Column(String(500), comment="原始文件路径")
    file_type = Column(String(20), default="pdf", comment="文件类型: pdf/docx/md/txt/paste")
    parse_engine = Column(String(20), default="rule", comment="解析引擎: rule/ai")
    is_primary = Column(Boolean, default=False, comment="是否主简历")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    profile = relationship("ResumeProfile", back_populates="resume", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resume(id={self.id}, name={self.name})>"
```

- [ ] **Step 2: 定义 ResumeProfile 模型**

在 `Resume` 类之后添加：

```python
class ResumeProfile(Base):
    """简历解析结果表"""
    __tablename__ = "resume_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, comment="关联简历ID")

    # 基本信息
    name = Column(String(50), comment="姓名")
    phone = Column(String(20), comment="手机号")
    email = Column(String(100), comment="邮箱")
    gender = Column(String(10), comment="性别")
    age = Column(Integer, comment="年龄")

    # 职业信息
    experience_years = Column(Integer, comment="工作年限")
    current_position = Column(String(100), comment="当前职位")
    current_company = Column(String(200), comment="当前公司")

    # 求职意向
    target_positions = Column(JSON, comment="目标职位列表")
    preferred_cities = Column(JSON, comment="意向城市列表")
    salary_min = Column(Integer, comment="期望薪资下限(K)")
    salary_max = Column(Integer, comment="期望薪资上限(K)")

    # 技能与背景
    education = Column(String(50), comment="学历")
    school = Column(String(100), comment="学校")
    major = Column(String(100), comment="专业")
    skills = Column(JSON, comment="技能列表")
    work_experiences = Column(JSON, comment="工作经历列表")
    projects = Column(JSON, comment="项目经历列表")

    # AI生成建议
    ai_search_suggestions = Column(JSON, comment="AI生成的搜索建议")
    ai_match_summary = Column(Text, comment="AI匹配摘要")

    # 原始数据
    raw_text = Column(Text, comment="简历原始文本")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联
    resume = relationship("Resume", back_populates="profile")

    def __repr__(self):
        return f"<ResumeProfile(resume_id={self.resume_id}, name={self.name})>"
```

需要添加导入:
```python
from sqlalchemy.orm import relationship, foreign
from sqlalchemy import ForeignKey
```

- [ ] **Step 3: 定义 SearchStrategy 模型**

在 `ResumeProfile` 类之后添加：

```python
class SearchStrategy(Base):
    """搜索策略表"""
    __tablename__ = "search_strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), comment="关联简历ID")

    # 搜索关键词
    primary_keywords = Column(JSON, comment="核心关键词")
    variant_keywords = Column(JSON, comment="变体关键词")
    skill_combinations = Column(JSON, comment="技能组合关键词")

    # 搜索条件
    cities = Column(JSON, comment="目标城市")
    salary_min = Column(Integer, comment="薪资下限(K)")
    salary_max = Column(Integer, comment="薪资上限(K)")
    exclude_keywords = Column(JSON, comment="排除关键词")

    # 优先级与状态
    priority = Column(Integer, default=0, comment="优先级")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<SearchStrategy(id={self.id}, resume_id={self.resume_id})>"
```

- [ ] **Step 4: 扩展 Job 模型**

在 `Job` 类中添加新字段（在 `applied_at` 之后）：

```python
    # 职位池状态
    pool_status = Column(String(20), default="pending", comment="职位池状态: pending/starred/rejected/queued")
    starred_at = Column(DateTime, comment="收藏时间")

    # 匹配分析扩展
    match_details = Column(JSON, comment="匹配分析详情")
```

- [ ] **Step 5: 扩展 Application 模型**

在 `Application` 类中添加新字段（在 `submitted_at` 之后）：

```python
    # 投递状态追踪
    delivery_status = Column(String(20), default="submitted", comment="投递状态: submitted/read/replied/interview/rejected/expired")
    status_updated_at = Column(DateTime, comment="状态更新时间")
    greeting_used = Column(Text, comment="使用的打招呼语")
```

- [ ] **Step 6: 扩展 UserProfile 模型**

在 `UserProfile` 类中添加新字段（在 `strategy` 之后）：

```python
    # 运行模式
    run_mode = Column(String(20), default="manual", comment="运行模式: manual/ai_assisted/ai_full_auto")
    primary_resume_id = Column(Integer, comment="主简历ID")
```

- [ ] **Step 7: 更新 __init__.py 导出**

在 `backend/core/database/__init__.py` 中添加新模型的导出：

```python
from .models import (
    # ... existing imports ...
    Resume,
    ResumeProfile,
    SearchStrategy,
)

__all__ = [
    # ... existing exports ...
    "Resume",
    "ResumeProfile",
    "SearchStrategy",
]
```

- [ ] **Step 8: 验证模型定义**

运行Python检查语法：

```bash
cd /d E:\Code\auto_job_hunter && python -c "from backend.core.database import Resume, ResumeProfile, SearchStrategy; print('Models imported successfully')"
```

Expected: 输出 "Models imported successfully"

- [ ] **Step 9: Commit**

```bash
git add backend/core/database/models.py backend/core/database/__init__.py
git commit -m "feat: 新增 Resume/ResumeProfile/SearchStrategy 数据模型，扩展 Job/Application/UserProfile 字段"
```

---

## Task 2: 数据库迁移脚本

**Files:**
- Create: `backend/core/database/migrations/versions/001_add_resume_models.py`

- [ ] **Step 1: 创建迁移目录**

```bash
mkdir -p backend/core/database/migrations/versions
```

- [ ] **Step 2: 初始化 Alembic（如果未初始化）**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.database import engine
print('Database URL:', engine.url)
"
```

- [ ] **Step 3: 创建迁移脚本**

创建文件 `backend/core/database/migrations/versions/001_add_resume_models.py`：

```python
"""add resume models

Revision ID: 001
Revises:
Create Date: 2026-03-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建 resumes 表
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), server_default='1'),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_type', sa.String(20), server_default='pdf'),
        sa.Column('parse_engine', sa.String(20), server_default='rule'),
        sa.Column('is_primary', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建 resume_profiles 表
    op.create_table(
        'resume_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50)),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('gender', sa.String(10)),
        sa.Column('age', sa.Integer()),
        sa.Column('experience_years', sa.Integer()),
        sa.Column('current_position', sa.String(100)),
        sa.Column('current_company', sa.String(200)),
        sa.Column('target_positions', sa.JSON()),
        sa.Column('preferred_cities', sa.JSON()),
        sa.Column('salary_min', sa.Integer()),
        sa.Column('salary_max', sa.Integer()),
        sa.Column('education', sa.String(50)),
        sa.Column('school', sa.String(100)),
        sa.Column('major', sa.String(100)),
        sa.Column('skills', sa.JSON()),
        sa.Column('work_experiences', sa.JSON()),
        sa.Column('projects', sa.JSON()),
        sa.Column('ai_search_suggestions', sa.JSON()),
        sa.Column('ai_match_summary', sa.Text()),
        sa.Column('raw_text', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建 search_strategies 表
    op.create_table(
        'search_strategies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('resume_id', sa.Integer()),
        sa.Column('primary_keywords', sa.JSON()),
        sa.Column('variant_keywords', sa.JSON()),
        sa.Column('skill_combinations', sa.JSON()),
        sa.Column('cities', sa.JSON()),
        sa.Column('salary_min', sa.Integer()),
        sa.Column('salary_max', sa.Integer()),
        sa.Column('exclude_keywords', sa.JSON()),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 为 jobs 表添加新字段
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(sa.Column('pool_status', sa.String(20), server_default='pending'))
        batch_op.add_column(sa.Column('starred_at', sa.DateTime()))
        batch_op.add_column(sa.Column('match_details', sa.JSON()))

    # 为 applications 表添加新字段
    with op.batch_alter_table('applications') as batch_op:
        batch_op.add_column(sa.Column('delivery_status', sa.String(20), server_default='submitted'))
        batch_op.add_column(sa.Column('status_updated_at', sa.DateTime()))
        batch_op.add_column(sa.Column('greeting_used', sa.Text()))

    # 为 user_profiles 表添加新字段
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.add_column(sa.Column('run_mode', sa.String(20), server_default='manual'))
        batch_op.add_column(sa.Column('primary_resume_id', sa.Integer()))


def downgrade():
    op.drop_table('search_strategies')
    op.drop_table('resume_profiles')
    op.drop_table('resumes')

    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('pool_status')
        batch_op.drop_column('starred_at')
        batch_op.drop_column('match_details')

    with op.batch_alter_table('applications') as batch_op:
        batch_op.drop_column('delivery_status')
        batch_op.drop_column('status_updated_at')
        batch_op.drop_column('greeting_used')

    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.drop_column('run_mode')
        batch_op.drop_column('primary_resume_id')
```

- [ ] **Step 4: 执行迁移**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.database import Base, engine
from backend.core.database.models import Resume, ResumeProfile, SearchStrategy
Base.metadata.create_all(bind=engine)
print('Tables created successfully')
"
```

Expected: 输出 "Tables created successfully"

- [ ] **Step 5: 验证表结构**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', sorted(tables))

# 检查新表
assert 'resumes' in tables, 'resumes table missing'
assert 'resume_profiles' in tables, 'resume_profiles table missing'
assert 'search_strategies' in tables, 'search_strategies table missing'
print('All new tables exist!')
"
```

Expected: 输出所有表名并显示 "All new tables exist!"

- [ ] **Step 6: Commit**

```bash
git add backend/core/database/migrations/
git commit -m "feat: 添加数据库迁移脚本"
```

---

## Task 3: Resume API 调整

**Files:**
- Modify: `backend/api/resume.py`

- [ ] **Step 1: 添加新的 Pydantic 模型**

在 `backend/api/resume.py` 文件顶部的导入之后添加：

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ResumeCreate(BaseModel):
    """创建简历请求"""
    name: str
    file_type: str = "pdf"


class ResumeUpdate(BaseModel):
    """更新简历请求"""
    name: Optional[str] = None
    is_primary: Optional[bool] = None


class ResumeProfileUpdate(BaseModel):
    """更新简历画像请求"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    experience_years: Optional[int] = None
    current_position: Optional[str] = None
    target_positions: Optional[List[str]] = None
    preferred_cities: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    education: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    skills: Optional[List[str]] = None


class ResumeResponse(BaseModel):
    """简历响应"""
    id: int
    name: str
    file_type: str
    parse_engine: str
    is_primary: bool
    created_at: datetime
    profile: Optional[dict] = None
```

- [ ] **Step 2: 添加简历列表 API**

在文件末尾添加：

```python
@router.get("/list")
async def list_resumes(
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """获取简历列表"""
    from backend.core.database import Resume, ResumeProfile

    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()

    result = []
    for resume in resumes:
        profile = db.query(ResumeProfile).filter(
            ResumeProfile.resume_id == resume.id
        ).first()

        result.append({
            "id": resume.id,
            "name": resume.name,
            "file_type": resume.file_type,
            "parse_engine": resume.parse_engine,
            "is_primary": resume.is_primary,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "profile": {
                "name": profile.name,
                "experience_years": profile.experience_years,
                "current_position": profile.current_position,
                "skills": profile.skills,
            } if profile else None,
        })

    return {"items": result, "total": len(result)}


@router.post("/create", response_model=ResumeResponse)
async def create_resume(
    request: ResumeCreate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """创建新简历记录"""
    from backend.core.database import Resume

    resume = Resume(
        user_id=user_id,
        name=request.name,
        file_type=request.file_type,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeResponse(
        id=resume.id,
        name=resume.name,
        file_type=resume.file_type,
        parse_engine=resume.parse_engine,
        is_primary=resume.is_primary,
        created_at=resume.created_at,
    )


@router.put("/{resume_id}/profile")
async def update_resume_profile(
    resume_id: int,
    request: ResumeProfileUpdate,
    db: Session = Depends(get_db),
):
    """更新简历画像"""
    from backend.core.database import Resume, ResumeProfile

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")

    profile = db.query(ResumeProfile).filter(
        ResumeProfile.resume_id == resume_id
    ).first()

    if not profile:
        profile = ResumeProfile(resume_id=resume_id)
        db.add(profile)

    # 更新字段
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()

    return {"success": True, "message": "简历画像已更新"}


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
):
    """删除简历"""
    from backend.core.database import Resume

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")

    db.delete(resume)
    db.commit()

    return {"success": True, "message": "简历已删除"}


@router.post("/{resume_id}/set-primary")
async def set_primary_resume(
    resume_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """设置主简历"""
    from backend.core.database import Resume, UserProfile

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")

    # 清除其他主简历
    db.query(Resume).filter(
        Resume.user_id == user_id
    ).update({"is_primary": False})

    # 设置当前为主简历
    resume.is_primary = True

    # 更新用户画像
    profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if profile:
        profile.primary_resume_id = resume_id

    db.commit()

    return {"success": True, "message": f"已将 {resume.name} 设为主简历"}
```

- [ ] **Step 3: 测试 API**

启动服务器并测试：

```bash
cd /d E:\Code\auto_job_hunter && python run.py web &
```

```bash
curl -X GET "http://localhost:8000/api/resume/list"
```

Expected: 返回 `{"items": [], "total": 0}`

- [ ] **Step 4: Commit**

```bash
git add backend/api/resume.py
git commit -m "feat: 添加简历管理API (列表/创建/更新/删除/设置主简历)"
```

---

## Task 4: 单元测试

**Files:**
- Create: `tests/unit/test_models.py`

- [ ] **Step 1: 创建测试文件**

创建 `tests/unit/test_models.py`：

```python
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
```

- [ ] **Step 2: 运行测试**

```bash
cd /d E:\Code\auto_job_hunter && pytest tests/unit/test_models.py -v
```

Expected: 所有测试通过

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_models.py
git commit -m "test: 添加数据模型单元测试"
```

---

## Verification

- [ ] **运行所有测试**

```bash
cd /d E:\Code\auto_job_hunter && pytest tests/unit/ -v
```

Expected: 所有测试通过

- [ ] **启动服务验证**

```bash
cd /d E:\Code\auto_job_hunter && python run.py web
```

访问 http://localhost:8000/docs 验证新增API端点。

---

## Summary

完成本计划后：

1. **新增数据模型**：Resume, ResumeProfile, SearchStrategy
2. **扩展字段**：Job.pool_status/match_details, Application.delivery_status, UserProfile.run_mode
3. **新增API**：/resume/list, /resume/create, /resume/{id}/profile, /resume/{id}/set-primary
4. **数据库迁移**：支持创建/回滚

这些改动为后续的简历解析模块重构和多简历管理提供了数据基础。