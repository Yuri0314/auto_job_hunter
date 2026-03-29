# Auto Job Hunter 产品重设计方案

**日期**: 2026-03-29
**定位**: 开源产品，需要完整度、清晰架构、可扩展性

---

## 问题分析

### 功能层面问题

1. **搜索策略不智能**: 简历解析出多个技能关键词，但搜索只支持单一关键词手动输入，无法自动组合关键词搜索不同职位变体
2. **投递后跟踪缺失**: 投递后流程结束，缺少状态追踪、HR回复提醒、面试邀约处理
3. **简历管理单薄**: 只能上传解析，不支持多简历管理、版本切换、结果编辑修正

### 交互层面问题

1. **重复操作太多**: 每次手动输入关键词、城市、重复相同搜索条件
2. **结果处理不够深入**: 投递结果只是列表展示，没有统计、筛选、导出等后续操作
3. **步骤引导不明显**: 用户不清楚下一步该做什么，系统状态不直观

---

## 设计方案

### 改动方案选择

**方案2: 全面重构（产品驱动重构）**

从用户旅程出发，重新设计核心流程和功能模块，再重构实现。

理由:
- 开源产品需要完整产品感，碎片化改进难以达到
- 核心问题涉及整体流程，局部修补难以根本解决
- 现有代码量不大，重构成本可控

分阶段执行:
- 第一阶段: 核心模块改进 + 简化版仪表盘
- 第二阶段: 职位管理、消息中心等高级功能

---

## 核心架构设计

### 双模式架构

支持两种运行模式，保持扩展性:

```
                    ┌──────────────────┐
                    │   配置选择入口    │
                    │ 选择运行模式      │
                    └──────────────────┘
                            ↓
            ┌───────────────┴───────────────┐
            ↓                               ↓
    ┌───────────────┐               ┌───────────────┐
    │   人工模式     │               │   AI自动模式   │
    │  (步骤引导)    │               │  (一键执行)    │
    └───────────────┘               └───────────────┘
            ↓                               ↓
    用户手动控制每一步              AI自动决策和执行
    - 手动搜索                      - 自动生成搜索策略
    - 手动筛选职位                  - AI匹配度分析
    - 手动选择投递                  - 自动投递高分职位
    - 手动回复                      - AI自动回复HR
            ↓                               ↓
            └───────────────┬───────────────┘
                            ↓
                    ┌──────────────────┐
                    │   共享的跟踪层    │
                    │ 投递状态追踪      │
                    │ HR消息通知        │
                    └──────────────────┘
```

### 运行模式定义

```python
UserProfile.strategy = "manual" | "ai_assisted" | "ai_full_auto"

# 模式特点
manual:        每步需用户确认，界面引导式
ai_assisted:   AI推荐，用户确认关键决策
ai_full_auto:  AI全自动执行，用户只看结果
```

---

## 用户旅程设计

### 新流程

```
用户旅程: 发现 → 准备 → 搜索 → 决策 → 投递 → 跟踪 → 优化

[仪表盘] 系统状态一目了然
 - 平台登录状态、简历状态、今日投递数、待处理消息

[准备] 简历智能解析
 - 多格式支持: PDF, Word, Markdown, 纯文本
 - 双引擎: 规则引擎(默认) + AI引擎(可选)
 - 解析结果可编辑修正
 - 多简历管理

[搜索] 智能多关键词搜索
 - 根据简历技能组合自动生成搜索词
 - 多平台并行搜索
 - 自动过滤 + 人工筛选

[决策] 职位管理面板
 - 职位详情查看、收藏、比较
 - 匹配度评分显示(AI模式)
 - 批量选择投递

[投递] 执行 + 结果反馈
 - 进度实时显示
 - 成功/失败详情
 - 问题职位标记

[跟踪] 投递后生命周期管理
 - HR回复提醒
 - 面试邀约处理
 - 状态变化追踪
```

---

