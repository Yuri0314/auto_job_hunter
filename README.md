# Auto Job Hunter - AI自动求职系统

## 项目简介

基于AI Agent技术的自动化求职系统，支持智能简历生成、多平台职位搜索、自动投递和HR消息回复。

**核心特性：**
- ✅ 双模式投递策略：简单模式(无AI) + 智能模式(AI驱动)
- ✅ 多平台支持：BOSS直聘、猎聘、脉脉
- ✅ 浏览器自动化：Playwright + 反检测
- ✅ Cookie持久化：自动登录状态管理
- ✅ Web GUI管理界面：Streamlit + FastAPI

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **AI框架**: LangChain (可选) / OpenAI API
- **浏览器自动化**: Playwright + Stealth
- **前端**: Streamlit
- **数据库**: SQLite (开发) + PostgreSQL (生产)
- **任务调度**: APScheduler

## 项目结构

```
auto_job_hunter/
├── backend/                 # 后端服务
│   ├── adapters/           # 平台适配器
│   │   ├── base_adapter.py # 基础适配器
│   │   ├── boss_adapter.py # BOSS直聘
│   │   └── liepin_adapter.py # 猎聘
│   ├── agents/             # AI智能体
│   │   └── ai/             # AI服务
│   ├── automation/         # 自动化模块
│   │   ├── browser/        # 浏览器管理
│   │   └── interaction/    # 人机模拟
│   ├── api/                # API接口
│   ├── core/               # 核心功能
│   │   ├── config/         # 配置管理
│   │   ├── database/       # 数据库模型
│   │   └── filter/         # 过滤系统
│   ├── services/           # 业务服务
│   │   └── orchestrator.py # 主协调器
│   └── main.py             # 应用入口
├── frontend/               # 前端应用
│   └── app.py              # Streamlit应用
├── docs/                   # 项目文档
├── requirements.txt        # Python依赖
└── README.md              # 项目说明
```

## 核心功能

### 1. 双模式投递策略

**简单模式（无AI）：**
- 基于关键词匹配
- 薪资/城市过滤
- 零成本、速度快

**智能模式（AI驱动）：**
- AI匹配度分析
- 个性化打招呼语
- 持续优化策略

### 2. 多平台支持

| 平台 | 状态 | 功能 |
|------|------|------|
| BOSS直聘 | ✅ 已实现 | 搜索、投递、消息 |
| 猎聘 | ✅ 已实现 | 搜索、投递 |
| 脉脉 | 🔄 规划中 | 待开发 |

### 3. 自动化特性

- **反检测**: Playwright + Stealth脚本
- **Cookie持久化**: 自动保存/加载登录状态
- **人机模拟**: 随机延迟、鼠标轨迹模拟

## 快速开始

### 环境要求

- Python 3.11+
- Playwright浏览器

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/Yuri0314/auto_job_hunter.git
cd auto_job_hunter

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 初始化系统
python run.py init

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入配置
```

### 启动方式

**方式一：Web界面**
```bash
# 启动后端API服务
python run.py web

# 新终端启动前端
streamlit run frontend/app.py
```

**方式二：命令行搜索**
```bash
# 搜索职位
python run.py search -k "Python后端" -p boss liepin -c 北京

# 搜索并自动投递
python run.py search -k "Python" -p boss --ai -a
```

**方式三：守护进程**
```bash
# 后台持续运行
python run.py daemon -i 60
```

## 配置说明

### 环境变量

```bash
# 应用配置
APP_NAME=Auto Job Hunter
DEBUG=false

# 数据库
DATABASE_URL=sqlite:///./auto_job_hunter.db

# AI配置（可选）
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

# 或使用本地模型
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# 平台账号（可选，主要依赖Cookie）
BOSS_USERNAME=your_phone
BOSS_PASSWORD=your_password
LIEPIN_USERNAME=your_phone
LIEPIN_PASSWORD=your_password
```

### 过滤规则配置

在Web界面或API中配置过滤规则：

```json
{
  "name": "Python后端",
  "keywords": ["Python", "后端", "FastAPI"],
  "exclude_keywords": ["外包", "劳务派遣"],
  "salary_range": [15, 30],
  "cities": ["北京", "上海", "深圳"],
  "priority": 1
}
```

## API文档

启动服务后访问: http://localhost:8000/docs

主要API端点：

- `GET /api/jobs` - 获取职位列表
- `POST /api/applications/search-and-apply` - 搜索并投递
- `GET /api/messages` - 获取HR消息
- `PUT /api/user/profile` - 更新用户画像
- `GET /api/system/status` - 系统状态

## 开发指南

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black backend/
isort backend/
```

### 添加新平台

1. 创建 `backend/adapters/xxx_adapter.py`
2. 继承 `BasePlatformAdapter`
3. 实现必要的方法
4. 在 `__init__.py` 中注册

## 注意事项

### 平台风险

| 平台 | 风险等级 | 建议 |
|------|----------|------|
| BOSS直聘 | 🔴 高 | 控制投递频率，使用小号测试 |
| 猎聘 | 🟢 低 | 正常使用即可 |

### 安全建议

1. 使用不重要的账号进行测试
2. 控制投递频率（建议间隔5秒以上）
3. 定期更新Cookie
4. 不要在高峰期大量投递

## 许可证

MIT License

## 联系方式

- 项目主页: https://github.com/Yuri0314/auto_job_hunter
- 问题反馈: https://github.com/Yuri0314/auto_job_hunter/issues