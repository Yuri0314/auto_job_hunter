"""侧边导航组件"""

import streamlit as st


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
    """渲染侧边导航栏 - 使用Streamlit原生sidebar布局"""
    # 不再使用自定义CSS，直接使用Streamlit原生sidebar
    with st.sidebar:
        # Logo
        st.markdown("""
        <style>
            /* Sidebar样式 */
            [data-testid="stSidebar"] {
                background: #0a0a0f !important;
            }
            [data-testid="stSidebar"] > div {
                padding-top: 1rem !important;
            }
            /* 按钮样式 */
            [data-testid="stSidebar"] .stButton button {
                background: rgba(18, 18, 26, 0.8) !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
                color: #71717a !important;
                font-family: 'JetBrains Mono', monospace !important;
                border-radius: 8px !important;
                text-align: left !important;
                padding: 0.75rem 1rem !important;
            }
            [data-testid="stSidebar"] .stButton button:hover {
                border-color: #00d4ff !important;
                color: #00d4ff !important;
                background: rgba(0,212,255,0.05) !important;
            }
            [data-testid="stSidebar"] .stButton button[kind="primary"] {
                background: rgba(0,212,255,0.1) !important;
                border-color: #00d4ff !important;
                color: #00d4ff !important;
            }
        </style>
        <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 1rem;">
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #00d4ff;">
                ⚡ AUTO_JOB_HUNTER
            </span>
        </div>
        """, unsafe_allow_html=True)

        # 导航按钮
        current_page = st.session_state.get("page", "dashboard")

        for item in NAV_ITEMS:
            is_active = current_page == item["id"]
            btn_type = "primary" if is_active else "secondary"

            if st.button(
                f"{item['icon']} {item['label']}",
                key=f"nav_{item['id']}",
                type=btn_type,
                use_container_width=True,
            ):
                _clear_loading_states()
                st.session_state.page = item["id"]
                st.rerun()

        # 底部信息
        st.markdown("""
        <div style="text-align: center; padding-top: 2rem; border-top: 1px solid rgba(255,255,255,0.08); margin-top: 2rem;">
            <span style="font-size: 0.75rem; color: #71717a;">v1.0.0 · Open Source</span>
        </div>
        """, unsafe_allow_html=True)


def _clear_loading_states():
    """清除resume相关的session state"""
    # 只清除可能卡住的状态键
    keys_to_remove = [
        "_resume_manager_loading",
        "_resume_loading_message",
        "_resume_action_type",
        "_resume_action_id",
        "_resume_upload_file",
        "_resume_text_content",
        "_resume_delete_confirm",
        "_resume_list_cache",
        "_edit_resume_id",
        "_view_resume_id",
        "_confirm_delete",
    ]

    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]


def get_current_page() -> str:
    """获取当前页面ID"""
    return st.session_state.get("page", "dashboard")


def navigate_to(page_id: str):
    """导航到指定页面"""
    st.session_state.page = page_id