## 核心模块设计

### 1. 简历解析模块

```
多格式支持:
- PDF (现有)
- Word (.docx)
- Markdown (.md)
- 纯文本 (.txt)
- 富文本粘贴 (用户直接粘贴简历内容)

解析引擎选择:
┌───────────────────────────────────────────────┐
│ 规则引擎 (默认，无成本)                        │
│  - 正则提取邮箱、电话                          │
│  - 关键词匹配技能、学历                        │
│  - 模板化提取结构信息                          │
└───────────────────────────────────────────────┘
┌───────────────────────────────────────────────┐
│ AI引擎 (可选，需要配置API Key)                 │
│  - LLM深度理解简历语义                         │
│  - 自动识别技能栈、项目经验                     │
│  - 推断目标岗位、薪资期望                       │
│  - 生成搜索策略建议                             │
└───────────────────────────────────────────────┘

解析结果编辑:
- 结构化结果展示
- 用户可编辑每个字段
- 补充/删除技能标签
- 调整目标职位和城市偏好
- 保存时验证必填字段

多简历管理:
- 支持保存多份简历
- 每份简历可设置不同目标岗位
- 搜索时可选择使用哪份简历
- 简历版本历史记录
```

数据结构:
```python
class Resume:
    id: int
    name: str                    # 文件名
    file_path: str               # 原始文件路径
    file_type: str               # "pdf" | "docx" | "md" | "txt" | "paste"
    parse_engine: str            # "rule" | "ai"
    created_at: datetime
    updated_at: datetime
    is_primary: bool             # 是否主简历

class ResumeProfile:
    resume_id: int
    # 基本信息
    name: str
    phone: str
    email: str

    # 职业信息
    experience_years: int
    current_position: str
    target_positions: List[str]   # 多个目标岗位

    # 技能标签 (可编辑)
    skills: List[str]
    soft_skills: List[str]

    # 其他
    education: str
    city: str
    preferred_cities: List[str]   # 多个意向城市
    salary_min: int
    salary_max: int

    # AI生成建议 (如果使用AI引擎)
    ai_search_suggestions: List[str]
    ai_match_summary: str
```

### 2. 搜索策略模块

```
搜索策略生成:
- 从技能组合生成搜索关键词
- 例: [Python, Django, FastAPI]
  → "Python后端", "Django开发", "FastAPI工程师"
- 从目标职位生成变体搜索词
- 例: 目标"后端工程师"
  → "后端开发", "服务端工程师", "Backend Engineer"
- 组合权重排序 (核心技能优先)

搜索策略数据结构:
class SearchStrategy:
    primary_keywords: List[str]     # 核心关键词 ["Python后端"]
    variant_keywords: List[str]    # 变体关键词 ["Django开发", "FastAPI"]
    skill_combinations: List[str]  # 技能组合 ["Python Django", "Python FastAPI"]
    cities: List[str]              # 意向城市
    salary_range: Tuple[int, int]  # 薪资期望
    priority: int                  # 搜索优先级
```

### 3. 搜索执行模块

```
搜索执行流程:
┌─────────────────────────────────────────────────────┐
│ 搜索任务队列                                         │
│  - 按搜索策略生成多个搜索任务                        │
│  - 任务优先级排序                                    │
│  - 并行执行控制 (限制并发数)                         │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ 平台并行搜索                                         │
│  - Boss直聘、猎聘 同时执行                          │
│  - 每个平台: 多关键词并行                            │
│  - 结果去重与合并                                    │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ 结果处理                                             │
│  - 初步过滤 (城市、薪资硬性条件)                     │
│  - 模式分流:                                        │
│    · 人工模式: 进入职位池待用户筛选                  │
│    · AI模式: 直接进行匹配度分析                      │
└─────────────────────────────────────────────────────┘
```

### 4. 职位管理模块

