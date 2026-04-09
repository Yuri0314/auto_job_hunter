"""核心配置管理模块 - 支持三层优先级"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, Dict, Any, List, Union
from functools import lru_cache

from backend.core.security import decrypt_value, is_encrypted

# 配置分类定义
CONFIG_CATEGORIES = {
    "basic": {
        "name": "基础配置",
        "description": "应用基本设置",
        "keys": ["debug", "log_level", "scheduler_enabled", "max_concurrent_jobs"],
    },
    "platform": {
        "name": "平台账号",
        "description": "招聘平台登录配置",
        "keys": [
            "boss_phone", "boss_password",
            "liepin_phone", "liepin_password",
            "maimai_phone", "maimai_password",
        ],
    },
    "ai": {
        "name": "AI配置",
        "description": "AI模型服务配置",
        "keys": [
            "openai_api_key", "openai_model",
            "ollama_base_url", "ollama_model",
        ],
    },
    "advanced": {
        "name": "高级设置",
        "description": "高级功能和通知配置",
        "keys": [
            "webhook_url", "log_file",
            "smtp_host", "smtp_port", "smtp_username", "smtp_password",
        ],
    },
}

# 敏感配置项（需要掩码处理）
SENSITIVE_KEYS = [
    "openai_api_key",
    "boss_password",
    "liepin_password",
    "maimai_password",
    "smtp_password",
    "secret_key",
]

# 不可编辑的配置项（通过API不允许修改）
NON_EDITABLE_KEYS = [
    "database_url",
    "redis_url",
    "secret_key",
    "access_token_expire_minutes",
]

# 配置项元信息（用于前端展示）
CONFIG_METADATA = {
    "debug": {
        "display_name": "调试模式",
        "description": "启用调试日志和开发模式",
        "input_type": "switch",
        "category": "basic",
    },
    "log_level": {
        "display_name": "日志级别",
        "description": "日志输出级别",
        "input_type": "select",
        "options": ["DEBUG", "INFO", "WARNING", "ERROR"],
        "category": "basic",
    },
    "scheduler_enabled": {
        "display_name": "启用调度",
        "description": "自动定时搜索投递",
        "input_type": "switch",
        "category": "basic",
    },
    "max_concurrent_jobs": {
        "display_name": "最大并发数",
        "description": "同时处理的职位数量上限",
        "input_type": "number",
        "min": 1,
        "max": 20,
        "category": "basic",
    },
    "boss_phone": {
        "display_name": "BOSS直聘手机号",
        "description": "BOSS直聘登录手机号",
        "input_type": "text",
        "category": "platform",
        "is_sensitive": False,
    },
    "boss_password": {
        "display_name": "BOSS直聘密码/验证码",
        "description": "登录密码或短信验证码（登录时动态获取）",
        "input_type": "password",
        "category": "platform",
        "is_sensitive": True,
    },
    "liepin_phone": {
        "display_name": "猎聘手机号",
        "description": "猎聘登录手机号",
        "input_type": "text",
        "category": "platform",
        "is_sensitive": False,
    },
    "liepin_password": {
        "display_name": "猎聘密码/验证码",
        "description": "登录密码或短信验证码（登录时动态获取）",
        "input_type": "password",
        "category": "platform",
        "is_sensitive": True,
    },
    "maimai_phone": {
        "display_name": "脉脉手机号",
        "description": "脉脉登录手机号",
        "input_type": "text",
        "category": "platform",
        "is_sensitive": False,
    },
    "maimai_password": {
        "display_name": "脉脉密码/验证码",
        "description": "登录密码或短信验证码（登录时动态获取）",
        "input_type": "password",
        "category": "platform",
        "is_sensitive": True,
    },
    "openai_api_key": {
        "display_name": "OpenAI API Key",
        "description": "OpenAI API密钥",
        "input_type": "password",
        "category": "ai",
        "is_sensitive": True,
    },
    "openai_model": {
        "display_name": "OpenAI模型",
        "description": "使用的GPT模型",
        "input_type": "select",
        "options": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        "category": "ai",
    },
    "ollama_base_url": {
        "display_name": "Ollama服务地址",
        "description": "本地Ollama服务URL",
        "input_type": "text",
        "category": "ai",
    },
    "ollama_model": {
        "display_name": "Ollama模型",
        "description": "本地模型名称",
        "input_type": "text",
        "category": "ai",
    },
    "webhook_url": {
        "display_name": "Webhook URL",
        "description": "通知推送地址",
        "input_type": "text",
        "category": "advanced",
    },
    "log_file": {
        "display_name": "日志文件路径",
        "description": "日志存储路径",
        "input_type": "text",
        "category": "advanced",
    },
    "smtp_host": {
        "display_name": "SMTP服务器",
        "description": "邮件发送服务器",
        "input_type": "text",
        "category": "advanced",
    },
    "smtp_port": {
        "display_name": "SMTP端口",
        "description": "邮件服务器端口",
        "input_type": "number",
        "category": "advanced",
    },
    "smtp_username": {
        "display_name": "SMTP用户名",
        "description": "邮件发送账号",
        "input_type": "text",
        "category": "advanced",
    },
    "smtp_password": {
        "display_name": "SMTP密码",
        "description": "邮件发送密码",
        "input_type": "password",
        "category": "advanced",
        "is_sensitive": True,
    },
}


class Settings(BaseSettings):
    """应用配置类 - 支持三层优先级"""

    # 应用配置
    app_name: str = Field(default="Auto Job Hunter", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./auto_job_hunter.db",
        alias="DATABASE_URL"
    )

    # Redis配置
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # AI模型配置
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")

    # 本地模型配置
    ollama_base_url: Optional[str] = Field(default=None, alias="OLLAMA_BASE_URL")
    ollama_model: Optional[str] = Field(default=None, alias="OLLAMA_MODEL")

    # 平台配置 - BOSS直聘
    boss_phone: Optional[str] = Field(default=None, alias="BOSS_PHONE")
    boss_password: Optional[str] = Field(default=None, alias="BOSS_PASSWORD")  # 保留兼容

    # 平台配置 - 猎聘
    liepin_phone: Optional[str] = Field(default=None, alias="LIEPIN_PHONE")
    liepin_password: Optional[str] = Field(default=None, alias="LIEPIN_PASSWORD")  # 保留兼容

    # 平台配置 - 脉脉
    maimai_phone: Optional[str] = Field(default=None, alias="MAIMAI_PHONE")
    maimai_password: Optional[str] = Field(default=None, alias="MAIMAI_PASSWORD")  # 保留兼容

    # 安全配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # 任务调度配置
    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")
    max_concurrent_jobs: int = Field(default=5, alias="MAX_CONCURRENT_JOBS")

    # 日志配置
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, alias="LOG_FILE")

    # 通知配置
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=None, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    webhook_url: Optional[str] = Field(default=None, alias="WEBHOOK_URL")

    # CORS 配置 - 生产环境应设置具体域名，多个用逗号分隔
    allowed_origins: str = Field(
        default="http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000",
        alias="ALLOWED_ORIGINS"
    )

    # Pydantic V2 配置方式
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 忽略 .env 中的未知字段
    )

    # 内部状态（不计入配置）
    _db_overrides: Dict[str, str] = {}
    _initialized_from_db: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化内部状态
        self._db_overrides = {}
        self._initialized_from_db = False

    def load_from_database(self, db_session) -> None:
        """从数据库加载覆盖配置"""
        from backend.core.database import SystemConfig

        configs = db_session.query(SystemConfig).all()
        for c in configs:
            # 解密敏感配置
            if c.key in SENSITIVE_KEYS and c.value and is_encrypted(c.value):
                try:
                    self._db_overrides[c.key] = decrypt_value(c.value)
                except Exception:
                    # 解密失败，使用原值
                    self._db_overrides[c.key] = c.value
            else:
                self._db_overrides[c.key] = c.value

        self._initialized_from_db = True

    def get_effective_value(self, field_name: str) -> Any:
        """获取有效配置值（按优先级）

        优先级：数据库 > 环境变量 > 默认值
        """
        # 数据库值优先
        if field_name in self._db_overrides:
            db_value = self._db_overrides[field_name]
            # 类型转换 - 使用 model_fields (Pydantic v2) 或 __fields__ (v1)
            field_info = self._get_field_info(field_name)
            if field_info:
                # 处理布尔值
                annotation = self._get_field_annotation(field_info)
                if annotation == bool or (hasattr(annotation, "__origin__") and annotation.__origin__ is Union and bool in getattr(annotation, "__args__", [])):
                    return db_value.lower() in ("true", "1", "yes")
                # 处理整数
                if annotation == int or (hasattr(annotation, "__origin__") and annotation.__origin__ is Union and int in getattr(annotation, "__args__", [])):
                    try:
                        return int(db_value)
                    except ValueError:
                        pass
            return db_value

        # 返回环境变量或默认值
        return getattr(self, field_name, None)

    def _get_field_info(self, field_name: str) -> Any:
        """获取字段信息（兼容 Pydantic v1 和 v2）"""
        # Pydantic v2 使用 model_fields
        model_fields = getattr(type(self), "model_fields", None)
        if model_fields is not None:
            return model_fields.get(field_name)
        # Pydantic v1 使用 __fields__
        fields = getattr(type(self), "__fields__", None)
        if fields is not None:
            return fields.get(field_name)
        return None

    def _get_field_annotation(self, field_info: Any) -> Any:
        """获取字段类型注解（兼容 Pydantic v1 和 v2）"""
        # Pydantic v2
        if hasattr(field_info, "annotation"):
            return field_info.annotation
        # Pydantic v1
        if hasattr(field_info, "type_"):
            return field_info.type_
        return None

    def get_value_source(self, field_name: str) -> str:
        """获取配置值的来源"""
        if field_name in self._db_overrides:
            return "database"

        # 获取默认值
        field_info = self._get_field_info(field_name)
        if field_info:
            default = self._get_field_default(field_info)
            current = getattr(self, field_name, None)
            if current != default and current is not None:
                return "env"

        return "default"

    def _get_field_default(self, field_info: Any) -> Any:
        """获取字段默认值（兼容 Pydantic v1 和 v2）"""
        # Pydantic v2
        if hasattr(field_info, "default"):
            return field_info.default
        # Pydantic v1
        if hasattr(field_info, "default_factory"):
            return field_info.default_factory() if field_info.default_factory else None
        return None

    def to_config_items(self, mask_sensitive: bool = True) -> Dict[str, Dict]:
        """导出所有配置项（含来源和掩码处理）"""
        result = {}

        # 获取所有字段名
        field_names = self._get_all_field_names()

        for field_name in field_names:
            # 获取值和来源
            effective_value = self.get_effective_value(field_name)
            source = self.get_value_source(field_name)

            # 获取默认值
            field_info = self._get_field_info(field_name)
            default_value = self._get_field_default(field_info) if field_info else None

            # 获取元信息
            meta = CONFIG_METADATA.get(field_name, {})
            is_sensitive = meta.get("is_sensitive", field_name in SENSITIVE_KEYS)

            # 掩码处理
            display_value = effective_value
            if mask_sensitive and is_sensitive and effective_value:
                display_value = "***CONFIGURED***"

            result[field_name] = {
                "key": field_name,
                "value": str(display_value) if display_value is not None else None,
                "default_value": str(default_value) if default_value is not None else None,
                "effective_value": str(effective_value) if effective_value is not None else None,
                "source": source,
                "is_sensitive": is_sensitive,
                "is_editable": field_name not in NON_EDITABLE_KEYS,
                "display_name": meta.get("display_name", field_name),
                "description": meta.get("description", ""),
                "input_type": meta.get("input_type", "text"),
                "options": meta.get("options"),
                "category": meta.get("category", "basic"),
            }

        return result

    def _get_all_field_names(self) -> List[str]:
        """获取所有配置字段名（兼容 Pydantic v1 和 v2）"""
        # Pydantic v2 使用 model_fields
        model_fields = getattr(type(self), "model_fields", None)
        if model_fields is not None:
            return list(model_fields.keys())
        # Pydantic v1 使用 __fields__
        fields = getattr(type(self), "__fields__", None)
        if fields is not None:
            return list(fields.keys())
        # 从 CONFIG_METADATA 获取
        return list(CONFIG_METADATA.keys())


# 全局配置实例（支持动态刷新）
_settings_instance: Optional[Settings] = None


def get_settings(use_cache: bool = True) -> Settings:
    """获取配置实例

    Args:
        use_cache: 是否使用缓存的实例
    """
    global _settings_instance

    if not use_cache or _settings_instance is None:
        _settings_instance = Settings()

    return _settings_instance


def reload_settings(db_session) -> Settings:
    """重新加载配置（包含数据库配置）

    配置优先级：数据库 > 环境变量 > 默认值
    """
    settings = Settings()
    settings.load_from_database(db_session)

    global _settings_instance
    _settings_instance = settings

    return settings


def invalidate_settings_cache() -> None:
    """清除配置缓存"""
    global _settings_instance
    _settings_instance = None


def get_config_categories() -> Dict[str, Dict]:
    """获取配置分类列表"""
    return CONFIG_CATEGORIES


def is_sensitive_key(key: str) -> bool:
    """判断是否为敏感配置项"""
    return key in SENSITIVE_KEYS


def is_editable_key(key: str) -> bool:
    """判断配置项是否可通过API编辑"""
    return key not in NON_EDITABLE_KEYS


def mask_sensitive_value(key: str, value: Optional[str]) -> Optional[str]:
    """掩码处理敏感值"""
    if key in SENSITIVE_KEYS and value:
        return "***CONFIGURED***"
    return value
