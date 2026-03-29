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

    # 使用 Streamlit 按钮作为导航
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