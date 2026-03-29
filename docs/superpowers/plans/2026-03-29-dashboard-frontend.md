# 仪表盘前端重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构前端为仪表盘导航模式，提供系统状态总览、快速操作入口、今日投递概览

**Architecture:** 仪表盘首页 + 多页面导航 (搜索职位、管理简历、投递记录、消息中心、设置)

**Tech Stack:** Streamlit, requests

**依赖:** 计划1-4 (所有后端模块)

---

## Files Structure

```
frontend/
├── app.py                   # 重构: 仪表盘主页
├── components/
│   ├── __init__.py          # 新增
│   ├── dashboard.py         # 新增: 仪表盘组件
│   ├── sidebar.py           # 新增: 侧边导航
│   ├── styles.py            # 新增: 样式定义
│   └── common.py            # 新增: 公共组件
└── pages/
    ├── __init__.py          # 新增
    ├── search.py            # 新增: 搜索职位页
    ├── resume_manager.py    # 已有
    ├── applications.py      # 新增: 投递记录页
    ├── messages.py          # 新增: 消息中心页
    └── settings.py          # 新增: 设置页
```

---

## Task 1: 样式和公共组件

**Files:**
- Create: `frontend/components/__init__.py`
- Create: `frontend/components/styles.py`
- Create: `frontend/components/common.py`

- [ ] **Step 1: 创建组件目录**

```bash
mkdir -p frontend/components frontend/pages
```

- [ ] **Step 2: 创建样式定义**

创建 `frontend/components/styles.py`：

```python
"""UI样式定义"""

# 颜色系统
COLORS = {
    "bg_deep": "#050508",
    "bg_primary": "#0a0a0f",
    "bg_card": "rgba(18, 18, 26, 0.8)",
    "bg_glass": "rgba(255, 255, 255, 0.03)",
    "text_primary": "#e4e4e7",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    "accent_electric": "#00d4ff",
    "accent_gold": "#fbbf24",
    "accent_green": "#4ade80",
    "accent_red": "#f87171",
    "accent_magenta": "#f472b6",
    "border_glow": "rgba(0, 212, 255, 0.3)",
    "border_subtle": "rgba(255, 255, 255, 0.08)",
}

# 全局CSS
GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-deep: #050508;
        --bg-primary: #0a0a0f;
        --bg-card: rgba(18, 18, 26, 0.8);
        --bg-glass: rgba(255, 255, 255, 0.03);
        --text-primary: #e4e4e7;
        --text-secondary: #a1a1aa;
        --text-muted: #71717a;
        --accent-electric: #00d4ff;
        --accent-gold: #fbbf24;
        --accent-green: #4ade80;
        --accent-red: #f87171;
        --accent-magenta: #f472b6;
        --border-glow: rgba(0, 212, 255, 0.3);
        --border-subtle: rgba(255, 255, 255, 0.08);
    }

    .stApp {
        background: var(--bg-deep);
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary);
    }

    /* 隐藏默认侧边栏 */
    [data-testid="stSidebar"] { display: none; }

    /* 主内容区 */
    [data-testid="stMainBlockContainer"] {
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 1.5rem !important;
    }

    /* 隐藏顶部和底部 */
    #MainMenu, header, footer, [data-testid="stStatusWidget"] { display: none; }

    /* 按钮样式 */
    .stButton button {
        background: var(--bg-card) !important;
        border: 1px solid var(--accent-electric) !important;
        color: var(--accent-electric) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.25s ease !important;
    }

    .stButton button:hover {
        background: rgba(0,212,255,0.1) !important;
        box-shadow: 0 0 20px rgba(0,212,255,0.3) !important;
    }

    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #0891b2, #00d4ff) !important;
        border: none !important;
        color: var(--bg-deep) !important;
    }

    /* 输入框样式 */
    .stTextInput input, .stTextArea textarea {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    .stTextInput input:focus {
        border-color: var(--accent-electric) !important;
    }

    /* 成功/错误提示 */
    .stSuccess {
        background: rgba(74,222,128,0.1) !important;
        border: 1px solid var(--accent-green) !important;
        color: var(--accent-green) !important;
        border-radius: 8px !important;
    }

    .stError {
        background: rgba(248,113,113,0.1) !important;
        border: 1px solid var(--accent-red) !important;
        color: var(--accent-red) !important;
        border-radius: 8px !important;
    }

    .stInfo {
        background: rgba(0,212,255,0.1) !important;
        border: 1px solid var(--accent-electric) !important;
        color: var(--accent-electric) !important;
        border-radius: 8px !important;
    }
</style>
"""

# 侧边栏样式
SIDEBAR_CSS = """
<style>
    .sidebar-container {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 220px;
        background: var(--bg-primary);
        border-right: 1px solid var(--border-subtle);
        padding: 1.5rem 1rem;
        display: flex;
        flex-direction: column;
        z-index: 100;
    }

    .sidebar-logo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--accent-electric);
        text-align: center;
        margin-bottom: 2rem;
    }

    .sidebar-nav-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        margin-bottom: 0.25rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: var(--text-secondary);
    }

    .sidebar-nav-item:hover {
        background: var(--bg-glass);
        color: var(--text-primary);
    }

    .sidebar-nav-item.active {
        background: rgba(0, 212, 255, 0.1);
        color: var(--accent-electric);
        border-left: 2px solid var(--accent-electric);
    }

    .sidebar-footer {
        margin-top: auto;
        padding-top: 1rem;
        border-top: 1px solid var(--border-subtle);
        font-size: 0.75rem;
        color: var(--text-muted);
        text-align: center;
    }

    /* 主内容区偏移 */
    [data-testid="stMainBlockContainer"] {
        margin-left: 220px !important;
    }
</style>
"""


def apply_styles():
    """应用全局样式"""
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def apply_sidebar_styles():
    """应用侧边栏样式"""
    import streamlit as st
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
```

