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