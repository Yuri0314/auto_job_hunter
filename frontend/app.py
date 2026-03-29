"""
Auto Job Hunter - Streamlit Web GUI

设计：流程引导式界面
- 风格：Obsidian Terminal (深黑 + 电蓝霓虹)
- 交互：步骤式引导，每步完成后提示下一步
- 简化：减少选项，突出核心操作
"""

import os
import streamlit as st
import requests
from datetime import datetime

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


# ========== 页面配置 ==========

st.set_page_config(
    page_title="Auto Job Hunter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",  # 收起侧边栏，聚焦主流程
)


# ========== OBSIDIAN TERMINAL 设计系统 ==========

st.markdown("""
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

    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,212,255,0.08) 0%, transparent 50%),
            radial-gradient(ellipse 60% 40% at 100% 100%, rgba(244,114,182,0.06) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }

    /* 隐藏侧边栏 */
    [data-testid="stSidebar"] { display: none; }

    /* 主内容区居中 */
    [data-testid="stMainBlockContainer"] {
        max-width: 900px !important;
        margin: 0 auto !important;
        padding: 2rem !important;
    }

    /* ========== 进度指示器 ========== */
    .progress-bar {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0 3rem 0;
    }

    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
    }

    .progress-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        transition: all 0.3s ease;
    }

    .progress-circle.pending {
        background: var(--bg-glass);
        border: 2px solid var(--border-subtle);
        color: var(--text-muted);
    }

    .progress-circle.active {
        background: rgba(0, 212, 255, 0.15);
        border: 2px solid var(--accent-electric);
        color: var(--accent-electric);
        box-shadow: 0 0 20px rgba(0,212,255,0.3);
        animation: pulse 2s infinite;
    }

    .progress-circle.done {
        background: rgba(74, 222, 128, 0.15);
        border: 2px solid var(--accent-green);
        color: var(--accent-green);
        box-shadow: 0 0 15px rgba(74,222,128,0.2);
    }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(0,212,255,0.3); }
        50% { box-shadow: 0 0 35px rgba(0,212,255,0.5); }
    }

    .progress-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }

    .progress-label.pending { color: var(--text-muted); }
    .progress-label.active { color: var(--accent-electric); }
    .progress-label.done { color: var(--accent-green); }

    .progress-connector {
        width: 80px;
        height: 2px;
        background: var(--border-subtle);
        margin-top: 30px;
    }

    .progress-connector.done {
        background: linear-gradient(90deg, var(--accent-green), var(--accent-electric));
    }

    /* ========== 步骤卡片 ========== */
    .step-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        position: relative;
    }

    .step-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-glow), transparent);
        opacity: 0.5;
    }

    .step-card.active::before {
        opacity: 1;
        background: linear-gradient(90deg, transparent, var(--accent-electric), transparent);
    }

    .step-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .step-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: var(--accent-electric);
        background: rgba(0,212,255,0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        border: 1px solid var(--accent-electric);
    }

    .step-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .step-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        letter-spacing: 0.05em;
    }

    .step-status.done {
        background: rgba(74,222,128,0.15);
        color: var(--accent-green);
        border: 1px solid var(--accent-green);
    }

    .step-status.pending {
        background: var(--bg-glass);
        color: var(--text-muted);
        border: 1px solid var(--border-subtle);
    }

    /* ========== 简历信息展示 ========== */
    .resume-info {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin-top: 1rem;
    }

    .info-item {
        padding: 0.75rem 1rem;
        background: var(--bg-glass);
        border-radius: 8px;
        border: 1px solid var(--border-subtle);
    }

    .info-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: var(--text-muted);
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .info-value {
        font-size: 0.95rem;
        color: var(--text-primary);
        margin-top: 0.25rem;
    }

    /* ========== 引导提示 ========== */
    .guide-box {
        background: rgba(0,212,255,0.05);
        border: 1px solid var(--accent-electric);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 1.5rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .guide-icon {
        font-size: 1.5rem;
        color: var(--accent-electric);
        filter: drop-shadow(0 0 8px rgba(0,212,255,0.4));
    }

    .guide-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: var(--accent-electric);
    }

    /* ========== Streamlit组件覆盖 ========== */
    .stButton button {
        background: var(--bg-card) !important;
        border: 1px solid var(--accent-electric) !important;
        color: var(--accent-electric) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 0 15px rgba(0,212,255,0.1) !important;
    }

    .stButton button:hover {
        background: rgba(0,212,255,0.1) !important;
        box-shadow: 0 0 25px rgba(0,212,255,0.3) !important;
        transform: translateY(-2px) !important;
    }

    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #0891b2, #00d4ff) !important;
        border: none !important;
        color: var(--bg-deep) !important;
        box-shadow: 0 0 30px rgba(0,212,255,0.4) !important;
    }

    .stTextInput input, .stTextArea textarea {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    .stTextInput input:focus {
        border-color: var(--accent-electric) !important;
        box-shadow: 0 0 10px rgba(0,212,255,0.2) !important;
    }

    .stSelectbox [data-baseweb="select"] {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 8px !important;
    }

    .stMultiselect [data-baseweb="select"] {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 8px !important;
    }

    .stCheckbox [data-baseweb="checkbox"] {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-subtle) !important;
    }

    .stCheckbox label {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stCheckbox label p {
        color: var(--text-primary) !important;
    }

    .stSlider [data-baseweb="slider-thumb"] {
        background: var(--accent-electric) !important;
    }

    label, .stCaption {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    label p {
        color: var(--text-primary) !important;
    }

    /* Placeholder 文字 */
    input::placeholder, textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* 下拉选择框选项 */
    [data-baseweb="select"] [role="option"] {
        color: var(--text-primary) !important;
    }

    /* 多选框已选标签 */
    [data-baseweb="tag"] {
        background: rgba(0,212,255,0.15) !important;
        color: var(--accent-electric) !important;
    }

    .stSuccess {
        background: rgba(74,222,128,0.1) !important;
        border: 1px solid var(--accent-green) !important;
        color: var(--accent-green) !important;
        border-radius: 12px !important;
    }

    .stError {
        background: rgba(248,113,113,0.1) !important;
        border: 1px solid var(--accent-red) !important;
        color: var(--accent-red) !important;
        border-radius: 12px !important;
    }

    .stWarning {
        background: rgba(251,191,36,0.1) !important;
        border: 1px solid var(--accent-gold) !important;
        color: var(--accent-gold) !important;
        border-radius: 12px !important;
    }

    .stInfo {
        background: rgba(0,212,255,0.1) !important;
        border: 1px solid var(--accent-electric) !important;
        color: var(--accent-electric) !important;
        border-radius: 12px !important;
    }

    /* 隐藏顶部和底部 */
    #MainMenu, header, footer, [data-testid="stStatusWidget"] { display: none; }

    /* 结果列表 */
    .job-list {
        margin-top: 1rem;
    }

    .job-item {
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }

    .job-item:hover {
        border-color: var(--accent-electric);
        transform: translateX(4px);
    }

    .job-title {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: var(--text-primary);
    }

    .job-company {
        color: var(--text-muted);
        font-size: 0.85rem;
    }

    .job-salary {
        font-family: 'JetBrains Mono', monospace;
        color: var(--accent-gold);
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ========== Session State ==========

if "step" not in st.session_state:
    st.session_state.step = 1  # 1:简历, 2:搜索, 3:投递结果, 4:设置, 5:投递记录
if "resume_parsed" not in st.session_state:
    st.session_state.resume_parsed = False
if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "loading" not in st.session_state:
    st.session_state.loading = False
if "loading_message" not in st.session_state:
    st.session_state.loading_message = ""
if "_history_data" not in st.session_state:
    st.session_state._history_data = None
if "_settings_data" not in st.session_state:
    st.session_state._settings_data = None
if "_platform_status" not in st.session_state:
    st.session_state._platform_status = None
if "_keyword_suggestions" not in st.session_state:
    st.session_state._keyword_suggestions = []
if "_search_keywords" not in st.session_state:
    st.session_state._search_keywords = ""


# ========== API Functions ==========

def api_get_resume_status():
    try:
        r = requests.get(f"{API_BASE}/resume/status", timeout=5)
        return r.json()
    except:
        return {"has_resume": False}


def api_upload_resume(file, use_ai=False):
    try:
        files = {"file": (file.name, file, "application/pdf")}
        data = {"use_ai": str(use_ai).lower()}
        r = requests.post(f"{API_BASE}/resume/upload", files=files, data=data, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_parse_resume(path, use_ai=False):
    try:
        r = requests.post(f"{API_BASE}/resume/parse", json={"file_path": path, "use_ai": use_ai}, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_search_jobs(keywords, platforms, city, auto_apply=False, greeting=""):
    try:
        # 正确的endpoint是 /applications/search-and-apply
        r = requests.post(f"{API_BASE}/applications/search-and-apply", json={
            "keywords": keywords,
            "platforms": platforms,
            "city": city,
            "auto_apply": auto_apply,
            "greeting_template": greeting,  # 后端参数名是 greeting_template
            "max_count": 20,
        }, timeout=120)  # 增加timeout，因为搜索需要时间
        result = r.json()
        # 记录搜索使用的关键词
        result["search_keywords"] = keywords
        # 映射后端的 filtered 字段到 frontend 的 filtered_jobs
        if "filtered" in result and "filtered_jobs" not in result:
            result["filtered_jobs"] = result["filtered"]
        return result
    except Exception as e:
        return {"error": str(e)}


def api_fetch_applications():
    try:
        r = requests.get(f"{API_BASE}/applications", timeout=10)
        return r.json()
    except:
        return {"items": []}


# ========== 进度条 ==========

def render_progress_bar():
    current_step = st.session_state.step

    st.markdown("""
    <div class="progress-bar">
        <div class="progress-step">
            <div class="progress-circle {step1_class}">{step1_icon}</div>
            <div class="progress-label {step1_class}">简历</div>
        </div>
        <div class="progress-connector {conn1_class}"></div>
        <div class="progress-step">
            <div class="progress-circle {step2_class}">{step2_icon}</div>
            <div class="progress-label {step2_class}">搜索</div>
        </div>
        <div class="progress-connector {conn2_class}"></div>
        <div class="progress-step">
            <div class="progress-circle {step3_class}">{step3_icon}</div>
            <div class="progress-label {step3_class}">投递</div>
        </div>
    </div>
    """.format(
        step1_class="done" if current_step > 1 else "active" if current_step == 1 else "pending",
        step1_icon="✓" if current_step > 1 else "1",
        step2_class="done" if current_step > 2 else "active" if current_step == 2 else "pending",
        step2_icon="✓" if current_step > 2 else "2",
        step3_class="done" if current_step > 3 else "active" if current_step == 3 else "pending",
        step3_icon="✓" if current_step > 3 else "3",
        conn1_class="done" if current_step > 1 else "",
        conn2_class="done" if current_step > 2 else "",
    ), unsafe_allow_html=True)


# ========== Logo ==========

def render_logo():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="font-family: 'JetBrains Mono'; font-size: 2rem; font-weight: 700; color: var(--accent-electric); filter: drop-shadow(0 0 10px rgba(0,212,255,0.3));">
            ⚡ AUTO_JOB_HUNTER
        </div>
        <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
            // 智能求职自动化系统
        </div>
    </div>
    """, unsafe_allow_html=True)


