"""
搜索职位页面

完整实现：搜索表单、API调用、进度显示、职位列表展示
状态变量使用命名空间 search.xxx
"""

import os
import streamlit as st
import requests
from datetime import datetime

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


# ========== 状态变量命名规范 ==========
# 本页面所有session_state变量使用 search.xxx 命名空间
# - search.keywords: 搜索关键词
# - search.platforms: 选择平台
# - search.city: 目标城市
# - search.auto_apply: 是否自动投递
# - search.results: 搜索结果
# - search.stats: 搜索统计


# ========== Helper Functions ==========

def _get_state(key: str, default=None):
    """获取命名空间状态"""
    return st.session_state.get(f"search.{key}", default)


def _set_state(key: str, value):
    """设置命名空间状态"""
    st.session_state[f"search.{key}"] = value


def _del_state(key: str):
    """删除命名空间状态"""
    full_key = f"search.{key}"
    if full_key in st.session_state:
        del st.session_state[full_key]


# ========== API Functions ==========

def api_search_jobs(keywords: str, platforms: list, city: str = None, auto_apply: bool = False):
    """调用搜索并投递API"""
    try:
        r = requests.post(
            f"{API_BASE}/applications/search-and-apply",
            json={
                "keywords": keywords,
                "platforms": platforms,
                "city": city,
                "auto_apply": auto_apply,
                "max_count": 20,
            },
            timeout=120  # 搜索可能需要较长时间
        )
        if r.ok:
            return r.json()
        return {"success": False, "error": r.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def api_get_jobs(status=None, platform=None, keyword=None, page=1, page_size=20):
    """获取职位列表"""
    try:
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if platform:
            params["platform"] = platform
        if keyword:
            params["keyword"] = keyword

        r = requests.get(f"{API_BASE}/jobs", params=params, timeout=10)
        if r.ok:
            return r.json()
        return {"items": [], "total": 0}
    except Exception as e:
        return {"items": [], "total": 0}


def api_apply_job(job_id: int):
    """手动投递职位"""
    try:
        r = requests.post(f"{API_BASE}/jobs/{job_id}/apply", timeout=30)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== Main Render Function ==========

def render_search_page():
    """渲染搜索页面"""

    # 页面标题
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 700; color: #00d4ff;">
            SEARCH_JOBS
        </div>
        <div style="font-size: 0.8rem; color: #71717a; margin-top: 0.25rem;">
            多平台搜索 · 智能过滤 · 自动投递
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 消息提示
    msg = _get_state("msg")
    if msg:
        msg_type, msg_text = msg
        if msg_type == "success":
            st.success(msg_text)
        else:
            st.error(msg_text)
        _del_state("msg")

    # 搜索表单区
    _render_search_form()

    # 搜索结果区（如果有结果）
    results = _get_state("results")
    if results:
        _render_search_results(results)


def _render_search_form():
    """渲染搜索表单"""

    st.markdown("**搜索条件**")

    col1, col2 = st.columns(2)

    with col1:
        # 使用上次搜索关键词作为默认值
        default_keywords = _get_state("keywords", "")
        keywords = st.text_input(
            "搜索关键词",
            value=default_keywords,
            placeholder="如: Python后端",
            key="search_keywords_input"
        )

    with col2:
        default_platforms = _get_state("platforms", ["boss"])
        platforms = st.multiselect(
            "选择平台",
            options=["boss", "liepin"],
            default=default_platforms,
            key="search_platforms_input"
        )

    default_city = _get_state("city", "")
    city = st.text_input(
        "目标城市",
        value=default_city,
        placeholder="如: 北京",
        key="search_city_input"
    )

    default_auto_apply = _get_state("auto_apply", False)
    auto_apply = st.checkbox(
        "自动投递符合条件的职位",
        value=default_auto_apply,
        key="search_auto_apply_input"
    )

    # 搜索按钮
    if st.button("开始搜索", type="primary", key="start_search_btn"):
        if not keywords:
            st.warning("请输入搜索关键词")
        elif not platforms:
            st.warning("请选择至少一个平台")
        else:
            # 保存搜索条件
            _set_state("keywords", keywords)
            _set_state("platforms", platforms)
            _set_state("city", city)
            _set_state("auto_apply", auto_apply)

            # 执行搜索
            with st.spinner("正在搜索职位，请稍候..."):
                result = api_search_jobs(keywords, platforms, city, auto_apply)

            # 检查是否有错误（后端返回 {"error": ...} 表示失败）
            if result.get("error"):
                _set_state("msg", ("error", f"搜索失败: {result.get('error')}"))
            else:
                _set_state("results", result)
                _set_state("msg", ("success", f"搜索完成！发现 {result.get('total_found', 0)} 个职位"))
            st.rerun()

    # 快捷操作
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("查看上次结果", key="view_last_results"):
            # 查看数据库中的职位列表
            jobs_data = api_get_jobs(status="new", page_size=50)
            if jobs_data.get("items"):
                _set_state("results", {
                    "success": True,
                    "total_found": jobs_data.get("total", 0),
                    "filtered": jobs_data.get("total", 0),
                    "applied": 0,
                    "jobs": jobs_data.get("items", [])
                })
                st.rerun()
            else:
                st.info("暂无职位记录")

    with col_b:
        if st.button("清空结果", key="clear_results"):
            _del_state("results")
            st.rerun()


def _render_search_results(results):
    """渲染搜索结果"""

    st.divider()

    # 统计信息
    total_found = results.get("total_found", 0)
    filtered = results.get("filtered", 0)
    applied = results.get("applied", 0)

    st.markdown(f"""
    <div style="background: rgba(18, 18, 26, 0.8); border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <span style="font-family: 'JetBrains Mono'; color: #00d4ff;">
            📊 发现: {total_found} | 符合条件: {filtered} | 已投递: {applied}
        </span>
    </div>
    """, unsafe_allow_html=True)

    jobs = results.get("jobs", [])

    if not jobs:
        st.info("没有找到符合条件的职位")
        return

    # 职位列表
    st.markdown("**职位列表**")

    for job in jobs:
        _render_job_card(job)


def _render_job_card(job):
    """渲染职位卡片"""

    job_id = job.get("id")
    title = job.get("title", "未知职位")
    company = job.get("company", "未知公司")
    salary = job.get("salary", "")
    city = job.get("city", "")
    platform = job.get("platform", "").upper()

    # 卡片样式
    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            # 职位信息
            st.markdown(f"""
            <div style="font-family: 'JetBrains Mono'; font-size: 1rem; color: #e4e4e7; margin-bottom: 0.25rem;">
                {title}
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"{company} | {city} | {salary} | {platform}")

        with col2:
            st.caption("")  # spacer

        # 操作按钮
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            if st.button("详情", key=f"detail_{job_id}", use_container_width=True):
                _show_job_detail(job)

        with btn_col2:
            # 如果未自动投递，提供手动投递按钮
            auto_apply = _get_state("auto_apply", False)
            if not auto_apply:
                if st.button("投递", key=f"apply_{job_id}", use_container_width=True):
                    with st.spinner("投递中..."):
                        result = api_apply_job(job_id)
                    if result.get("error"):
                        st.error(f"投递失败: {result.get('error')}")
                    else:
                        st.success("投递成功！")

        with btn_col3:
            # 查看原链接（如果有URL）
            url = job.get("url")
            if url:
                st.markdown(f"""
                <a href="{url}" target="_blank" style="
                    display: inline-block;
                    background: rgba(18, 18, 26, 0.8);
                    border: 1px solid rgba(255,255,255,0.08);
                    color: #71717a;
                    font-family: 'JetBrains Mono';
                    padding: 0.375rem 0.75rem;
                    border-radius: 8px;
                    text-decoration: none;
                    width: 100%;
                    text-align: center;
                ">原链接</a>
                """, unsafe_allow_html=True)

        st.divider()


def _show_job_detail(job):
    """显示职位详情（简单弹窗方式）"""

    st.markdown("---")
    st.markdown(f"**职位详情: {job.get('title', '未知')}**")

    col1, col2 = st.columns(2)

    with col1:
        st.text(f"公司: {job.get('company', '-')}")
        st.text(f"城市: {job.get('city', '-')}")
        st.text(f"薪资: {job.get('salary', '-')}")

    with col2:
        st.text(f"平台: {job.get('platform', '-').upper()}")
        st.text(f"职位ID: {job.get('job_id', '-')}")

    # 职位描述
    description = job.get("description", "")
    if description:
        st.markdown("**职位描述**")
        st.text_area("", value=description[:500] + ("..." if len(description) > 500 else ""), height=150, disabled=True)

    # 关闭按钮
    if st.button("关闭详情", key="close_detail"):
        st.rerun()


if __name__ == "__main__":
    pass