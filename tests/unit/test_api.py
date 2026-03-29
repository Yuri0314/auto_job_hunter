"""
API 端点单元测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    with patch("backend.api.settings.SessionLocal") as mock:
        db = MagicMock()
        mock.return_value = db
        yield db


class TestSystemAPI:
    """系统 API 测试"""

    def test_get_status(self, client):
        """测试获取系统状态"""
        response = client.get("/api/system/status")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_get_platforms(self, client):
        """测试获取平台状态"""
        response = client.get("/api/system/platforms")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestUserAPI:
    """用户 API 测试"""

    def test_get_profile(self, client):
        """测试获取用户画像"""
        response = client.get("/api/user/profile")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_update_profile(self, client):
        """测试更新用户画像"""
        response = client.put(
            "/api/user/profile",
            json={"name": "测试用户", "city": "北京"}
        )

        assert response.status_code == 200


class TestSettingsAPI:
    """设置 API 测试"""

    def test_get_categories(self, client):
        """测试获取配置分类"""
        response = client.get("/api/settings/categories")

        assert response.status_code == 200
        data = response.json()
        assert "basic" in data
        assert "ai" in data

    def test_get_config_items(self, client):
        """测试获取配置项"""
        response = client.get("/api/settings/items")

        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data

    def test_get_config_items_by_category(self, client):
        """测试按分类获取配置项"""
        response = client.get("/api/settings/items?category=basic")

        assert response.status_code == 200
        data = response.json()
        # 应该只包含 basic 分类的配置
        for key, item in data.items():
            assert item.get("category") == "basic"


class TestJobsAPI:
    """职位 API 测试"""

    def test_list_jobs(self, client):
        """测试获取职位列表"""
        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data


class TestApplicationsAPI:
    """投递 API 测试"""

    def test_list_applications(self, client):
        """测试获取投递记录"""
        response = client.get("/api/applications")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data


class TestMessagesAPI:
    """消息 API 测试"""

    def test_list_messages(self, client):
        """测试获取消息列表"""
        response = client.get("/api/messages")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data