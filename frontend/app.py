"""
Auto Job Hunter - Streamlit Web GUI

新版架构：仪表盘 + 多页面导航
"""

import streamlit as st
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


# ========== 页面配置 ==========

st.set_page_config(
    page_title="Auto Job Hunter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",  # 侧边栏默认展开
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