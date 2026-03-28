# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于AI Agent技术的自动化求职系统，支持多平台职位搜索、自动投递和HR消息回复。

**核心架构：**
```
Frontend (Streamlit)
    ↓ HTTP
Backend (FastAPI)
    ↓
Orchestrator (主协调器)
    ├── AI Service (可选 - OpenAI/Ollama)
    ├── Filter Service (简单/智能模式)
    └── Platform Adapters (Boss, Liepin)
        └── Browser Automation (Playwright + Stealth)
```

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 初始化数据库
python run.py init

# 启动服务
python run.py web              # FastAPI后端
streamlit run frontend/app.py # 前端GUI

# CLI使用
python run.py search -k "Python后端" -p boss liepin -c 北京
python run.py search -k "Python" -p boss --ai -a  # AI模式+自动投递
python run.py daemon -i 60     # 守护进程模式

# 测试与质量检查
pytest tests/
pytest --cov=backend tests/
black backend/
isort backend/
flake8 backend/
mypy backend/
```

## 核心架构

### 双模式策略

- **简单模式**: 基于规则的关键词/城市/薪资过滤，无AI成本
- **智能模式**: AI匹配度分析(70+分投递)，个性化打招呼语

### 平台适配器接口

所有适配器继承 `BasePlatformAdapter` (`backend/adapters/base_adapter.py`)：

```python
class BasePlatformAdapter(ABC):
    async def login(username, password) -> bool
    async def check_login_status() -> bool
    async def search_jobs(keywords, city, salary_range, page) -> SearchResult
    async def apply_job(job_id, greeting, resume_id) -> ApplicationResult
    async def get_messages(unread_only, limit) -> List[Message]
    async def reply_message(message_id, content) -> bool
```

添加新平台：创建 `backend/adapters/xxx_adapter.py`，继承基类，在 `__init__.py` 注册。

### AI服务

支持多提供商 (`backend/agents/ai/ai_service.py`)：
- OpenAI (GPT-4)
- Ollama (本地模型如 llama3)

自动fallback和成本追踪。Prompt模板用于匹配分析和打招呼生成。

### 数据结构

使用dataclasses定义核心数据：
- `JobInfo`: 职位信息
- `FilterConfig`: 过滤规则
- `MatchResult`: AI匹配结果
- `ApplicationResult`: 投递结果

## 编码规范

- Python 3.11+，使用类型注解
- Black格式化(88字符行宽)，isort排序import
- 使用dataclasses而非Pydantic模型
- Async/await贯穿全栈(FastAPI、适配器、AI服务)
- 日志使用 `loguru`

## 数据库模型

SQLAlchemy 2.0，开发用SQLite，生产用PostgreSQL：
- `Job`: 职位缓存
- `Application`: 投递记录
- `Message`: HR消息
- `UserProfile`: 用户画像
- `FilterRule`: 过滤规则
- `SystemConfig`: 系统配置

## Git提交规范

- `feat:` 新功能
- `fix:` Bug修复
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具

## 注意事项

- 招聘平台有反爬机制，控制投递频率(建议5秒+间隔)
- 建议使用半自动模式，关键操作需用户确认
- BOSS直聘风险较高，建议用小号测试
- 遵守相关法律法规