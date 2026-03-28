"""系统配置 API"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from backend.core.config import (
    get_settings,
    reload_settings,
    get_config_categories,
    is_sensitive_key,
    is_editable_key,
    mask_sensitive_value,
    CONFIG_METADATA,
    SENSITIVE_KEYS,
    NON_EDITABLE_KEYS,
)
from backend.core.database import SessionLocal, SystemConfig


router = APIRouter()


# ============ Pydantic Models ============

class ConfigCategoryResponse(BaseModel):
    """配置分类响应"""
    name: str
    display_name: str
    description: str
    keys: List[str]


class ConfigItemResponse(BaseModel):
    """配置项响应"""
    key: str
    value: Optional[str]
    default_value: Optional[str]
    effective_value: Optional[str]
    source: str  # "database", "env", "default"
    is_sensitive: bool
    is_editable: bool
    display_name: str
    description: str
    input_type: str
    options: Optional[List[str]] = None
    category: str


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    value: str


class ConfigBatchUpdateRequest(BaseModel):
    """批量配置更新请求"""
    items: Dict[str, str]


class ConfigResetResponse(BaseModel):
    """配置重置响应"""
    key: str
    message: str
    new_value: Optional[str]


# ============ Helper Functions ============

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_editable(key: str) -> bool:
    """校验配置项是否可编辑"""
    if key not in CONFIG_METADATA:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration key '{key}' not found"
        )

    if key in NON_EDITABLE_KEYS:
        raise HTTPException(
            status_code=403,
            detail=f"Configuration '{key}' cannot be modified via API"
        )

    return True


def get_config_from_db(db, key: str) -> Optional[SystemConfig]:
    """从数据库获取配置"""
    return db.query(SystemConfig).filter(SystemConfig.key == key).first()


# ============ API Endpoints ============

@router.get("/categories", response_model=Dict[str, ConfigCategoryResponse])
async def get_categories():
    """获取配置分类列表"""
    categories = get_config_categories()

    result = {}
    for cat_key, cat_info in categories.items():
        result[cat_key] = ConfigCategoryResponse(
            name=cat_key,
            display_name=cat_info["name"],
            description=cat_info["description"],
            keys=cat_info["keys"],
        )

    return result


@router.get("/items", response_model=Dict[str, ConfigItemResponse])
async def get_all_config_items(
    category: Optional[str] = None,
    mask: bool = True,
):
    """获取所有配置项

    Args:
        category: 可选，按分类筛选
        mask: 是否掩码敏感信息，默认 True
    """
    settings = get_settings()
    all_items = settings.to_config_items(mask_sensitive=mask)

    # 按分类筛选
    if category:
        categories = get_config_categories()
        if category not in categories:
            raise HTTPException(
                status_code=404,
                detail=f"Category '{category}' not found"
            )

        allowed_keys = categories[category]["keys"]
        all_items = {
            k: v for k, v in all_items.items()
            if k in allowed_keys
        }

    return all_items


@router.get("/items/{key}", response_model=ConfigItemResponse)
async def get_config_item(key: str, mask: bool = True):
    """获取单个配置项"""
    settings = get_settings()
    all_items = settings.to_config_items(mask_sensitive=mask)

    if key not in all_items:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration key '{key}' not found"
        )

    return all_items[key]


@router.put("/items/{key}", response_model=ConfigItemResponse)
async def update_config_item(
    key: str,
    request: ConfigUpdateRequest,
    db=Depends(get_db),
):
    """更新单个配置项"""
    validate_editable(key)

    # 更新或创建数据库记录
    config = get_config_from_db(db, key)

    if config:
        config.value = request.value
    else:
        config = SystemConfig(
            key=key,
            value=request.value,
            description=CONFIG_METADATA.get(key, {}).get("description", ""),
        )
        db.add(config)

    db.commit()

    # 重新加载配置
    reload_settings(db)

    logger.info(f"Configuration updated: {key}")

    # 返回更新后的配置项（掩码敏感信息）
    settings = get_settings()
    all_items = settings.to_config_items(mask_sensitive=True)

    return all_items[key]


@router.put("/batch", response_model=Dict[str, ConfigItemResponse])
async def batch_update_config(
    request: ConfigBatchUpdateRequest,
    db=Depends(get_db),
):
    """批量更新配置项"""
    updated_items = {}
    errors = []

    for key, value in request.items.items():
        try:
            validate_editable(key)

            # 更新数据库
            config = get_config_from_db(db, key)
            if config:
                config.value = value
            else:
                config = SystemConfig(
                    key=key,
                    value=value,
                    description=CONFIG_METADATA.get(key, {}).get("description", ""),
                )
                db.add(config)

            updated_items[key] = True

        except HTTPException as e:
            errors.append(f"{key}: {e.detail}")
            continue

    if updated_items:
        db.commit()
        reload_settings(db)
        logger.info(f"Batch configuration updated: {list(updated_items.keys())}")

    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Some items failed to update: {', '.join(errors)}"
        )

    # 返回更新后的配置项
    settings = get_settings()
    all_items = settings.to_config_items(mask_sensitive=True)

    return {
        key: all_items[key]
        for key in updated_items.keys()
        if key in all_items
    }


@router.post("/reset/{key}", response_model=ConfigResetResponse)
async def reset_config_item(key: str, db=Depends(get_db)):
    """重置配置项为默认值（删除数据库覆盖）"""
    validate_editable(key)

    # 删除数据库记录
    config = get_config_from_db(db, key)

    if not config:
        return ConfigResetResponse(
            key=key,
            message="No database override found, already using default/env value",
            new_value=None,
        )

    db.delete(config)
    db.commit()

    # 重新加载配置
    reload_settings(db)

    # 获取新的有效值
    settings = get_settings()
    new_value = settings.get_effective_value(key)

    # 如果是敏感信息，返回掩码值
    display_value = mask_sensitive_value(key, str(new_value) if new_value else None)

    logger.info(f"Configuration reset: {key}")

    return ConfigResetResponse(
        key=key,
        message="Configuration reset to default/env value",
        new_value=display_value,
    )


@router.get("/status")
async def get_config_status(db=Depends(get_db)):
    """获取配置系统状态"""
    settings = get_settings()

    # 统计各来源的配置数量
    db_count = db.query(SystemConfig).count()

    all_items = settings.to_config_items(mask_sensitive=False)
    env_count = sum(1 for item in all_items.values() if item["source"] == "env")
    default_count = sum(1 for item in all_items.values() if item["source"] == "default")

    return {
        "initialized_from_db": settings._initialized_from_db,
        "database_overrides_count": db_count,
        "env_values_count": env_count,
        "default_values_count": default_count,
        "sensitive_keys": SENSITIVE_KEYS,
        "non_editable_keys": NON_EDITABLE_KEYS,
    }