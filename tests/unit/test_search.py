"""搜索模块单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from backend.core.search import (
    get_strategy_service,
    get_search_executor,
    StrategyService,
    SearchExecutor,
)
from backend.core.database import Base, Resume, SearchStrategy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def mock_session_local(db_session):
    """Mock SessionLocal that doesn't close the session"""
    class MockSessionLocal:
        def __call__(self):
            return db_session

        def close(self):
            # Don't actually close during tests
            pass

    return MockSessionLocal()


@pytest.fixture
def db_engine():
    """创建内存数据库引擎"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """创建数据库会话"""
    Session = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def reset_singletons():
    """重置单例实例"""
    import backend.core.search.strategy_service as ss_module
    import backend.core.search.search_executor as se_module

    ss_module._strategy_service = None
    se_module._search_executor = None
    yield
    ss_module._strategy_service = None
    se_module._search_executor = None


class TestStrategyService:
    """策略管理服务测试"""

    def test_get_strategy_service_singleton(self, reset_singletons):
        """测试服务单例"""
        service1 = get_strategy_service()
        service2 = get_strategy_service()
        assert service1 is service2

    def test_create_strategy(self, db_session, mock_session_local):
        """测试创建策略"""
        # 创建测试简历
        resume = Resume(user_id=1, name="测试简历", file_type="pdf")
        db_session.add(resume)
        db_session.commit()

        # 使用 mock 替换 SessionLocal
        with patch("backend.core.search.strategy_service.SessionLocal", mock_session_local):
            service = StrategyService()
            strategy = service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Python后端", "Django"],
                cities=["北京"],
            )

            assert strategy["id"] is not None
            assert "Python后端" in strategy["primary_keywords"]
            assert "北京" in strategy["cities"]

    def test_get_all_keywords(self, db_session, mock_session_local):
        """测试获取所有关键词"""
        # 创建测试简历
        resume = Resume(user_id=1, name="测试简历", file_type="pdf")
        db_session.add(resume)
        db_session.commit()

        # 使用 mock 替换 SessionLocal
        with patch("backend.core.search.strategy_service.SessionLocal", mock_session_local):
            service = StrategyService()

            # 创建策略
            strategy = service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Python"],
                variant_keywords=["Python开发"],
                skill_combinations=["Django"],
            )

            # 获取所有关键词
            keywords = service.get_all_keywords(strategy["id"])
            assert "Python" in keywords
            assert "Python开发" in keywords
            assert "Django" in keywords

    def test_get_strategy(self, db_session, mock_session_local):
        """测试获取策略"""
        # 创建测试简历
        resume = Resume(user_id=1, name="测试简历", file_type="pdf")
        db_session.add(resume)
        db_session.commit()

        with patch("backend.core.search.strategy_service.SessionLocal", mock_session_local):
            service = StrategyService()

            # 创建策略
            created = service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Python"],
                cities=["北京"],
            )

            # 获取策略
            strategy = service.get_strategy(created["id"])
            assert strategy is not None
            assert strategy["id"] == created["id"]
            assert "Python" in strategy["primary_keywords"]

    def test_get_strategies_by_resume(self, db_session, mock_session_local):
        """测试获取简历关联的所有策略"""
        # 创建测试简历
        resume = Resume(user_id=1, name="测试简历", file_type="pdf")
        db_session.add(resume)
        db_session.commit()

        with patch("backend.core.search.strategy_service.SessionLocal", mock_session_local):
            service = StrategyService()

            # 创建多个策略
            service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Python"],
                priority=1,
            )
            service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Java"],
                priority=2,
            )

            # 获取策略列表
            strategies = service.get_strategies_by_resume(resume.id)
            assert len(strategies) == 2
            # 按优先级降序排列
            assert strategies[0]["priority"] == 2

    def test_update_strategy(self, db_session, mock_session_local):
        """测试更新策略"""
        # 创建测试简历
        resume = Resume(user_id=1, name="测试简历", file_type="pdf")
        db_session.add(resume)
        db_session.commit()

        with patch("backend.core.search.strategy_service.SessionLocal", mock_session_local):
            service = StrategyService()

            # 创建策略
            created = service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Python"],
            )

            # 更新策略
            updated = service.update_strategy(
                created["id"],
                primary_keywords=["Python", "Django"],
                cities=["北京", "上海"],
            )

            assert updated is not None
            assert "Django" in updated["primary_keywords"]
            assert "北京" in updated["cities"]

    def test_delete_strategy(self, db_session, mock_session_local):
        """测试删除策略"""
        # 创建测试简历
        resume = Resume(user_id=1, name="测试简历", file_type="pdf")
        db_session.add(resume)
        db_session.commit()

        with patch("backend.core.search.strategy_service.SessionLocal", mock_session_local):
            service = StrategyService()

            # 创建策略
            created = service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Python"],
            )

            # 删除策略
            result = service.delete_strategy(created["id"])
            assert result is True

            # 确认已删除
            strategy = service.get_strategy(created["id"])
            assert strategy is None

    def test_get_all_keywords_deduplication(self, db_session, mock_session_local):
        """测试关键词去重"""
        # 创建测试简历
        resume = Resume(user_id=1, name="测试简历", file_type="pdf")
        db_session.add(resume)
        db_session.commit()

        with patch("backend.core.search.strategy_service.SessionLocal", mock_session_local):
            service = StrategyService()

            # 创建策略，包含重复关键词
            strategy = service.create_strategy(
                resume_id=resume.id,
                primary_keywords=["Python", "Python"],
                variant_keywords=["Python开发", "Django"],
                skill_combinations=["Django", "Flask"],
            )

            # 获取所有关键词
            keywords = service.get_all_keywords(strategy["id"])

            # 检查去重
            assert keywords.count("Python") == 1
            assert keywords.count("Django") == 1


class TestSearchExecutor:
    """搜索执行器测试"""

    def test_get_search_executor_singleton(self, reset_singletons):
        """测试执行器单例"""
        executor1 = get_search_executor()
        executor2 = get_search_executor()
        assert executor1 is executor2

    def test_deduplicate_jobs_with_id(self):
        """测试基于ID的职位去重"""
        executor = SearchExecutor()

        jobs = [
            {"id": "job_1", "title": "Python工程师", "company": "公司A", "platform": "boss"},
            {"id": "job_2", "title": "Java工程师", "company": "公司B", "platform": "boss"},
            {"id": "job_1", "title": "Python工程师", "company": "公司A", "platform": "boss"},  # 重复
        ]

        unique = executor._deduplicate_jobs(jobs)

        assert len(unique) == 2
        titles = [j["title"] for j in unique]
        assert "Python工程师" in titles
        assert "Java工程师" in titles

    def test_deduplicate_jobs_without_id(self):
        """测试基于公司+职位的去重"""
        executor = SearchExecutor()

        jobs = [
            {"id": None, "title": "前端工程师", "company": "公司C", "platform": "boss"},
            {"id": None, "title": "前端工程师", "company": "公司C", "platform": "boss"},  # 重复
            {"id": None, "title": "前端工程师", "company": "公司D", "platform": "boss"},  # 不同公司
        ]

        unique = executor._deduplicate_jobs(jobs)

        assert len(unique) == 2

    def test_deduplicate_jobs_mixed(self):
        """测试混合去重"""
        executor = SearchExecutor()

        jobs = [
            {"id": "job_1", "title": "Python工程师", "company": "公司A", "platform": "boss"},
            {"id": "job_2", "title": "Java工程师", "company": "公司B", "platform": "boss"},
            {"id": "job_1", "title": "Python工程师", "company": "公司A", "platform": "boss"},  # ID重复
            {"id": None, "title": "前端工程师", "company": "公司C", "platform": "boss"},
            {"id": None, "title": "前端工程师", "company": "公司C", "platform": "boss"},  # 公司+职位重复
        ]

        unique = executor._deduplicate_jobs(jobs)

        assert len(unique) == 3
        titles = [j["title"] for j in unique]
        assert "Python工程师" in titles
        assert "Java工程师" in titles
        assert "前端工程师" in titles

    def test_job_to_dict(self):
        """测试职位转换"""
        executor = SearchExecutor()

        # 模拟 JobInfo 对象
        class MockJob:
            id = "test_123"
            title = "测试职位"
            company = "测试公司"
            salary = "20-30K"
            salary_min = 20
            salary_max = 30
            city = "北京"
            company_size = "100-499人"
            company_size_min = 100
            company_size_max = 499
            job_type = None
            experience_required = "3-5年"
            experience_min = 3
            experience_max = 5
            description = "职位描述"
            hr_name = "张三"
            url = "https://example.com/job/123"
            platform = "boss"

        result = executor._job_to_dict(MockJob())

        assert result["id"] == "test_123"
        assert result["title"] == "测试职位"
        assert result["company"] == "测试公司"
        assert result["salary"] == "20-30K"
        assert result["city"] == "北京"
        assert result["platform"] == "boss"

    def test_parse_platforms_default(self):
        """测试默认平台解析"""
        executor = SearchExecutor()

        from backend.adapters import Platform

        platforms = executor._parse_platforms(None)

        assert len(platforms) == 2
        assert Platform.BOSS in platforms
        assert Platform.LIEPIN in platforms

    def test_parse_platforms_specific(self):
        """测试指定平台解析"""
        executor = SearchExecutor()

        from backend.adapters import Platform

        platforms = executor._parse_platforms(["boss"])

        assert len(platforms) == 1
        assert platforms[0] == Platform.BOSS

    def test_parse_platforms_invalid(self):
        """测试无效平台处理"""
        executor = SearchExecutor()

        from backend.adapters import Platform

        # 无效平台会被忽略，返回默认平台
        platforms = executor._parse_platforms(["invalid_platform"])

        # 无效平台时返回默认平台
        assert len(platforms) == 2
        assert Platform.BOSS in platforms
        assert Platform.LIEPIN in platforms

    def test_get_adapter_caching(self):
        """测试适配器缓存"""
        executor = SearchExecutor()

        from backend.adapters import Platform

        adapter1 = executor.get_adapter(Platform.BOSS)
        adapter2 = executor.get_adapter(Platform.BOSS)

        # 应该返回同一个适配器实例
        assert adapter1 is adapter2