```
职位生命周期:
┌─────────────────────────────────────────────────────┐
│ 搜索结果池                                           │
│  - 所有平台搜索结果汇总                              │
│  - 基本过滤 (城市、薪资硬条件)                       │
│  - 待用户进一步处理                                  │
└─────────────────────────────────────────────────────┘
         ↓ 用户筛选/AI评分
┌─────────────────────────────────────────────────────┐
│ 职位候选池                                           │
│  - 用户感兴趣/AI评分达标的职位                       │
│  - 支持收藏、标记、排序                              │
│  - 匹配度评分 (AI模式)                               │
│  - 状态: pending | starred | rejected              │
└─────────────────────────────────────────────────────┘
         ↓ 用户选择投递
┌─────────────────────────────────────────────────────┐
│ 投递队列                                             │
│  - 用户确认要投递的职位                              │
│  - 优先级排序                                        │
│  - 打招呼语预览/编辑                                 │
│  - 状态: queued | submitting | submitted | failed  │
└─────────────────────────────────────────────────────┘
```

职位详情视图:
```
职位详情页:
┌───────────────────────────────────────────────┐
│ 职位标题: Python高级工程师                     │
│ 公司: XXX科技 · 规模100-500人 · 行业互联网     │
│ 薪资: 25-40K · 城市: 北京                      │
│ 经验: 3-5年 · 学历: 本科                       │
└───────────────────────────────────────────────┘
┌───────────────────────────────────────────────┐
│ HR信息                                         │
│ 姓名: 张经理 · 在线状态: ●                     │
│ 最近活跃: 10分钟前                              │
└───────────────────────────────────────────────┘
┌───────────────────────────────────────────────┐
│ 职位描述 (可展开详情)                           │
│ 职责: 后端系统开发、API设计、数据库优化...      │
│ 要求: Python、Django/FastAPI、MySQL、Redis...  │
└───────────────────────────────────────────────┘
┌───────────────────────────────────────────────┐
│ 匹配分析 (AI模式)                               │
│ 匹配度: 85分                                    │
│ ✓ 技能匹配: Python, FastAPI                    │
│ ✓ 经验匹配: 4年符合3-5年要求                   │
│ ○ 建议提升: 分布式系统经验                      │
└───────────────────────────────────────────────┘

[收藏] [投递] [忽略] [查看原链接]
```

### 5. 投递跟踪模块

```
投递状态追踪:
状态: 已投递 → HR已读 → HR回复 → 面试邀约

○ submitted   提交成功
○ read        HR已查看简历
○ replied     HR已回复
○ interview   面试邀约
○ rejected    不合适
○ expired     职位已关闭

消息监控:
- 定时拉取各平台HR消息
- 新消息通知提醒
- 消息分类: 回复、面试邀约、拒绝
- 支持手动回复 或 AI自动回复

数据统计:
- 今日投递数
- 本周投递数
- HR回复率
- 面试邀约数
- 平台分布统计
- 导出投递记录 (CSV)
```

---

## UI设计

### 仪表盘设计

```
┌─────────────────────────────────────────────────────────┐
│ ⚡ AUTO_JOB_HUNTER                            [设置]   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 系统状态总览                                             │
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ BOSS    │ │ 猎聘    │ │ 简历    │ │ 今日    │       │
│  │ ● 已登录│ │ ○ 未登录│ │ ✓ 已解析│ │ 投递: 5 │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│                                                         │
│  [一键求职] → 点击后自动执行:搜索→过滤→投递(需配置)     │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 快速操作                                                 │
│                                                         │
│  [搜索职位]  [管理简历]  [投递记录]  [消息中心]         │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 今日投递概览                                             │
│                                                         │
│  职位                    公司         状态     时间      │
│  Python高级工程师        XX科技      HR已读    10:30    │
│  后端开发工程师          YY公司      已投递    09:15    │
│  FastAPI工程师           ZZ互联网    HR回复    昨天      │
│                                                         │
│  [查看全部投递记录]                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 待处理消息                                               │
│                                                         │
│  🔔 BOSS直聘: 张经理回复了你的消息                       │
│  🔔 猎聘: 收到面试邀约 - AAA公司                         │
│                                                         │
│  [查看全部消息]                                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 导航结构

```
导航层级:

仪表盘
├── 搜索职位
│   ├── 搜索条件设置 (关键词、城市、平台)
│   ├── 搜索执行 (实时进度)
│   └── 结果筛选 (职位池 → 勾选投递)
│
├── 管理简历
│   ├── 简历列表 (多简历管理)
│   ├── 上传新简历
│   └── 编辑简历信息
│
├── 投递记录
│   ├── 记录列表 (筛选、搜索)
│   ├── 状态详情
│   └── 导出记录
│
├── 消息中心
│   ├── 未读消息
│   ├── 全部消息
│   └── 消息回复
│
└── 设置
    ├── 平台账号 (登录管理)
    ├── AI配置 (API Key、模型选择)
    ├── 策略配置 (运行模式、过滤规则)
    └── 系统设置
```

### UI设计规范 (Obsidian Terminal风格)

```
色彩系统:
- 背景: #050508 (深黑)
- 卡片: rgba(18, 18, 26, 0.8) (半透明深灰)
- 主强调: #00d4ff (电蓝) - 活跃状态、操作按钮
- 成功: #4ade80 (绿) - 已完成、已登录
- 警告: #fbbf24 (金) - 待处理、需关注
- 失败: #f87171 (红) - 失败、未登录

状态指示:
- ● 已登录/已完成
- ○ 未登录/待完成
- ✓ 成功
- ✗ 失败
- → 下一步引导

字体:
- 标题: JetBrains Mono (代码感)
- 正文: DM Sans (清晰易读)
- 数字/状态: JetBrains Mono

交互反馈:
- 按钮: 悬停时发光效果
- 状态变化: 颜色渐变过渡
- 加载: 蓝色脉冲动画
- 成功: 绿色闪现确认
```

---

## 后端架构调整

### 模块划分

```
backend/
├── core/
│   ├── resume/
│   │   ├── parser_base.py      # 解析基类
│   │   ├── rule_parser.py      # 规则引擎
│   │   ├── ai_parser.py        # AI引擎
│   │   └── strategy_gen.py     # 搜索策略生成
│   │
│   ├── search/
│   │   ├── strategy.py         # 搜索策略
│   │   ├── executor.py         # 搜索执行
│   │   └── aggregator.py       # 结果聚合
│   │
│   ├── job/
│   │   ├── manager.py          # 职位管理
│   │   ├── matcher.py          # 匹配分析(AI)
│   │   └── pool.py             # 职位池
│   │
│   ├── application/
│   │   ├── tracker.py          # 投递跟踪
│   │   ├── message_monitor.py  # 消息监控
│   │   └── stats.py            # 数据统计
│   │
│   └── config/
│   │   └── settings.py         # 配置管理
│   │   └── strategy.py         # 运行模式配置
│   │
│   └── database/
│   │   ├── models.py           # 数据模型 (扩展)
│   │   └── session.py
│   │
├── adapters/
│   ├── base_adapter.py
│   ├── boss_adapter.py
│   └── liepin_adapter.py
│   └── [可扩展其他平台]
│
├── agents/
│   └── ai/
│   │   ├── ai_service.py       # AI服务
│   │   ├── resume_analyzer.py  # 简历分析
│   │   ├── job_matcher.py      # 职位匹配
│   │   └── greeting_gen.py     # 打招呼生成
│   │   └── reply_gen.py        # 回复生成
│
├── api/
│   ├── dashboard.py            # 仪表盘API
│   ├── resume.py               # 简历管理API
│   ├── search.py               # 搜索API
│   ├── jobs.py                 # 职位管理API
│   ├── applications.py         # 投递API
│   ├── messages.py             # 消息API
│   ├── settings.py             # 设置API
│   └── system.py               # 系统状态API
│
├── services/
│   └── orchestrator.py         # 主协调器 (调整职责)
│
└── main.py
```

### Orchestrator职责调整

现有 Orchestrator 承担过多职责，需要拆分:

```
Orchestrator (调整后):
- 不再直接处理简历解析 → 由 ResumeService 处理
- 不再直接执行搜索 → 由 SearchExecutor 处理
- 不再直接管理投递 → 由 ApplicationTracker 处理

