"""
简历管理前端组件

功能：
- 简历列表展示
- 文件上传解析
- 文本粘贴解析
- 设置主简历
- 删除简历

设计风格: Obsidian Terminal (深黑 + 电蓝霓虹)
"""

import os
import streamlit as st
import requests
from datetime import datetime

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


# ========== 暗黑科技风格 CSS ==========

RESUME_MANAGER_CSS = """
<style>
    /* 简历卡片样式 */
    .resume-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
        position: relative;
    }

    .resume-card:hover {
        border-color: var(--accent-electric);
        box-shadow: 0 0 20px rgba(0,212,255,0.15);
    }

    .resume-card.primary {
        border-color: var(--accent-gold);
        box-shadow: 0 0 15px rgba(251,191,36,0.2);
    }

    .resume-card.primary::before {
        content: 'PRIMARY';
        position: absolute;
        top: -1px;
        right: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        padding: 0.15rem 0.5rem;
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        color: var(--bg-deep);
        border-radius: 0 0 4px 4px;
        letter-spacing: 0.05em;
    }

    .resume-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
    }

    .resume-name {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .resume-meta {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .meta-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        padding: 0.25rem 0.6rem;
        background: var(--bg-glass);
        border-radius: 6px;
        color: var(--text-muted);
        border: 1px solid var(--border-subtle);
    }

    .meta-tag.file-type {
        color: var(--accent-electric);
        border-color: rgba(0,212,255,0.3);
    }

    .resume-info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
        margin-top: 0.75rem;
    }

    .resume-info-item {
        padding: 0.5rem 0.75rem;
        background: var(--bg-glass);
        border-radius: 6px;
        border: 1px solid var(--border-subtle);
    }

    .resume-info-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: var(--text-muted);
        letter-spacing: 0.05em;
    }

    .resume-info-value {
        font-size: 0.85rem;
        color: var(--text-primary);
        margin-top: 0.15rem;
    }

    .resume-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-subtle);
    }

    /* 上传区域样式 */
    .upload-zone {
        border: 2px dashed var(--border-subtle);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: var(--bg-glass);
        transition: all 0.2s ease;
    }

    .upload-zone:hover {
        border-color: var(--accent-electric);
        background: rgba(0,212,255,0.05);
    }

    .upload-icon {
        font-size: 2.5rem;
        color: var(--accent-electric);
        margin-bottom: 1rem;
    }

    /* Tabs 样式 */
    .stTabs [data-baseweb="tabs-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        padding: 0.75rem 1.5rem !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 8px !important;
        color: var(--text-muted) !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        border-color: var(--accent-electric) !important;
        color: var(--accent-electric) !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(0,212,255,0.1) !important;
        border-color: var(--accent-electric) !important;
        color: var(--accent-electric) !important;
    }

    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: var(--text-muted);
    }

    .empty-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    /* 详情模态框 */
    .detail-modal {
        background: var(--bg-card);
        border: 1px solid var(--accent-electric);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1rem;
    }

    .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }

    .detail-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    /* 技能标签 */
    .skill-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .skill-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        background: rgba(0,212,255,0.1);
        border-radius: 6px;
        color: var(--accent-electric);
        border: 1px solid rgba(0,212,255,0.2);
    }
</style>
"""


# ========== API Functions ==========

def fetch_resume_list():
    """获取简历列表"""
    try:
        r = requests.get(f"{API_BASE}/resume/list", timeout=10)
        if r.ok:
            return r.json()
        return {"items": [], "total": 0}
    except Exception as e:
        st.error(f"获取简历列表失败: {e}")
        return {"items": [], "total": 0, "error": str(e)}