# ========== 步骤1: 简历 ==========

def step_resume():
    # 首次加载时，设置loading状态
    if not st.session_state.initialized:
        st.session_state.loading = True
        st.session_state.loading_message = "正在加载简历信息..."
        st.rerun()

    if st.session_state.resume_parsed:
        # 简历已解析完成
        render_resume_done()
    else:
        # 需要上传简历
        render_resume_upload()


def render_resume_done():
    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number">STEP_01</span>
            <span class="step-title">简历解析</span>
            <span class="step-status done">已完成</span>
        </div>
    """, unsafe_allow_html=True)

    # 优先使用简历解析的数据 (extracted_data)
    data = st.session_state.resume_data or {}
    profile = data.get("extracted_data", {})

    # 如果没有简历数据，尝试从 API 获取
    if not profile.get("name"):
        try:
            r = requests.get(f"{API_BASE}/user/profile", timeout=5)
            if r.ok:
                profile = r.json()
        except:
            pass

    st.markdown("""
    <div class="resume-info">
        <div class="info-item">
            <div class="info-label">姓名</div>
            <div class="info-value">{name}</div>
        </div>
        <div class="info-item">
            <div class="info-label">学历</div>
            <div class="info-value">{edu}</div>
        </div>
        <div class="info-item">
            <div class="info-label">工作年限</div>
            <div class="info-value">{exp}年</div>
        </div>
        <div class="info-item">
            <div class="info-label">所在城市</div>
            <div class="info-value">{city}</div>
        </div>
    </div>
    """.format(
        name=profile.get("name", "-"),
        edu=profile.get("education", "-"),
        exp=profile.get("experience_years", "-"),
        city=profile.get("city", "-"),
    ), unsafe_allow_html=True)

    # 显示技能
    skills = profile.get("skills", [])
    if skills:
        st.markdown(f"""
        <div style="margin-top: 1rem; padding: 0.75rem 1rem; background: var(--bg-glass); border-radius: 8px; border: 1px solid var(--border-subtle);">
            <div class="info-label">核心技能</div>
            <div style="color: var(--text-primary); margin-top: 0.25rem;">{', '.join(skills[:6])}</div>
        </div>
        """, unsafe_allow_html=True)

    # 显示历史简历文件信息
    resume_file = data.get("resume_file", "")
    if resume_file:
        import os
        file_name = os.path.basename(resume_file) if resume_file else "resume.pdf"

        # 简历文件块
        st.markdown(f"""
        <div style="margin-top: 1rem; padding: 0.75rem 1rem; background: var(--bg-glass); border-radius: 8px; border: 1px solid var(--border-subtle);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="info-label">📄 简历文件</div>
                    <div style="color: var(--text-primary); margin-top: 0.25rem; font-family: 'JetBrains Mono'; font-size: 0.85rem;">{file_name}</div>
                    <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.25rem;">{resume_file}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 下载按钮 - 只有点击时才触发
        if st.button("📥 下载简历", key="btn_download_resume"):
            try:
                r = requests.get(f"{API_BASE}/resume/download", timeout=10)
                if r.ok:
                    st.download_button(
                        label="确认下载",
                        data=r.content,
                        file_name=file_name,
                        mime="application/pdf",
                        key="download_resume_confirm"
                    )
                else:
                    st.error("下载失败")
            except Exception as e:
                st.error(f"下载失败: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # 引导下一步
    st.markdown("""
    <div class="guide-box">
        <span class="guide-icon">→</span>
        <span class="guide-text">简历已就绪，点击下方按钮开始搜索职位</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("开始搜索职位 →", type="primary", use_container_width=True):
        st.session_state.step = 2
        st.rerun()

    # 重新上传选项
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("重新上传简历"):
        uploaded = st.file_uploader("上传新简历 (PDF)", type=["pdf"])
        use_ai = st.checkbox("使用 AI 模式", value=False, key="reparse_ai")
        if uploaded and st.button("重新解析"):
            result = api_upload_resume(uploaded, use_ai)
            if result.get("success"):
                st.session_state.resume_data = result
                st.success("解析成功！")
                st.rerun()
            else:
                st.error(result.get("error", "解析失败"))


def render_resume_upload():
    st.markdown("""
    <div class="step-card active">
        <div class="step-header">
            <span class="step-number">STEP_01</span>
            <span class="step-title">简历解析</span>
            <span class="step-status pending">待完成</span>
        </div>
        <div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem;">
            上传简历后系统会自动提取关键信息，用于智能匹配职位
        </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("上传 PDF 简历", type=["pdf"])
    use_ai = st.checkbox("使用 AI 模式（更准确）", value=False)

    if uploaded:
        if st.button("解析简历", type="primary", use_container_width=True):
            # 保存文件引用，设置loading状态
            st.session_state._resume_file = uploaded
            st.session_state._resume_use_ai = use_ai
            st.session_state.loading = True
            st.session_state.loading_message = "正在解析简历..."
            st.session_state._resume_parse_pending = True
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ========== 步骤2: 搜索 ==========

def step_search():
    # 返回上一步按钮
    if st.button("← 返回简历页", key="back_to_resume"):
        st.session_state.step = 1
        st.rerun()

    st.markdown("""
    <div class="step-card active">
        <div class="step-header">
            <span class="step-number">STEP_02</span>
            <span class="step-title">职位搜索</span>
        </div>
        <div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem;">
            设置搜索条件，系统会自动在多个平台查找匹配职位
        </div>
    """, unsafe_allow_html=True)

    # 使用初始化时缓存的预填值
    default_keywords = st.session_state.get("_prefill_keywords", "")
    default_city = st.session_state.get("_prefill_city", "")

    # 如果缓存中没有，尝试从用户画像获取（备用逻辑）
    if not default_keywords:
        profile = st.session_state.get("_user_profile", {})
        if profile:
            target_positions = profile.get("target_positions", [])
            skills = profile.get("skills", [])
            if target_positions:
                default_keywords = target_positions[0]
            elif skills:
                default_keywords = skills[0]

    if not default_city:
        profile = st.session_state.get("_user_profile", {})
        if profile:
            default_city = profile.get("city", "") or ""

    # 显示关键词建议
    suggestions = st.session_state.get("_keyword_suggestions", [])
    if suggestions:
        st.markdown("<div style='margin-bottom: 0.5rem;'>", unsafe_allow_html=True)
        st.caption("推荐关键词（点击添加）:")
        suggestion_cols = st.columns(min(len(suggestions), 5))
        for i, kw in enumerate(suggestions[:5]):
            with suggestion_cols[i]:
                if st.button(kw, key=f"kw_{i}", use_container_width=True):
                    current = st.session_state.get("_search_keywords", "")
                    if current:
                        new_value = f"{current} {kw}"
                    else:
                        new_value = kw
                    # 同时更新两个状态：一个是我们的记录，一个是 text_input 的实际状态
                    st.session_state._search_keywords = new_value
                    st.session_state.keywords_input = new_value
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Initialize search keywords from prefill
    if not st.session_state.get("_search_keywords"):
        st.session_state._search_keywords = default_keywords
        # 同步到 text_input 的 key
        st.session_state.keywords_input = default_keywords

    keywords = st.text_input(
        "搜索关键词",
        placeholder="如: Python后端、产品经理（可输入多个，空格分隔）",
        value=st.session_state._search_keywords,
        key="keywords_input"
    )
    # Sync to session state
    st.session_state._search_keywords = keywords

    col1, col2 = st.columns(2)
    with col1:
        platforms = st.multiselect("选择平台", ["boss", "liepin"], default=["boss"])
    with col2:
        city = st.text_input(
            "目标城市",
            placeholder="如: 北京",
            value=default_city
        )

    # 显示预填提示
    if suggestions:
        st.caption(f"已从简历提取 {len(suggestions)} 个推荐关键词，点击上方按钮快速添加")

    # 投递选项
    st.markdown("<br>", unsafe_allow_html=True)
    auto_apply = st.checkbox("自动投递符合条件的职位", value=False)

    greeting = ""
    if auto_apply:
        greeting = st.text_area("打招呼语", placeholder="您好，我对这个职位很感兴趣...", height=60)

    st.markdown("</div>", unsafe_allow_html=True)

    # 如果有上次搜索结果，显示快速访问
    if st.session_state.search_results:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("查看上次搜索结果", expanded=False):
            last_result = st.session_state.search_results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("发现职位", last_result.get("total_found", 0))
            with col2:
                st.metric("符合条件", last_result.get("filtered_jobs", 0) or last_result.get("filtered", 0))
            with col3:
                st.metric("已投递", last_result.get("applied", 0) or last_result.get("success_count", 0))

            if st.button("查看详细结果", key="view_last_results"):
                st.session_state.step = 3
                st.rerun()

    # 搜索按钮
    if st.button("开始搜索 →", type="primary", use_container_width=True):
        if not keywords:
            st.warning("请输入搜索关键词")
        elif not platforms:
            st.warning("请选择至少一个平台")
        else:
            # 保存搜索参数，设置loading状态
            st.session_state._search_params = {
                "keywords": keywords,
                "platforms": platforms,
                "city": city,
                "auto_apply": auto_apply,
                "greeting": greeting,
            }
            st.session_state.loading = True
            st.session_state.loading_message = "正在搜索职位..."
            st.session_state._search_pending = True
            st.rerun()


# ========== 步骤3: 结果 ==========

def step_results():
    # 返回按钮
    col_back1, col_back2 = st.columns(2)
    with col_back1:
        if st.button("← 返回修改搜索", key="back_to_search"):
            st.session_state.step = 2
            st.rerun()
    with col_back2:
        if st.button("← 返回简历页", key="back_to_resume_from_result"):
            st.session_state.step = 1
            st.rerun()

    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number">STEP_03</span>
            <span class="step-title">投递结果</span>
            <span class="step-status done">已完成</span>
        </div>
    """, unsafe_allow_html=True)

    result = st.session_state.search_results or {}

    # 显示本次搜索使用的关键词
    search_keywords = result.get("search_keywords", "")
    if search_keywords:
        st.markdown(f"""
        <div style="padding: 0.75rem 1rem; background: var(--bg-glass); border-radius: 8px; margin-bottom: 1rem; border: 1px solid var(--border-subtle);">
            <span style="color: var(--text-muted); font-size: 0.85rem;">搜索关键词：</span>
            <span style="color: var(--accent-electric); font-family: 'JetBrains Mono';">{search_keywords}</span>
        </div>
        """, unsafe_allow_html=True)

    # 统计数据
    total_found = result.get("total_found", 0)
    filtered_jobs = result.get("filtered_jobs", 0)
    applied_count = result.get("applied", 0) or result.get("success_count", 0)

    # 统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: var(--bg-glass); border-radius: 12px; border: 1px solid var(--border-subtle);">
            <div style="font-family: 'JetBrains Mono'; font-size: 2rem; font-weight: 700; color: var(--accent-electric);">{total_found}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">发现职位</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: var(--bg-glass); border-radius: 12px; border: 1px solid var(--border-subtle);">
            <div style="font-family: 'JetBrains Mono'; font-size: 2rem; font-weight: 700; color: var(--accent-gold);">{filtered_jobs}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">符合条件</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: var(--bg-glass); border-radius: 12px; border: 1px solid var(--border-subtle);">
            <div style="font-family: 'JetBrains Mono'; font-size: 2rem; font-weight: 700; color: var(--accent-green);">{applied_count}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">已投递</div>
        </div>
        """, unsafe_allow_html=True)

    # 职位列表
    jobs = result.get("jobs", [])
    if jobs:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="job-list">', unsafe_allow_html=True)
        for job in jobs[:15]:
            st.markdown(f"""
            <div class="job-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="job-title">{job.get('title', '未知')}</div>
                        <div class="job-company">{job.get('company', '未知公司')} · {job.get('city', '-')}</div>
                    </div>
                    <div class="job-salary">{job.get('salary', '面议')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # 继续操作
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("继续搜索", use_container_width=True):
            st.session_state.step = 2
            st.session_state.search_results = None
            st.rerun()
    with col2:
        if st.button("查看投递记录", use_container_width=True):
            st.session_state._history_pending = True
            st.session_state.loading = True
            st.session_state.loading_message = "加载投递记录..."
            st.session_state.step = 5
            st.rerun()


# ========== 设置页面 ==========

def step_settings():
    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number">SETTINGS</span>
            <span class="step-title">系统设置</span>
        </div>
    """, unsafe_allow_html=True)

    # 使用缓存数据或触发loading
    if st.session_state.get("_settings_data") is None:
        st.session_state._settings_pending = True
        st.session_state.loading = True
        st.session_state.loading_message = "加载设置..."
        st.rerun()

    configs = st.session_state._settings_data or {}

    st.markdown("<br>", unsafe_allow_html=True)

    # AI配置
    st.markdown("**🤖 AI 服务**")

    ai_key = configs.get("openai_api_key", {})
    key_value = ai_key.get("effective_value", "")

    # 检查是否是有效的API key（排除占位符）
    is_valid_key = key_value and not key_value.startswith("your_") and len(key_value) > 10

    if is_valid_key:
        st.success("✓ API Key 已配置")
    elif key_value:
        st.warning("○ API Key 无效（请配置真实的Key）")
    else:
        st.warning("○ API Key 未配置")

    new_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model = st.selectbox("模型", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])

    if st.button("保存 AI 配置"):
        updates = {"openai_model": model}
        if new_key:
            updates["openai_api_key"] = new_key
        try:
            requests.post(f"{API_BASE}/settings/batch", json=updates, timeout=10)
            st.success("保存成功！")
            # 清除缓存以刷新
            st.session_state._settings_data = None
            st.session_state._settings_pending = True
            st.session_state.loading = True
            st.session_state.loading_message = "刷新设置..."
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.markdown("<br>", unsafe_allow_html=True)

    # 平台账号
    st.markdown("**🔐 平台账号**")

    # 刷新按钮
    if st.button("🔄 刷新登录状态", key="refresh_platforms"):
        st.session_state._settings_pending = True
        st.session_state.loading = True
        st.session_state.loading_message = "刷新状态..."
        st.rerun()

    platform_status = st.session_state.get("_platform_status") or []

    platforms_info = [
        {"name": "BOSS直聘", "key": "boss"},
        {"name": "猎聘", "key": "liepin"},
    ]

    for p in platforms_info:
        status = next((s for s in platform_status if s["platform"] == p["key"]), {})
        is_logged = status.get("cookie_saved", False)

        col_a, col_b = st.columns([3, 1])
        with col_a:
            if is_logged:
                st.success(f"✓ {p['name']} 已登录")
            else:
                st.warning(f"○ {p['name']} 未登录")
        with col_b:
            if st.button(f"登录", key=f"login_{p['key']}"):
                try:
                    # 正确路径是 /system/login 而不是 /auth/login
                    r = requests.post(f"{API_BASE}/system/login/{p['key']}", timeout=30)
                    if r.ok:
                        data = r.json()
                        if data.get("status") == "started":
                            st.success("浏览器已打开，请完成登录")
                        elif data.get("status") == "already_running":
                            st.info("登录任务正在进行中")
                        else:
                            st.warning(data.get("message", "未知状态"))
                    else:
                        st.error(f"请求失败: {r.status_code}")
                except Exception as e:
                    st.error(str(e))

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("返回首页", use_container_width=True):
        st.session_state.step = 1
        st.rerun()