- [ ] **Step 3: 创建公共组件**

创建 `frontend/components/common.py`：

```python
"""公共UI组件"""

import streamlit as st
from .styles import COLORS


def render_stat_card(label: str, value: str, color: str = None):
    """渲染统计卡片"""
    color = color or COLORS["accent_electric"]

    st.markdown(f"""
    <div style="
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    ">
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 1.5rem;
            font-weight: 700;
            color: {color};
        ">{value}</div>
        <div style="
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        ">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_indicator(label: str, is_ok: bool):
    """渲染状态指示器"""
    icon = "●" if is_ok else "○"
    color = COLORS["accent_green"] if is_ok else COLORS["text_muted"]
    text = label

    st.markdown(f"""
    <div style="
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    ">
        <span style="color: {color}; font-size: 0.85rem;">{icon}</span>
        <span style="color: var(--text-primary); font-size: 0.85rem;">{text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = None):
    """渲染区块标题"""
    subtitle_html = f'<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''

    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent-electric);
        ">{title}</div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_action_button(label: str, icon: str, key: str, primary: bool = False):
    """渲染操作按钮"""
    button_type = "primary" if primary else "secondary"
    return st.button(f"{icon} {label}", key=key, type=button_type, use_container_width=True)


def render_job_item(job: dict):
    """渲染职位条目"""
    status_colors = {
        "submitted": COLORS["accent_electric"],
        "read": COLORS["accent_gold"],
        "replied": COLORS["accent_green"],
        "interview": COLORS["accent_magenta"],
        "rejected": COLORS["accent_red"],
    }

    status = job.get("status", "submitted")
    status_color = status_colors.get(status, COLORS["text_muted"])
    status_text = {
        "submitted": "已投递",
        "read": "HR已读",
        "replied": "HR回复",
        "interview": "面试邀约",
        "rejected": "不合适",
    }.get(status, status)

    st.markdown(f"""
    <div style="
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <div style="font-weight: 600; color: var(--text-primary);">{job.get('title', '-')}</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">{job.get('company', '-')} · {job.get('city', '-')}</div>
        </div>
        <div style="font-family: 'JetBrains Mono'; font-size: 0.85rem; color: {status_color};">{status_text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_loading_screen(message: str = "加载中..."):
    """渲染全屏加载"""
    st.markdown(f"""
    <div style="
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: var(--bg-deep);
        z-index: 9999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    ">
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 2rem;
            color: var(--accent-electric);
            animation: pulse 1.5s ease-in-out infinite;
        ">⚡</div>
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 1rem;
        ">{message}</div>
    </div>
    <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
        }}
    </style>
    """, unsafe_allow_html=True)
```

- [ ] **Step 4: 创建组件导出**

创建 `frontend/components/__init__.py`：

