# 数据库迁移

此目录存放数据库迁移脚本。

## 迁移脚本命名规范

使用 `NNN_description.py` 格式，例如：
- `001_add_resume_models.py`
- `002_add_message_indexes.py`

## 执行迁移

### 方式一：使用 SQLAlchemy（当前方式）

```python
from backend.core.database import Base, engine
from backend.core.database.models import Resume, ResumeProfile, SearchStrategy
Base.metadata.create_all(bind=engine)
```

### 方式二：使用 Alembic（未来）

```bash
# 初始化 Alembic（仅首次）
alembic init migrations

# 生成迁移脚本
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head
```

## 当前迁移记录

| 版本 | 描述 | 日期 |
|------|------|------|
| 001 | 添加简历相关表和字段 | 2026-03-29 |