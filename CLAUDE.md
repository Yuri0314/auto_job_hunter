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
python run.py web              # FastAPI后端 (port 8000)
streamlit run frontend/app.py  # 前端GUI (port 8501)
python run.py gui              # 一键启动后端+前端

# CLI使用
python run.py search -k "Python后端" -p boss liepin -c 北京
python run.py search -k "Python" -p boss --ai -a  # AI模式+自动投递

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

## Streamlit Loading模式

显示loading时必须用全局状态完全遮挡旧内容，否则旧按钮仍可点击：

```python
if st.session_state.loading:
    # 全屏loading遮挡，不渲染任何其他内容
    st.markdown("<div style='position:fixed;top:0;left:0;right:0;bottom:0;z-index:9999'>...</div>")
    # 执行任务
    st.session_state.loading = False
    st.rerun()
else:
    # 正常渲染页面
```

**不要用 `st.spinner()`** - 它无法阻止旧内容渲染。

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