```python
"""UI组件模块"""

from .styles import COLORS, apply_styles, apply_sidebar_styles
from .common import (
    render_stat_card,
    render_status_indicator,
    render_section_header,
    render_action_button,
    render_job_item,
    render_loading_screen,
)

__all__ = [
    "COLORS",
    "apply_styles",
    "apply_sidebar_styles",
    "render_stat_card",
    "render_status_indicator",
    "render_section_header",
    "render_action_button",
    "render_job_item",
    "render_loading_screen",
]
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/
git commit -m "feat: 添加前端样式和公共组件"
```

---

## Task 2: 侧边导航

**Files:**
- Create: `frontend/components/sidebar.py`

- [ ] **Step 1: 创建侧边导航组件**

创建 `frontend/components/sidebar.py`：

```python
"""侧边导航组件"""

import streamlit as st
from .styles import apply_sidebar_styles


# 导航项定义
NAV_ITEMS = [
    {"id": "dashboard", "label": "仪表盘", "icon": "🏠"},
    {"id": "search", "label": "搜索职位", "icon": "🔍"},
    {"id": "resumes", "label": "管理简历", "icon": "📄"},
    {"id": "applications", "label": "投递记录", "icon": "📊"},
    {"id": "messages", "label": "消息中心", "icon": "💬"},
    {"id": "settings", "label": "设置", "icon": "⚙️"},
]


def render_sidebar():
    """渲染侧边导航栏"""
    apply_sidebar_styles()

    current_page = st.session_state.get("page", "dashboard")

    # Logo
    st.markdown("""
    <div class="sidebar-logo">
        ⚡ AUTO_JOB_HUNTER
    </div>
    """, unsafe_allow_html=True)

    # 导航项
    for item in NAV_ITEMS:
        is_active = current_page == item["id"]
        active_class = "active" if is_active else ""

        st.markdown(f"""
        <div class="sidebar-nav-item {active_class}" onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'{item['id']}"}},'*')">
            <span>{item['icon']}</span>
            <span>{item['label']}</span>
        </div>
        """, unsafe_allow_html=True)

    # 使用 Streamlit 按钮作为导航（兼容性更好）
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    for item in NAV_ITEMS:
        is_active = current_page == item["id"]
        btn_type = "primary" if is_active else "secondary"

        if st.button(
            f"{item['icon']} {item['label']}",
            key=f"nav_{item['id']}",
            type=btn_type,
            use_container_width=True,
        ):
            st.session_state.page = item["id"]
            st.rerun()

    # 底部信息
    st.markdown("""
    <div class="sidebar-footer">
        v1.0.0 · Open Source
    </div>
    """, unsafe_allow_html=True)


def get_current_page() -> str:
    """获取当前页面ID"""
    return st.session_state.get("page", "dashboard")


def navigate_to(page_id: str):
    """导航到指定页面"""
    st.session_state.page = page_id
```

- [ ] **Step 2: 更新组件导出**

修改 `frontend/components/__init__.py`：

```python
from .sidebar import render_sidebar, get_current_page, navigate_to, NAV_ITEMS
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/
git commit -m "feat: 添加侧边导航组件"
```

---

## Task 3: 仪表盘组件

**Files:**
- Create: `frontend/components/dashboard.py`
- Create: `backend/api/dashboard.py`

- [ ] **Step 1: 创建仪表盘API**

创建 `backend/api/dashboard.py`：

```python
"""仪表盘API"""

from fastapi import APIRouter
from datetime import datetime, timedelta

from backend.core.database import SessionLocal, Job, Application, UserProfile
from backend.adapters import Platform

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(user_id: int = 1):
    """获取仪表盘概览数据"""
    db = SessionLocal()
    try:
        # 今日投递数
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())

        today_applications = db.query(Application).filter(
            Application.created_at >= today_start
        ).count()

        # 平台登录状态
        platform_status = []
        for platform in [Platform.BOSS, Platform.LIEPIN]:
            from backend.adapters import get_adapter
            try:
                adapter = get_adapter(platform)
                logged_in = False  # 实际应检查Cookie
                platform_status.append({
                    "platform": platform.value,
                    "logged_in": logged_in,
                })
            except:
                platform_status.append({
                    "platform": platform.value,
                    "logged_in": False,
                })

        # 简历状态
        profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        has_resume = bool(profile and profile.resume_text)

        # 本周投递数
        week_start = today - timedelta(days=today.weekday())
        week_start_dt = datetime.combine(week_start, datetime.min.time())

        week_applications = db.query(Application).filter(
            Application.created_at >= week_start_dt
        ).count()

        # 最近投递
        recent_apps = db.query(Application).join(Job).order_by(
            Application.created_at.desc()
        ).limit(5).all()

        recent = []
        for app in recent_apps:
            recent.append({
                "id": app.id,
                "job_title": app.job.title if app.job else None,
                "company": app.job.company if app.job else None,
                "status": app.status.value if app.status else "pending",
                "created_at": app.created_at.isoformat() if app.created_at else None,
            })

        return {
            "today_applications": today_applications,
            "week_applications": week_applications,
            "platform_status": platform_status,
            "has_resume": has_resume,
            "recent_applications": recent,
        }

    finally:
        db.close()
```

