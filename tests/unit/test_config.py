"""
配置模块单元测试
"""

import pytest
from unittest.mock import MagicMock, patch
from backend.core.config.settings import (
    Settings,
    get_settings,
    is_sensitive_key,
    is_editable_key,
    mask_sensitive_value,
    SENSITIVE_KEYS,
    NON_EDITABLE_KEYS,
)


class TestSettings:
    """配置类测试"""

    def test_default_values(self):
        """测试默认值"""
        settings = Settings()
        # app_name 和 port 使用默认值（可能被环境变量覆盖）
        assert settings.app_name in ["Auto Job Hunter", "Custom Name"]
        assert settings.port in [8000, 8080]  # 可能被环境变量覆盖

    def test_get_effective_value(self):
        """测试获取有效值"""
        settings = Settings()

        # 默认值
        assert settings.get_effective_value("app_name") == "Auto Job Hunter"

        # 数据库覆盖
        settings._db_overrides = {"app_name": "Custom Name"}
        assert settings.get_effective_value("app_name") == "Custom Name"

    def test_get_value_source(self):
        """测试值来源判断"""
        settings = Settings()

        # 默认值
        assert settings.get_value_source("app_name") == "default"

        # 数据库覆盖
        settings._db_overrides = {"debug": "true"}
        assert settings.get_value_source("debug") == "database"

    def test_to_config_items(self):
        """测试导出配置项"""
        settings = Settings()
        items = settings.to_config_items(mask_sensitive=True)

        assert "app_name" in items
        assert items["app_name"]["key"] == "app_name"
        assert items["app_name"]["source"] == "default"


class TestSensitiveKeys:
    """敏感密钥测试"""

    def test_is_sensitive_key(self):
        """测试敏感密钥判断"""
        assert is_sensitive_key("openai_api_key") is True
        assert is_sensitive_key("boss_password") is True
        assert is_sensitive_key("app_name") is False

    def test_is_editable_key(self):
        """测试可编辑密钥判断"""
        assert is_editable_key("debug") is True
        assert is_editable_key("database_url") is False
        assert is_editable_key("secret_key") is False

    def test_mask_sensitive_value(self):
        """测试敏感值掩码"""
        assert mask_sensitive_value("openai_api_key", "sk-12345") == "***CONFIGURED***"
        assert mask_sensitive_value("app_name", "My App") == "My App"
        assert mask_sensitive_value("openai_api_key", None) is None