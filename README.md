# Auto Job Hunter - AI自动求职系统

## 项目简介

基于AI Agent技术的自动化求职系统，支持智能简历生成、多平台职位搜索、自动投递和HR消息回复。

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **AI框架**: LangChain + LangGraph
- **前端**: Streamlit (原型) + React (生产)
- **数据库**: SQLite (开发) + PostgreSQL (生产)
- **任务调度**: APScheduler + Celery
- **部署**: Docker + Kubernetes

## 项目结构

```
auto_job_hunter/
├── backend/                 # 后端服务
│   ├── agents/             # AI智能体
│   │   ├── orchestrator/   # 主控协调智能体
│   │   ├── resume/         # 简历生成智能体
│   │   ├── job_search/     # 职位搜索智能体
│   │   ├── application/    # 投递智能体
│   │   └── messaging/      # 消息回复智能体
│   ├── core/               # 核心功能
│   │   ├── config/         # 配置管理
│   │   ├── database/       # 数据库模型
│   │   ├── security/       # 安全认证
│   │   └── utils/          # 工具函数
│   ├── platforms/          # 平台适配器
│   │   ├── base/           # 基础适配器
│   │   ├── boss/           # BOSS直聘
│   │   ├── liepin/         # 猎聘
│   │   └── maimai/         # 脉脉
│   ├── api/                # API接口
│   │   ├── routes/         # 路由定义
│   │   └── schemas/        # 数据模型
│   └── main.py             # 应用入口
├── frontend/               # 前端应用
│   ├── streamlit_app/      # Streamlit原型
│   └── react_app/          # React生产版本
├── tests/                  # 测试代码
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── e2e/                # 端到端测试
├── docs/                   # 项目文档
│   ├── api/                # API文档
│   ├── architecture/       # 架构设计
│   └── user_guide/         # 用户指南
├── deployment/             # 部署配置
│   ├── docker/             # Docker配置
│   ├── kubernetes/         # K8s配置
│   └── scripts/            # 部署脚本
├── requirements.txt        # Python依赖
├── pyproject.toml         # 项目配置
└── README.md              # 项目说明
```

## 核心功能

### 1. 简历智能生成
- 用户画像分析
- AI简历优化
- 多格式输出（PDF、Word、HTML）
- 职位匹配优化

### 2. 职位智能搜索
- 多平台聚合搜索
- AI职位匹配
- 智能筛选推荐
- 实时职位更新

### 3. 自动化投递
- 批量投递
- 智能投递策略
- 投递状态跟踪
- 避免重复投递

### 4. HR消息回复
- 消息自动监听
- AI智能回复
- 个性化应答
- 多平台支持

## 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 15+ (生产环境)
- Redis 7+ (可选)

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/yourusername/auto_job_hunter.git
cd auto_job_hunter

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入必要的配置

# 初始化数据库
python scripts/init_db.py

# 启动服务
python -m backend.main
```

## 配置说明

详见 [配置文档](docs/configuration.md)

## API文档

启动服务后访问: http://localhost:8000/docs

## 开发指南

详见 [开发文档](docs/development.md)

## 贡献指南

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md)

## 许可证

MIT License

## 联系方式

- 项目主页: https://github.com/yourusername/auto_job_hunter
- 问题反馈: https://github.com/yourusername/auto_job_hunter/issues