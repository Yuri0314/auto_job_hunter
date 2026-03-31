# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于AI Agent技术的自动化求职系统，支持多平台职位搜索、自动投递和HR消息回复。

**核心架构：**
```
Frontend (NiceGUI @ /ui)
    ↓ 同进程调用
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

# 启动服务（FastAPI + NiceGUI 单服务）
python run.py web              # 后端服务 (port 8000)
python run.py gui              # 一键启动并打开浏览器

# CLI使用
python run.py search -k "Python后端" -p boss liepin -c 北京
python run.py search -k "Python" -p boss --ai -a  # AI模式+自动投递

# 访问地址
http://localhost:8000/ui       # NiceGUI 前端
http://localhost:8000/api/*    # API 端点
http://localhost:8000/docs     # API 文档

# 测试
pytest tests/
pytest tests/unit/test_config.py -v  # 单个测试文件
pytest --cov=backend tests/

# 代码质量
black backend/ && isort backend/
```

## 核心架构

### 双模式策略

- **简单模式**: 基于规则的关键词/城市/薪资过滤，无AI成本
- **智能模式**: AI匹配度分析(70+分投递)，个性化打招呼语

### 平台适配器接口

所有适配器继承 `BasePlatformAdapter` (`backend/adapters/base_adapter.py`)。添加新平台：创建 `backend/adapters/xxx_adapter.py`，继承基类，在 `__init__.py` 注册。

### 关键API端点

| 端点 | 说明 |
|------|------|
| `/api/system/login/{platform}` | 平台登录 (POST) |
| `/api/system/platforms` | 平台状态 (GET) |
| `/api/resume/status` | 简历状态 (GET) |
| `/api/resume/download` | 简历下载 (GET) |
| `/api/settings/items` | 配置项 (GET) |
| `/api/user/profile` | 用户画像 (GET/PUT) |

**注意:** 登录API是 `/system/login` 不是 `/auth/login`。

## Windows 兼容性

Playwright在Windows上需要 `WindowsProactorEventLoopPolicy` 支持子进程：

```python
# tests/conftest.py 和 backend/cli.py 中已配置
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

## NiceGUI 前端

前端使用 NiceGUI 框架，挂载在 `/ui` 路径下。主要页面：
- `/ui/dashboard` - 仪表盘
- `/ui/resumes` - 简历管理
- `/ui/search` - 职位搜索
- `/ui/settings` - 系统设置

**注意:** NiceGUI 页面函数在 `@ui.page()` 装饰器内部执行，UI 元素必须在页面上下文中创建。

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