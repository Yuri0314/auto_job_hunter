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