- [ ] **Step 2: 注册仪表盘路由**

修改 `backend/api/routes.py`：

```python
from .dashboard import router as dashboard_router

api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
```

- [ ] **Step 3: 创建仪表盘组件**

创建 `frontend/components/dashboard.py`：

```python
"""仪表盘组件"""

import streamlit as st
import requests
import os

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")

from .common import (
    render_stat_card,
    render_status_indicator,
    render_section_header,
    render_action_button,
    render_job_item,
)


def render_dashboard():
    """渲染仪表盘"""

    # 获取概览数据
    overview = fetch_dashboard_overview()

    # 系统状态总览
    render_section_header("系统状态总览")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        boss_status = next(
            (p for p in overview.get("platform_status", []) if p["platform"] == "boss"),
            {"logged_in": False}
        )
        render_status_indicator("BOSS直聘", boss_status.get("logged_in", False))

    with col2:
        liepin_status = next(
            (p for p in overview.get("platform_status", []) if p["platform"] == "liepin"),
            {"logged_in": False}
        )
        render_status_indicator("猎聘", liepin_status.get("logged_in", False))

    with col3:
        render_status_indicator("简历", overview.get("has_resume", False))

    with col4:
        st.markdown(f"""
        <div style="
            background: var(--bg-glass);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            text-align: center;
        ">
            <div style="font-family: 'JetBrains Mono'; font-size: 1.2rem; font-weight: 700; color: var(--accent-electric);">
                {overview.get('today_applications', 0)}
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">今日投递</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 快速操作
    render_section_header("快速操作")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if render_action_button("搜索职位", "🔍", "quick_search"):
            st.session_state.page = "search"
            st.rerun()

    with col2:
        if render_action_button("管理简历", "📄", "quick_resume"):
            st.session_state.page = "resumes"
            st.rerun()

    with col3:
        if render_action_button("投递记录", "📊", "quick_apps"):
            st.session_state.page = "applications"
            st.rerun()

    with col4:
        if render_action_button("消息中心", "💬", "quick_msgs"):
            st.session_state.page = "messages"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 一键求职
    render_section_header("一键求职", "自动搜索并投递匹配职位")

    if st.button("🚀 开始一键求职", type="primary", use_container_width=True):
        st.session_state.page = "search"
        st.session_state.auto_start = True
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 今日投递概览
    render_section_header("今日投递概览")

    recent = overview.get("recent_applications", [])
    if recent:
        for app in recent[:5]:
            render_job_item({
                "title": app.get("job_title"),
                "company": app.get("company"),
                "status": app.get("status"),
            })

        if st.button("查看全部投递记录", key="view_all_apps"):
            st.session_state.page = "applications"
            st.rerun()
    else:
        st.info("今日暂无投递记录")


def fetch_dashboard_overview():
    """获取仪表盘概览数据"""
    try:
        r = requests.get(f"{API_BASE}/dashboard/overview", timeout=10)
        if r.ok:
            return r.json()
    except:
        pass
    return {}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/ backend/api/dashboard.py backend/api/routes.py
git commit -m "feat: 添加仪表盘API和前端组件"
```

---

## Task 4: 重构主应用

**Files:**
- Rewrite: `frontend/app.py`

- [ ] **Step 1: 重写主应用入口**

重写 `frontend/app.py`：