def upload_resume(file, use_ai=False):
    """上传简历文件"""
    try:
        files = {"file": (file.name, file, "application/octet-stream")}
        params = {"use_ai": str(use_ai).lower()}
        r = requests.post(f"{API_BASE}/resume/upload", files=files, params=params, timeout=60)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_text_resume(text, use_ai=False):
    """解析粘贴的简历文本"""
    try:
        r = requests.post(
            f"{API_BASE}/resume/parse-text",
            json={"text": text, "use_ai": use_ai},
            timeout=60
        )
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_primary_resume(resume_id):
    """设置主简历"""
    try:
        r = requests.post(f"{API_BASE}/resume/{resume_id}/set-primary", timeout=10)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_resume(resume_id):
    """删除简历"""
    try:
        r = requests.delete(f"{API_BASE}/resume/{resume_id}", timeout=10)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_resume_detail(resume_id):
    """获取简历详情"""
    try:
        r = requests.get(f"{API_BASE}/resume/{resume_id}", timeout=10)
        if r.ok:
            return r.json()
        return None
    except Exception as e:
        return None


def update_resume_profile(resume_id, profile_data):
    """更新简历画像"""
    try:
        r = requests.put(
            f"{API_BASE}/resume/{resume_id}/profile",
            json=profile_data,
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== Session State Keys ==========

RESUME_LIST_KEY = "_resume_manager_list"
RESUME_LOADING_KEY = "_resume_manager_loading"
RESUME_DETAIL_KEY = "_resume_manager_detail"
RESUME_ACTION_KEY = "_resume_manager_action"


# ========== Render Functions ==========

def render_resume_manager():
    """主渲染函数 - 简历管理页面"""
    # 应用 CSS
    st.markdown(RESUME_MANAGER_CSS, unsafe_allow_html=True)

    # 页面标题
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 700; color: var(--accent-electric);">
            RESUME_MANAGER
        </div>
        <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
            // 简历管理 · 多简历支持 · 智能解析
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 检查 loading 状态
    if st.session_state.get(RESUME_LOADING_KEY):
        show_loading_screen(st.session_state.get("_resume_loading_message", "处理中..."))
        execute_pending_action()
        return

    # Tabs 布局
    tab1, tab2, tab3 = st.tabs(["简历列表", "上传简历", "粘贴文本"])

    with tab1:
        render_resume_list()

    with tab2:
        render_upload_section()

    with tab3:
        render_paste_section()


def render_resume_list():
    """渲染简历列表"""
    # 加载简历列表
    if st.session_state.get(RESUME_LIST_KEY) is None:
        st.session_state[RESUME_LIST_KEY] = fetch_resume_list()

    data = st.session_state.get(RESUME_LIST_KEY, {})
    resumes = data.get("items", [])

    # 刷新按钮
    if st.button("刷新列表", key="refresh_resume_list"):
        st.session_state[RESUME_LIST_KEY] = None
        st.rerun()

    if not resumes:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📄</div>
            <div style="font-family: 'JetBrains Mono';">暂无简历</div>
            <div style="font-size: 0.85rem; margin-top: 0.5rem;">上传或粘贴简历开始使用</div>
        </div>
        """, unsafe_allow_html=True)
        # 即使没有简历，也要处理模态框状态（防止残留）
        if st.session_state.get("_edit_resume_id") or st.session_state.get("_view_resume_id"):
            st.session_state._edit_resume_id = None
            st.session_state._view_resume_id = None
        return

    # 显示简历卡片
    for resume in resumes:
        render_resume_card(resume)

    # 显示编辑模态框
    if st.session_state.get("_edit_resume_id"):
        render_resume_detail_modal(st.session_state._edit_resume_id, readonly=False)

    # 显示详情模态框
    if st.session_state.get("_view_resume_id"):
        render_resume_detail_modal(st.session_state._view_resume_id, readonly=True)


def render_resume_card(resume):
    """渲染单个简历卡片"""
    resume_id = resume.get("id")
    is_primary = resume.get("is_primary", False)
    profile = resume.get("profile") or {}

    # 卡片容器
    card_class = "resume-card primary" if is_primary else "resume-card"
    st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)

    # 头部信息
    st.markdown(f"""
    <div class="resume-header">
        <div>
            <div class="resume-name">{resume.get('name', '未命名简历')}</div>
            <div class="resume-meta">
                <span class="meta-tag file-type">{resume.get('file_type', '-').upper()}</span>
                <span class="meta-tag">{resume.get('parse_engine', 'simple')}</span>
                <span class="meta-tag">{format_created_time(resume.get('created_at'))}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 画像信息网格
    if profile:
        st.markdown("""
        <div class="resume-info-grid">
            <div class="resume-info-item">
                <div class="resume-info-label">当前职位</div>
                <div class="resume-info-value">{current_position}</div>
            </div>
            <div class="resume-info-item">
                <div class="resume-info-label">工作年限</div>
                <div class="resume-info-value">{exp_years}年</div>
            </div>
            <div class="resume-info-item">
                <div class="resume-info-label">学历</div>
                <div class="resume-info-value">{education}</div>
            </div>
            <div class="resume-info-item">
                <div class="resume-info-label">学校</div>
                <div class="resume-info-value">{school}</div>
            </div>
        </div>
        """.format(
            current_position=profile.get("current_position", "-") or "-",
            exp_years=profile.get("experience_years", "-") or "-",
            education=profile.get("education", "-") or "-",
            school=profile.get("school", "-") or "-",
        ), unsafe_allow_html=True)

        # 技能标签
        skills = profile.get("skills", [])
        if skills:
            skills_html = "".join([f"<span class='skill-tag'>{s}</span>" for s in skills[:6]])
            st.markdown(f"""
            <div style="margin-top: 0.75rem;">
                <div class="resume-info-label">核心技能</div>
                <div class="skill-tags">{skills_html}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # 操作按钮
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("查看详情", key=f"detail_{resume_id}", use_container_width=True):
            st.session_state._view_resume_id = resume_id
            st.rerun()

    with col2:
        if not is_primary:
            if st.button("设为主简历", key=f"primary_{resume_id}", use_container_width=True):
                st.session_state[RESUME_LOADING_KEY] = True
                st.session_state["_resume_loading_message"] = "设置主简历..."
                st.session_state["_resume_action_type"] = "set_primary"
                st.session_state["_resume_action_id"] = resume_id
                st.rerun()

    with col3:
        if st.button("编辑", key=f"edit_{resume_id}", use_container_width=True):
            st.session_state._edit_resume_id = resume_id
            st.rerun()

    with col4:
        if st.button("删除", key=f"delete_{resume_id}", use_container_width=True):
            st.session_state["_resume_delete_confirm"] = resume_id
            st.rerun()

    # 删除确认对话框
    if st.session_state.get("_resume_delete_confirm") == resume_id:
        st.warning(f"确认删除简历 '{resume.get('name')}'？")
        col_confirm1, col_confirm2 = st.columns(2)
        with col_confirm1:
            if st.button("确认删除", key=f"confirm_del_{resume_id}"):
                st.session_state[RESUME_LOADING_KEY] = True
                st.session_state["_resume_loading_message"] = "删除简历..."
                st.session_state["_resume_action_type"] = "delete"
                st.session_state["_resume_action_id"] = resume_id
                st.session_state["_resume_delete_confirm"] = None
                st.rerun()
        with col_confirm2:
            if st.button("取消", key=f"cancel_del_{resume_id}"):
                st.session_state["_resume_delete_confirm"] = None
                st.rerun()


def render_upload_section():
    """渲染上传简历区域"""
    st.markdown("""
    <div class="upload-zone">
        <div class="upload-icon">📤</div>
        <div style="font-family: 'JetBrains Mono'; color: var(--text-primary); margin-bottom: 0.5rem;">
            上传简历文件
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted);">
            支持 PDF · Word · Markdown · TXT
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "doc", "md", "txt"],
        key="resume_file_upload"
    )

    use_ai = st.checkbox("使用 AI 模式解析（更准确）", value=False, key="upload_use_ai")

    if uploaded_file:
        st.markdown(f"""
        <div style="padding: 0.75rem; background: var(--bg-glass); border-radius: 8px; margin-top: 1rem;">
            <span style="color: var(--text-muted); font-size: 0.85rem;">已选择：</span>
            <span style="color: var(--accent-electric); font-family: 'JetBrains Mono';">{uploaded_file.name}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("解析简历", type="primary", use_container_width=True, key="btn_parse_upload"):
            st.session_state[RESUME_LOADING_KEY] = True
            st.session_state["_resume_loading_message"] = "解析简历中..."
            st.session_state["_resume_action_type"] = "upload"
            st.session_state["_resume_upload_file"] = uploaded_file
            st.session_state["_resume_upload_use_ai"] = use_ai
            st.rerun()


def render_paste_section():
    """渲染粘贴文本区域"""
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <div style="font-family: 'JetBrains Mono'; color: var(--text-primary); margin-bottom: 0.5rem;">
            粘贴简历内容
        </div>
        <div style="font-size: 0.85rem; color: var(--text-muted);">
            直接复制粘贴简历文本，系统将自动提取关键信息
        </div>
    </div>
    """, unsafe_allow_html=True)

    text_content = st.text_area(
        "简历内容",
        placeholder="粘贴您的简历内容...\n\n姓名: 张三\n学历: 本科\n工作年限: 5年\n...",
        height=300,
        key="resume_text_paste"
    )

    use_ai = st.checkbox("使用 AI 模式解析（更准确）", value=False, key="paste_use_ai")

    if st.button("解析文本", type="primary", use_container_width=True, key="btn_parse_text"):
        if len(text_content) < 50:
            st.warning("文本内容太少，请提供完整的简历信息")
        else:
            st.session_state[RESUME_LOADING_KEY] = True
            st.session_state["_resume_loading_message"] = "解析文本中..."
            st.session_state["_resume_action_type"] = "parse_text"
            st.session_state["_resume_text_content"] = text_content
            st.session_state["_resume_text_use_ai"] = use_ai
            st.rerun()


