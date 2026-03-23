# Auto Job Hunter - 架构设计补充文档

## 一、架构对比分析

### 1.1 get_jobs项目核心特性

基于对 get_jobs 项目的深入分析，发现以下关键设计：

| 模块 | get_jobs实现 | 重要程度 |
|------|--------------|----------|
| 浏览器自动化 | Playwright + Stealth反检测 | 🔴 关键 |
| Cookie管理 | 持久化存储，自动登录 | 🔴 关键 |
| 黑名单系统 | 公司/HR/职位三级过滤 | 🟡 重要 |
| 配置管理 | 数据库存储 + Web GUI | 🟡 重要 |
| AI服务 | 多模型支持 + 自动降级 | 🟡 重要 |
| 消息通知 | 企业微信推送 | 🟢 可选 |
| 日志系统 | 完整记录 + 文件存储 | 🟢 可选 |

### 1.2 需要补充的功能模块

#### 1.2.1 浏览器自动化层 (新增)
```
backend/automation/
├── browser/
│   ├── playwright_manager.py    # Playwright浏览器管理
│   ├── stealth.py              # 反检测脚本
│   └── cookie_manager.py       # Cookie持久化
├── interaction/
│   ├── human_simulator.py      # 人机交互模拟
│   └── captcha_solver.py       # 验证码处理
└── utils/
    ├── screenshot.py           # 截图工具
    └── wait_utils.py           # 等待机制
```

#### 1.2.2 黑名单过滤系统 (新增)
```
backend/core/filter/
├── blacklist_service.py        # 黑名单服务
├── company_filter.py           # 公司过滤
├── hr_filter.py                # HR过滤
└── job_filter.py               # 职位过滤
```

#### 1.2.3 配置中心 (增强)
```
backend/core/config/
├── settings.py                 # 环境变量配置
├── db_config_service.py        # 数据库配置服务
└── config_validator.py         # 配置验证
```

#### 1.2.4 AI服务增强 (增强)
```
backend/agents/ai/
├── multi_model_service.py      # 多模型支持
├── prompt_template_manager.py  # 提示词模板
├── cost_tracker.py             # 成本追踪
└── auto_fallback.py            # 自动降级
```

## 二、技术栈补充

### 2.1 新增依赖

```python
# 浏览器自动化
playwright==1.41.0              # 替代Selenium
undetected-chromedriver==3.5.4  # 反检测驱动

# 反爬虫
fake-useragent==1.4.0           # User-Agent池
stem==1.8.0                     # Tor支持（可选）

# 配置管理
pydantic==2.5.3                 # 已有
python-dotenv==1.0.0            # 已有

# 日志增强
loguru==0.7.2                   # 已有
sentry-sdk==1.40.0              # 错误追踪（可选）

# 消息推送（可选）
requests==2.31.0                # 已有
```

### 2.2 技术选择对比

| 需求 | get_jobs方案 | 推荐方案 | 理由 |
|------|--------------|----------|------|
| 浏览器自动化 | Playwright | Playwright | 更稳定，原生反检测支持 |
| 数据库 | SQLite | SQLite开发 + PostgreSQL生产 | 保持一致 |
| AI调用 | HTTP Client | LangChain | 更易扩展，支持多模型 |
| 配置管理 | 数据库 + 环境变量 | 环境变量 + 数据库 | 优先环境变量，便于部署 |
| 日志 | Logback | Loguru | Python生态更好 |

## 三、风险评估

### 3.1 平台反爬虫风险

| 平台 | 风险等级 | get_jobs状态 | 应对策略 |
|------|----------|--------------|----------|
| Boss直聘 | 🔴 高 | 有问题 | 模拟真实用户行为，限制频率 |
| 猎聘 | 🟢 低 | 正常 | 常规自动化即可 |
| 前程无忧 | 🟡 中 | 有限制 | 控制投递速度 |
| 脉脉 | 🟡 中 | 未支持 | 需要研究 |

### 3.2 账号安全建议

1. **使用小号测试**：先用不重要的账号测试
2. **控制投递频率**：模拟人类操作节奏
3. **Cookie定期更新**：避免长期使用同一身份
4. **IP轮换**：如有必要，使用代理池

## 四、待确认问题

### 4.1 功能优先级
- [ ] 是否需要Web GUI管理界面？
- [ ] Cookie持久化是否必要？
- [ ] 黑名单系统优先级？

### 4.2 平台策略
- [ ] Boss直聘的封号风险接受度？
- [ ] 是否只支持本地运行？
- [ ] 平台扩展优先级？

### 4.3 AI集成
- [ ] AI功能的重要程度？
- [ ] 是否需要多模型支持？
- [ ] 成本控制需求？

---

**更新时间**: 2026-03-24
**状态**: 待用户确认