# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于AI Agent技术的自动化求职系统，支持多平台职位搜索、自动投递和HR消息回复。

**核心架构：**
```
Frontend (NiceGUI @ /ui) ──同进程──→ FastAPI API (/api/*)
                                         ↓
                                   Orchestrator (backend/services/)
                                         ↓
              ┌──────────────────────────┼──────────────────────────┐
              ↓                          ↓                          ↓
        AI Service              Filter Service              Platform Adapters
    (backend/agents/ai/)     (backend/core/filter/)      (backend/adapters/)
    OpenAI/Ollama            简单模式/智能模式             BossAdapter/LiepinAdapter
                                                              ↓
                                                    Browser Automation
                                               (Playwright + Stealth)
                                               单例模式: get_browser_manager()
```

**数据流：** Job → Filter → Application → Message，所有状态存储在SQLite/PostgreSQL。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 初始化数据库
python run.py init

# 启动服务（默认模式，浏览器功能完整可用）
python run.py                    # 一键启动并打开浏览器
python run.py --port 8080        # 指定端口
python run.py --no-browser       # 不自动打开浏览器

# 开发模式（热重载，但浏览器自动化功能不可用）
python run.py --reload           # 热重载开发模式

# CLI搜索
python run.py search -k "Python后端" -p boss liepin -c 北京
python run.py search -k "Python" -p boss --ai -a  # AI模式+自动投递

# 访问地址
http://localhost:8000/ui/dashboard   # NiceGUI 前端入口
http://localhost:8000/docs           # Swagger API 文档

# 测试
pytest tests/                        # 全部测试
pytest tests/unit/test_config.py -v  # 单个测试文件
pytest --cov=backend tests/          # 带覆盖率

# 代码质量
black backend/ && isort backend/

# 调试脚本 (Playwright浏览器自动化)
python tests/debug_page_structure.py    # 页面结构分析
python tests/debug_api_interception.py  # API拦截调试
```

## 核心架构

### 双模式策略

- **简单模式**: 基于规则的关键词/城市/薪资过滤，无AI成本
- **智能模式**: AI匹配度分析(70+分投递)，个性化打招呼语

### Orchestrator (主协调器)

`backend/services/orchestrator.py` 是核心协调器，编排所有Agent。关键方法：
- `search_jobs()` → 调用平台适配器搜索
- `filter_jobs()` → 简单模式或AI模式过滤
- `apply_jobs()` → 执行投递并记录
- `run_job_search_cycle()` → 完整搜索周期（搜索→过滤→投递）

获取单例: `await get_orchestrator(use_ai=True/False)`

### 平台适配器接口

所有适配器继承 `BasePlatformAdapter` (`backend/adapters/base_adapter.py`)。

**添加新平台步骤：**
1. 创建 `backend/adapters/xxx_adapter.py`
2. 继承 `BasePlatformAdapter`，实现所有 `@abstractmethod`
3. 在 `backend/adapters/__init__.py` 注册到 `get_adapter()`

### 浏览器管理 (Playwright)

`backend/automation/browser/playwright_manager.py` 使用单例模式：
```python
from backend.automation.browser import get_browser_manager
browser = get_browser_manager()  # 单例，headless=False
page = await browser.get_page()
```

**重要：** 浏览器始终使用有界面模式 (`headless=False`) 以避免反爬检测。

### 关键API端点

| 端点 | 说明 |
|------|------|
| `/api/system/login/{platform}` | 平台登录 (POST) |
| `/api/system/platforms` | 平台状态 (GET) |
| `/api/resume/status` | 简历状态 (GET) |
| `/api/resume/download` | 简历下载 (GET) |
| `/api/settings/items` | 配置项 (GET) |
| `/api/user/profile` | 用户画像 (GET/PUT) |
| `/api/search/execute` | 执行搜索 (POST) |

**注意:** 登录API是 `/system/login` 不是 `/auth/login`。

## Windows 兼容性

Playwright在Windows上需要 `WindowsProactorEventLoopPolicy` 支持子进程：

```python
# tests/conftest.py 和 backend/cli.py 中已配置
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

**注意：** `backend/main.py` 使用 `ProactorEventLoopPolicy`，但 `run_web()` 使用 `SelectorEventLoopPolicy` 以支持 uvicorn reload。

## SQLAlchemy Session 使用

避免 `DetachedInstanceError`，正确模式：
```python
db = SessionLocal()
try:
    # 在 session 内完成所有数据库操作
    job = db.query(Job).filter(...).first()
    job.status = JobStatus.APPLIED  # 在 session 内修改
    db.commit()
finally:
    db.close()  # 关闭后 job 对象变成 detached，无法再访问关系属性
```

**错误示例：** 在 session 关闭后访问 `job.applications` 等关系属性会报错。

## NiceGUI 前端

前端使用 NiceGUI 框架，挂载在 `/ui` 路径下。入口文件: `frontend_nicegui/app.py`。

**主要页面：**
- `/ui/dashboard` - 仪表盘
- `/ui/resumes` - 简历管理
- `/ui/search` - 职位搜索
- `/ui/settings` - 系统设置

**开发注意：**
- NiceGUI 页面函数在 `@ui.page()` 调用的函数内执行，UI元素必须在页面上下文中创建
- `frontend_nicegui/styles.py` 定义全局CSS和颜色变量
- 页面组件在 `frontend_nicegui/pages/` 目录
- 共用组件在 `frontend_nicegui/components/`

## 前端设计风格

偏好暗黑科技风格 (Obsidian Terminal)：
- 深黑背景 (#050508)
- 电蓝霓虹强调色 (#00d4ff)
- 金色点缀 (#fbbf24)
- JetBrains Mono 字体

## Git提交规范

- `feat:` 新功能
- `fix:` Bug修复
- `refactor:` 重构
- 不添加 `Co-Authored-By` 署名

## 注意事项

- 招聘平台有反爬机制，控制投递频率(建议5秒+间隔)
- BOSS直聘风险较高，建议用小号测试
- 修复后先自己测试验证，再让用户刷新