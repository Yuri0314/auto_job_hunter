"""核心配置管理模块"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""

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
    boss_username: Optional[str] = Field(default=None, alias="BOSS_USERNAME")
    boss_password: Optional[str] = Field(default=None, alias="BOSS_PASSWORD")

    # 平台配置 - 猎聘
    liepin_username: Optional[str] = Field(default=None, alias="LIEPIN_USERNAME")
    liepin_password: Optional[str] = Field(default=None, alias="LIEPIN_PASSWORD")

    # 平台配置 - 脉脉
    maimai_username: Optional[str] = Field(default=None, alias="MAIMAI_USERNAME")
    maimai_password: Optional[str] = Field(default=None, alias="MAIMAI_PASSWORD")

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()