def render_resume_detail_modal(resume_id: int, readonly: bool = False):
    """渲染简历详情模态框

    Args:
        resume_id: 简历ID
        readonly: 是否只读模式（只读模式下禁用编辑）
    """
    detail = get_resume_detail(resume_id)

    if not detail:
        st.error("加载详情失败")
        if st.button("关闭", key=f"close_error_{resume_id}"):
            st.session_state._edit_resume_id = None
            st.session_state._view_resume_id = None
            st.rerun()
        return

    st.markdown("""
    <div class="detail-modal">
        <div class="detail-header">
            <div class="detail-title">简历详情</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    profile = detail.get("profile") or {}

    # 基本信息
    st.markdown("**基本信息**")
    col1, col2 = st.columns(2)
    with col1:
        name_val = profile.get("name", "")
        phone_val = profile.get("phone", "")
        if readonly:
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>姓名</div><div class='resume-info-value'>{name_val or '-'}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>电话</div><div class='resume-info-value'>{phone_val or '-'}</div></div>", unsafe_allow_html=True)
        else:
            st.text_input("姓名", value=name_val, key=f"edit_name_{resume_id}")
            st.text_input("电话", value=phone_val, key=f"edit_phone_{resume_id}")
    with col2:
        email_val = profile.get("email", "")
        age_val = profile.get("age", "")
        if readonly:
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>邮箱</div><div class='resume-info-value'>{email_val or '-'}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>年龄</div><div class='resume-info-value'>{age_val or '-'}</div></div>", unsafe_allow_html=True)
        else:
            st.text_input("邮箱", value=email_val, key=f"edit_email_{resume_id}")
            st.text_input("年龄", value=str(age_val) if age_val else "", key=f"edit_age_{resume_id}")

    # 工作信息
    st.markdown("**工作信息**")
    col3, col4 = st.columns(2)
    with col3:
        position_val = profile.get("current_position", "")
        company_val = profile.get("current_company", "")
        if readonly:
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>当前职位</div><div class='resume-info-value'>{position_val or '-'}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>当前公司</div><div class='resume-info-value'>{company_val or '-'}</div></div>", unsafe_allow_html=True)
        else:
            st.text_input("当前职位", value=position_val, key=f"edit_position_{resume_id}")
            st.text_input("当前公司", value=company_val, key=f"edit_company_{resume_id}")
    with col4:
        exp_val = profile.get("experience_years", 0)
        salary_min = profile.get("salary_min", "")
        salary_max = profile.get("salary_max", "")
        salary_range = f"{salary_min}-{salary_max}" if salary_min and salary_max else ""
        if readonly:
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>工作年限</div><div class='resume-info-value'>{exp_val}年</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>期望薪资</div><div class='resume-info-value'>{salary_range or '-'}</div></div>", unsafe_allow_html=True)
        else:
            st.number_input("工作年限", value=exp_val, min_value=0, key=f"edit_exp_{resume_id}")
            st.text_input("期望薪资范围", value=salary_range, key=f"edit_salary_{resume_id}")

    # 教育信息
    st.markdown("**教育背景**")
    col5, col6 = st.columns(2)
    with col5:
        edu_val = profile.get("education", "")
        major_val = profile.get("major", "")
        if readonly:
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>学历</div><div class='resume-info-value'>{edu_val or '-'}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>专业</div><div class='resume-info-value'>{major_val or '-'}</div></div>", unsafe_allow_html=True)
        else:
            st.text_input("学历", value=edu_val, key=f"edit_edu_{resume_id}")
            st.text_input("专业", value=major_val, key=f"edit_major_{resume_id}")
    with col6:
        school_val = profile.get("school", "")
        if readonly:
            st.markdown(f"<div class='resume-info-item'><div class='resume-info-label'>学校</div><div class='resume-info-value'>{school_val or '-'}</div></div>", unsafe_allow_html=True)
        else:
            st.text_input("学校", value=school_val, key=f"edit_school_{resume_id}")

    # 技能展示
    skills = profile.get("skills", [])
    if skills:
        skills_html = "".join([f"<span class='skill-tag'>{s}</span>" for s in skills[:10]])
        st.markdown(f"""
        <div style="margin-top: 1rem;">
            <div class='resume-info-label'>技能标签</div>
            <div class="skill-tags">{skills_html}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # 操作按钮
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if not readonly:
            if st.button("保存修改", type="primary", use_container_width=True, key=f"save_{resume_id}"):
                # 收集表单数据
                profile_data = {
                    "name": st.session_state.get(f"edit_name_{resume_id}", ""),
                    "phone": st.session_state.get(f"edit_phone_{resume_id}", ""),
                    "email": st.session_state.get(f"edit_email_{resume_id}", ""),
                    "age": int(st.session_state.get(f"edit_age_{resume_id}", 0) or 0),
                    "current_position": st.session_state.get(f"edit_position_{resume_id}", ""),
                    "current_company": st.session_state.get(f"edit_company_{resume_id}", ""),
                    "experience_years": st.session_state.get(f"edit_exp_{resume_id}", 0),
                    "education": st.session_state.get(f"edit_edu_{resume_id}", ""),
                    "school": st.session_state.get(f"edit_school_{resume_id}", ""),
                    "major": st.session_state.get(f"edit_major_{resume_id}", ""),
                }
                # 解析薪资
                salary_str = st.session_state.get(f"edit_salary_{resume_id}", "")
                if salary_str and "-" in salary_str:
                    parts = salary_str.split("-")
                    try:
                        profile_data["salary_min"] = int(parts[0].strip())
                        profile_data["salary_max"] = int(parts[1].strip())
                    except ValueError:
                        pass

                result = update_resume_profile(resume_id, profile_data)
                if result.get("success"):
                    st.success("保存成功！")
                    st.session_state._edit_resume_id = None
                    st.session_state[RESUME_LIST_KEY] = None  # 清除列表缓存
                    st.rerun()
                else:
                    st.error(f"保存失败: {result.get('error', '未知错误')}")

    with col_btn2:
        if st.button("关闭", use_container_width=True, key=f"close_{resume_id}"):
            st.session_state._edit_resume_id = None
            st.session_state._view_resume_id = None
            st.rerun()


def show_loading_screen(message="处理中..."):
    """显示全屏loading"""
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
            font-size: 1.5rem;
            color: var(--accent-electric);
            margin-bottom: 1rem;
            animation: pulse 1.5s ease-in-out infinite;
        ">⚡</div>
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 0.9rem;
            color: var(--text-secondary);
        ">{message}</div>
        <div style="
            margin-top: 1rem;
            width: 120px;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-electric), transparent);
            animation: shimmer 1.5s ease-in-out infinite;
        "></div>
    </div>
    <style>
        @keyframes shimmer {{
            0% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.3; }}
        }}
    </style>
    """, unsafe_allow_html=True)


def execute_pending_action():
    """执行待处理的操作"""
    action_type = st.session_state.get("_resume_action_type")

    if action_type == "upload":
        file = st.session_state.get("_resume_upload_file")
        use_ai = st.session_state.get("_resume_upload_use_ai", False)
        result = upload_resume(file, use_ai)
        handle_parse_result(result)

    elif action_type == "parse_text":
        text = st.session_state.get("_resume_text_content")
        use_ai = st.session_state.get("_resume_text_use_ai", False)
        result = parse_text_resume(text, use_ai)
        handle_parse_result(result)

    elif action_type == "set_primary":
        resume_id = st.session_state.get("_resume_action_id")
        result = set_primary_resume(resume_id)
        if result.get("success"):
            st.session_state["_resume_action_message"] = ("success", result.get("message", "设置成功"))
            st.session_state[RESUME_LIST_KEY] = None  # 清除缓存
        else:
            st.session_state["_resume_action_message"] = ("error", result.get("error", "设置失败"))

    elif action_type == "delete":
        resume_id = st.session_state.get("_resume_action_id")
        result = delete_resume(resume_id)
        if result.get("success"):
            st.session_state["_resume_action_message"] = ("success", result.get("message", "删除成功"))
            st.session_state[RESUME_LIST_KEY] = None
        else:
            st.session_state["_resume_action_message"] = ("error", result.get("error", "删除失败"))

    # 清除状态
    st.session_state[RESUME_LOADING_KEY] = False
    st.session_state["_resume_loading_message"] = ""
    st.session_state["_resume_action_type"] = None
    st.session_state["_resume_upload_file"] = None
    st.session_state["_resume_text_content"] = None
    st.rerun()


def handle_parse_result(result):
    """处理解析结果"""
    if result.get("success"):
        st.session_state["_resume_action_message"] = ("success", "简历解析成功！")
        st.session_state[RESUME_LIST_KEY] = None  # 清除列表缓存
        st.session_state["_resume_parse_result"] = result
    else:
        error_msg = result.get("error", "解析失败")
        st.session_state["_resume_action_message"] = ("error", error_msg)


def format_created_time(created_at):
    """格式化创建时间"""
    if not created_at:
        return "-"
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", ""))
        return dt.strftime("%m-%d %H:%M")
    except:
        return created_at[:10] if len(created_at) > 10 else created_at


def init_session_state():
    """初始化 session state"""
    if RESUME_LIST_KEY not in st.session_state:
        st.session_state[RESUME_LIST_KEY] = None
    if RESUME_LOADING_KEY not in st.session_state:
        st.session_state[RESUME_LOADING_KEY] = False
    if RESUME_DETAIL_KEY not in st.session_state:
        st.session_state[RESUME_DETAIL_KEY] = None
    if "_edit_resume_id" not in st.session_state:
        st.session_state._edit_resume_id = None
    if "_view_resume_id" not in st.session_state:
        st.session_state._view_resume_id = None


# ========== 主入口 ==========

def main():
    """Streamlit 页面主入口"""
    init_session_state()
    render_resume_manager()

    # 显示操作结果消息
    msg = st.session_state.get("_resume_action_message")
    if msg:
        msg_type, msg_text = msg
        if msg_type == "success":
            st.success(msg_text)
        else:
            st.error(msg_text)
        st.session_state["_resume_action_message"] = None


if __name__ == "__main__":
    main()