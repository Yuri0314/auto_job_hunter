# Auto Job Hunter - Claude Code 配置

## 项目概述

这是一个基于AI Agent技术的自动化求职系统，支持智能简历生成、多平台职位搜索、自动投递和HR消息回复。

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **AI框架**: LangChain + LangGraph
- **前端**: Streamlit (原型) + React (生产)
- **数据库**: SQLite (开发) + PostgreSQL (生产)

## 编码规范

### Python代码规范
- 使用 Python 3.11+
- 遵循 PEP 8 编码风格
- 使用类型注解 (Type Hints)
- 使用 Black 进行代码格式化
- 使用 isort 进行 import 排序

### 代码结构
- 每个模块应该有明确的职责
- 使用依赖注入模式
- 遵循 SOLID 原则
- 保持函数简短，单一职责

### 命名规范
- 变量名: snake_case
- 类名: PascalCase
- 常量: UPPER_SNAKE_CASE
- 私有方法: _leading_underscore

## 架构设计

### AI Agent架构
```
Orchestrator Agent (主控)
├── Resume Agent (简历生成)
├── Job Search Agent (职位搜索)
├── Application Agent (投递)
└── Messaging Agent (消息回复)
```

### 平台适配器
- `platforms/base/` - 基础适配器接口
- `platforms/boss/` - BOSS直聘
- `platforms/liepin/` - 猎聘
- `platforms/maimai/` - 脉脉

## 开发指南

### 环境设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

### 测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_resume_agent.py

# 生成覆盖率报告
pytest --cov=backend tests/
```

### 代码质量
```bash
# 格式化代码
black .

# 检查代码风格
flake8 .

# 类型检查
mypy backend/
```

## 安全注意事项

- 不要在代码中硬编码敏感信息
- 使用环境变量存储API密钥和密码
- 对用户数据进行加密存储
- 实现适当的访问控制

## Git提交规范

- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具

## 注意事项

- 招聘平台有反爬虫机制，请谨慎操作
- 自动化操作可能违反平台使用协议
- 建议使用半自动模式，需要用户确认
- 遵守相关法律法规