新职责:
- 协调各子服务
- 管理全局状态
- 处理跨模块流程
- 提供一键执行入口
```

---

## 数据模型扩展

```python
# 新增/修改的模型

class Resume(Base):
    __tablename__ = "resumes"
    id: int
    name: str
    file_path: str
    file_type: str               # "pdf" | "docx" | "md" | "txt" | "paste"
    parse_engine: str            # "rule" | "ai"
    created_at: datetime
    updated_at: datetime
    is_primary: bool
    profile: relationship("ResumeProfile")

class ResumeProfile(Base):
    __tablename__ = "resume_profiles"
    id: int
    resume_id: int
    name: str
    phone: str
    email: str
    experience_years: int
    current_position: str
    target_positions: JSON       # List[str]
    skills: JSON                 # List[str]
    soft_skills: JSON            # List[str]
    education: str
    city: str
    preferred_cities: JSON       # List[str]
    salary_min: int
    salary_max: int
    ai_search_suggestions: JSON  # List[str]
    ai_match_summary: str

class SearchStrategy(Base):
    __tablename__ = "search_strategies"
    id: int
    resume_id: int               # 关联简历
    primary_keywords: JSON       # List[str]
    variant_keywords: JSON       # List[str]
    skill_combinations: JSON     # List[str]
    cities: JSON                 # List[str]
    salary_min: int
    salary_max: int
    priority: int
    created_at: datetime

class Job(Base):
    # 扩展字段
    pool_status: str             # "pending" | "starred" | "rejected" | "queued"
    match_score: int             # AI匹配度分数
    match_details: JSON          # 匹配分析详情
    starred_at: datetime         # 收藏时间

class Application(Base):
    # 扩展字段
    status: str                  # "submitted" | "read" | "replied" | "interview" | "rejected" | "expired"
    status_updated_at: datetime
    greeting_used: str           # 使用的打招呼语

class Message(Base):
    __tablename__ = "messages"
    id: int
    application_id: int          # 关联投递记录
    platform: str
    hr_name: str
    content: str
    direction: str               # "in" | "out"
    is_unread: bool
    received_at: datetime
    message_type: str            # "reply" | "interview" | "reject" | "other"
    ai_reply: str                # AI生成的回复建议

class UserProfile(Base):
    # 扩展字段
    strategy: str                # "manual" | "ai_assisted" | "ai_full_auto"
    primary_resume_id: int       # 主简历ID
```

---

## 实施阶段

### 第一阶段: 核心模块改进 + 简化版仪表盘

1. **简历解析模块重构**
   - 多格式支持
   - 解析结果可编辑
   - 搜索策略生成
   - 多简历管理

2. **搜索执行模块改进**
   - 多关键词并行搜索
   - 搜索策略应用

3. **仪表盘基础版**
   - 系统状态总览
   - 快速操作入口
   - 今日投递概览

4. **数据模型扩展**
   - Resume/ResumeProfile
   - SearchStrategy
   - Job/Application扩展字段

### 第二阶段: 高级功能

1. **职位管理面板**
   - 职位候选池
   - 职位详情视图
   - 匹配度分析(AI)

2. **投递跟踪模块**
   - 状态追踪
   - 消息监控
   - 数据统计

3. **消息中心**
   - 消息列表
   - 消息回复(AI)

4. **AI自动模式**
   - 全自动执行
   - AI回复生成

---

## 开放问题

(无)