```python
"""
Auto Job Hunter - Streamlit Web GUI

新版架构：仪表盘 + 多页面导航
"""

import streamlit as st
import os

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


# ========== 页面配置 ==========

st.set_page_config(
    page_title="Auto Job Hunter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ========== 导入组件 ==========

from frontend.components import (
    apply_styles,
    render_sidebar,
    get_current_page,
    render_loading_screen,
)


# ========== Session State 初始化 ==========

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "loading" not in st.session_state:
    st.session_state.loading = False

if "loading_message" not in st.session_state:
    st.session_state.loading_message = ""


# ========== 应用样式 ==========

apply_styles()


# ========== 渲染布局 ==========

# 加载状态
if st.session_state.loading:
    render_loading_screen(st.session_state.loading_message)
    st.session_state.loading = False
    st.rerun()

# 侧边导航
render_sidebar()

# 主内容区
current_page = get_current_page()

# 根据页面渲染内容
if current_page == "dashboard":
    from frontend.components.dashboard import render_dashboard
    render_dashboard()

elif current_page == "search":
    from frontend.pages.search import render_search_page
    render_search_page()

elif current_page == "resumes":
    from frontend.pages.resume_manager import render_resume_manager
    render_resume_manager()

elif current_page == "applications":
    from frontend.pages.applications import render_applications_page
    render_applications_page()

elif current_page == "messages":
    from frontend.pages.messages import render_messages_page
    render_messages_page()

elif current_page == "settings":
    from frontend.pages.settings import render_settings_page
    render_settings_page()

else:
    st.error("未知页面")


if __name__ == "__main__":
    pass
```

- [ ] **Step 2: 创建搜索页面骨架**

创建 `frontend/pages/search.py`：

```python
"""搜索职位页面"""

import streamlit as st
from frontend.components import render_section_header


def render_search_page():
    """渲染搜索页面"""

    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 600; color: var(--accent-electric);">
            🔍 搜索职位
        </div>
    </div>
    """, unsafe_allow_html=True)

    # TODO: 实现完整的搜索功能
    # 这里可以复用现有的搜索逻辑

    render_section_header("搜索条件")

    col1, col2 = st.columns(2)

    with col1:
        keywords = st.text_input("搜索关键词", placeholder="如: Python后端")

    with col2:
        platforms = st.multiselect("选择平台", ["boss", "liepin"], default=["boss"])

    city = st.text_input("目标城市", placeholder="如: 北京")

    auto_apply = st.checkbox("自动投递符合条件的职位")

    if st.button("开始搜索", type="primary"):
        st.info("搜索功能开发中...")


if __name__ == "__main__":
    pass
```

- [ ] **Step 3: 创建其他页面骨架**

创建 `frontend/pages/__init__.py`：
```python
"""页面模块"""
```

创建 `frontend/pages/applications.py`：
```python
"""投递记录页面"""

import streamlit as st
from frontend.components import render_section_header


def render_applications_page():
    st.markdown("### 📊 投递记录")
    # TODO: 实现投递记录功能
    st.info("投递记录功能开发中...")
```

创建 `frontend/pages/messages.py`：
```python
"""消息中心页面"""

import streamlit as st


def render_messages_page():
    st.markdown("### 💬 消息中心")
    # TODO: 实现消息中心功能
    st.info("消息中心功能开发中...")
```

创建 `frontend/pages/settings.py`：
```python
"""设置页面"""

import streamlit as st


def render_settings_page():
    st.markdown("### ⚙️ 设置")
    # TODO: 实现设置功能
    st.info("设置功能开发中...")
```

- [ ] **Step 4: 测试新架构**

```bash
cd /d E:\Code\auto_job_hunter && streamlit run frontend/app.py
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "refactor: 重构前端为仪表盘导航模式"
```

---

## Verification

- [ ] **启动后端**

```bash
cd /d E:\Code\auto_job_hunter && python run.py web
```

- [ ] **启动前端**

```bash
streamlit run frontend/app.py
```

- [ ] **验证功能**
- 仪表盘显示正常
- 侧边导航可用
- 各页面可切换
- 样式正确应用

---

## Summary

完成本计划后：

1. **仪表盘首页**: 系统状态总览、快速操作、一键求职入口
2. **侧边导航**: 仪表盘、搜索、简历、投递记录、消息、设置
3. **多页面架构**: 各功能模块独立页面
4. **统一样式系统**: 暗黑科技风格 UI 组件
5. **公共组件库**: 卡片、状态指示器、按钮等可复用组件

前端架构重构完成，后续可以在各页面骨架中填充具体功能。