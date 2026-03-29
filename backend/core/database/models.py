"""数据库模型定义"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.core.database.session import Base


class JobStatus(str, enum.Enum):
    """职位状态"""
    NEW = "new"                 # 新发现
    FILTERED = "filtered"       # 已过滤
    APPLIED = "applied"         # 已投递
    INTERVIEWED = "interviewed" # 面试中
    REJECTED = "rejected"       # 已拒绝
    OFFERED = "offered"         # 已录用
    EXPIRED = "expired"         # 已过期


class ApplicationStatus(str, enum.Enum):
    """投递状态"""
    PENDING = "pending"     # 待处理
    SUCCESS = "success"     # 成功
    FAILED = "failed"       # 失败
    RETRY = "retry"         # 重试中


class Job(Base):
    """职位表"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), unique=True, nullable=False, comment="职位平台ID")
    platform = Column(String(50), nullable=False, comment="平台名称")

    # 职位信息
    title = Column(String(200), nullable=False, comment="职位标题")
    company = Column(String(200), nullable=False, comment="公司名称")
    salary = Column(String(50), comment="薪资范围")
    salary_min = Column(Integer, comment="最低薪资(K)")
    salary_max = Column(Integer, comment="最高薪资(K)")
    city = Column(String(50), comment="城市")
    district = Column(String(50), comment="区县")
    address = Column(String(200), comment="详细地址")

    # 公司信息
    company_size = Column(String(50), comment="公司规模")
    company_industry = Column(String(100), comment="行业")
    company_stage = Column(String(50), comment="融资阶段")

    # 职位详情
    description = Column(Text, comment="职位描述")
    requirements = Column(Text, comment="职位要求")
    experience_required = Column(String(50), comment="经验要求")
    education_required = Column(String(50), comment="学历要求")
    job_type = Column(String(50), comment="工作类型")

    # HR信息
    hr_name = Column(String(50), comment="HR姓名")
    hr_title = Column(String(50), comment="HR职位")

    # 元信息
    url = Column(String(500), comment="职位链接")
    raw_data = Column(JSON, comment="原始数据")

    # 匹配分析
    match_score = Column(Integer, comment="匹配度分数")
    match_points = Column(JSON, comment="匹配点")
    gap_points = Column(JSON, comment="差距点")

    # 状态
    status = Column(
        SQLEnum(JobStatus),
        default=JobStatus.NEW,
        comment="职位状态"
    )

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    applied_at = Column(DateTime, comment="投递时间")

    # 职位池状态
    pool_status = Column(String(20), default="pending", comment="职位池状态: pending/starred/rejected/queued")
    starred_at = Column(DateTime, comment="收藏时间")

    # 匹配分析扩展
    match_details = Column(JSON, comment="匹配分析详情")

    def __repr__(self):
        return f"<Job({self.title} @ {self.company})>"


class Application(Base):
    """投递记录表"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, nullable=False, comment="关联职位ID")

    # 投递信息
    platform = Column(String(50), nullable=False, comment="平台")
    greeting = Column(Text, comment="打招呼语")
    resume_id = Column(String(100), comment="使用的简历ID")

    # 投递结果
    status = Column(
        SQLEnum(ApplicationStatus),
        default=ApplicationStatus.PENDING,
        comment="投递状态"
    )
    error_message = Column(Text, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    submitted_at = Column(DateTime, comment="提交时间")

    # 投递状态追踪
    delivery_status = Column(String(20), default="submitted", comment="投递状态: submitted/read/replied/interview/rejected/expired")
    status_updated_at = Column(DateTime, comment="状态更新时间")
    greeting_used = Column(Text, comment="使用的打招呼语")

    def __repr__(self):
        return f"<Application(job_id={self.job_id}, status={self.status})>"


class Message(Base):
    """HR消息表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, comment="平台")
    conversation_id = Column(String(100), comment="会话ID")

    # 消息信息
    sender_name = Column(String(50), comment="发送者姓名")
    sender_title = Column(String(50), comment="发送者职位")
    company = Column(String(200), comment="公司")
    content = Column(Text, nullable=False, comment="消息内容")

    # 关联职位
    job_id = Column(Integer, comment="关联职位ID")
    job_title = Column(String(200), comment="职位标题")

    # 消息状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_replied = Column(Boolean, default=False, comment="是否已回复")
    reply_content = Column(Text, comment="回复内容")

    # AI分析
    intent = Column(String(50), comment="意图分类")
    sentiment = Column(String(20), comment="情感分析")
    suggested_reply = Column(Text, comment="建议回复")

    # 时间戳
    received_at = Column(DateTime, comment="接收时间")
    replied_at = Column(DateTime, comment="回复时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<Message(from={self.sender_name}, content={self.content[:20]}...)>"


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


class UserProfile(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), comment="姓名")
    email = Column(String(100), comment="邮箱")
    phone = Column(String(20), comment="手机号")

    # 基本信息
    gender = Column(String(10), comment="性别")
    age = Column(Integer, comment="年龄")
    city = Column(String(50), comment="所在城市")
    experience_years = Column(Integer, comment="工作年限")

    # 教育背景
    education = Column(String(50), comment="学历")
    school = Column(String(100), comment="学校")
    major = Column(String(100), comment="专业")

    # 求职意向
    target_positions = Column(JSON, comment="目标职位列表")
    target_cities = Column(JSON, comment="目标城市列表")
    expected_salary_min = Column(Integer, comment="期望薪资下限(K)")
    expected_salary_max = Column(Integer, comment="期望薪资上限(K)")

    # 技能
    skills = Column(JSON, comment="技能列表")
    certifications = Column(JSON, comment="证书列表")

    # 工作经历
    work_experiences = Column(JSON, comment="工作经历")

    # 简历
    resume_text = Column(Text, comment="简历文本")
    resume_file = Column(String(500), comment="简历文件路径")

    # 配置
    strategy = Column(String(50), default="simple", comment="投递策略")
    auto_reply_enabled = Column(Boolean, default=False, comment="自动回复开关")
    daily_application_limit = Column(Integer, default=50, comment="每日投递上限")

    # 运行模式
    run_mode = Column(String(20), default="manual", comment="运行模式: manual/ai_assisted/ai_full_auto")
    primary_resume_id = Column(Integer, comment="主简历ID")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<UserProfile(name={self.name})>"


class FilterRule(Base):
    """过滤规则表"""
    __tablename__ = "filter_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")

    # 规则内容
    keywords = Column(JSON, comment="关键词列表")
    exclude_keywords = Column(JSON, comment="排除关键词")
    salary_range = Column(JSON, comment="薪资范围")
    cities = Column(JSON, comment="城市列表")
    company_size_range = Column(JSON, comment="公司规模范围")
    experience_range = Column(JSON, comment="经验范围")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<FilterRule(name={self.name})>"


class ApplicationLog(Base):
    """投递日志表"""
    __tablename__ = "application_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, comment="投递ID")

    # 日志内容
    level = Column(String(20), comment="日志级别")
    message = Column(Text, comment="日志消息")
    extra_data = Column(JSON, comment="额外数据")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<ApplicationLog(level={self.level})>"


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, comment="配置键")
    value = Column(Text, comment="配置值")
    description = Column(Text, comment="配置描述")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<SystemConfig(key={self.key})>"