# ========== 投递记录页面 ==========

def step_history():
    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number">HISTORY</span>
            <span class="step-title">投递记录</span>
        </div>
    """, unsafe_allow_html=True)

    # 如果没有缓存数据，触发loading
    if st.session_state.get("_history_data") is None:
        st.session_state._history_pending = True
        st.session_state.loading = True
        st.session_state.loading_message = "加载投递记录..."
        st.rerun()

    result = st.session_state._history_data or {}

    items = result.get("items", [])

    if items:
        for app in items[:20]:
            status = app.get("status", "pending")
            status_color = "var(--accent-green)" if status == "success" else "var(--accent-red)" if status == "failed" else "var(--accent-gold)"
            status_text = "成功" if status == "success" else "失败" if status == "failed" else "待处理"

            st.markdown(f"""
            <div class="job-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="job-title">{app.get('job_title', '未知')}</div>
                        <div class="job-company">{app.get('company', '未知')} · {app.get('platform', '-')}</div>
                    </div>
                    <div style="font-family: 'JetBrains Mono'; color: {status_color}; font-size: 0.85rem;">{status_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.caption(f"共 {result.get('total', len(items))} 条记录")
    else:
        st.info("暂无投递记录")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("返回首页", use_container_width=True):
        st.session_state.step = 1
        st.rerun()


# ========== 全局Loading界面 ==========

def show_loading_screen(message="加载中..."):
    """显示全屏loading，遮挡所有旧内容"""
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


# ========== 主渲染 ==========

# 全局loading检查 - 只有明确的异步任务才需要loading
if st.session_state.loading:
    # 显示全屏loading
    show_loading_screen(st.session_state.loading_message)

    # 根据任务类型执行
    if not st.session_state.initialized:
        # 初始化加载简历信息和用户画像
        status = api_get_resume_status()
        if status.get("has_resume"):
            st.session_state.resume_parsed = True
            st.session_state.resume_data = status

        # 加载用户画像用于预填
        try:
            r = requests.get(f"{API_BASE}/user/profile", timeout=5)
            if r.ok:
                profile = r.json()
                st.session_state._user_profile = profile
                # Generate keyword suggestions from profile
                suggestions = []
                # Add target positions first
                target_positions = profile.get("target_positions", [])
                suggestions.extend(target_positions[:3])
                # Add top skills
                skills = profile.get("skills", [])
                suggestions.extend(skills[:3])
                # Remove duplicates while preserving order
                seen = set()
                unique_suggestions = []
                for s in suggestions:
                    if s and s not in seen:
                        seen.add(s)
                        unique_suggestions.append(s)
                st.session_state._keyword_suggestions = unique_suggestions
                # Set default prefill (first suggestion)
                if unique_suggestions:
                    st.session_state._prefill_keywords = unique_suggestions[0]
                st.session_state._prefill_city = profile.get("city", "")
        except:
            pass

        st.session_state.initialized = True

    elif st.session_state.get("_search_pending"):
        # 执行搜索任务
        params = st.session_state._search_params
        result = api_search_jobs(
            params["keywords"],
            params["platforms"],
            params["city"],
            params["auto_apply"],
            params["greeting"],
        )
        st.session_state.search_results = result
        st.session_state._search_pending = False
        st.session_state._search_params = None
        if not result.get("error"):
            st.session_state.step = 3

    elif st.session_state.get("_resume_parse_pending"):
        # 执行简历解析任务
        result = api_upload_resume(st.session_state._resume_file, st.session_state._resume_use_ai)
        st.session_state._resume_parse_pending = False
        st.session_state._resume_file = None
        st.session_state._resume_use_ai = None
        if result.get("success"):
            st.session_state.resume_parsed = True
            st.session_state.resume_data = result

    elif st.session_state.get("_history_pending"):
        # 加载投递记录
        st.session_state._history_data = api_fetch_applications()
        st.session_state._history_pending = False

    elif st.session_state.get("_settings_pending"):
        # 加载设置数据
        try:
            r1 = requests.get(f"{API_BASE}/settings/items", timeout=5)
            st.session_state._settings_data = r1.json() if r1.ok else {}
        except:
            st.session_state._settings_data = {}

        try:
            r2 = requests.get(f"{API_BASE}/system/platforms", timeout=5)
            st.session_state._platform_status = r2.json() if r2.ok else []
        except:
            st.session_state._platform_status = []

        st.session_state._settings_pending = False

    else:
        # 没有待执行任务，直接结束loading
        pass

    # 完成loading
    st.session_state.loading = False
    st.session_state.loading_message = ""
    st.rerun()

else:
    # 正常渲染流程
    render_logo()

    step = st.session_state.step

    # 只在求职流程页面（1-3）显示进度条
    if step <= 3:
        render_progress_bar()
    elif step == 4:
        # 设置页面标题
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 600; color: var(--accent-electric);">
                ⚙️ 系统设置
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">
                AI服务 · 平台账号 · 系统配置
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif step == 5:
        # 投递记录页面标题
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 600; color: var(--accent-electric);">
                📊 投递记录
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">
                查看历史投递 · 追踪求职进度
            </div>
        </div>
        """, unsafe_allow_html=True)

    if step == 1:
        step_resume()
    elif step == 2:
        step_search()
    elif step == 3:
        step_results()
    elif step == 4:
        step_settings()
    elif step == 5:
        step_history()

    # ========== 底部导航 ==========
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 投递记录", use_container_width=True):
            st.session_state._history_pending = True
            st.session_state.loading = True
            st.session_state.loading_message = "加载投递记录..."
            st.session_state.step = 5
            st.rerun()
    with col2:
        if st.button("🏠 返回首页", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("⚙️ 设置", use_container_width=True):
            st.session_state._settings_pending = True
            st.session_state.loading = True
            st.session_state.loading_message = "加载设置..."
            st.session_state.step = 4
            st.rerun()


if __name__ == "__main__":
    pass