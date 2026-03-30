"""UI样式定义"""

# 颜色系统 - 改进对比度
COLORS = {
    "bg_deep": "#0f0f14",          # 稍微亮一点的深色背景
    "bg_primary": "#16161d",       # 主背景色
    "bg_card": "rgba(30, 30, 40, 0.9)",  # 卡片背景
    "bg_glass": "rgba(255, 255, 255, 0.05)",
    "text_primary": "#ffffff",      # 纯白色主文字
    "text_secondary": "#c4c4c8",   # 更亮的次要文字
    "text_muted": "#9ca3af",       # 更亮的muted文字
    "text_label": "#e5e7eb",       # 标签文字颜色
    "accent_electric": "#00d4ff",
    "accent_gold": "#fbbf24",
    "accent_green": "#4ade80",
    "accent_red": "#f87171",
    "accent_magenta": "#f472b6",
    "border_glow": "rgba(0, 212, 255, 0.3)",
    "border_subtle": "rgba(255, 255, 255, 0.12)",
}

# 全局CSS
GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-deep: #0f0f14;
        --bg-primary: #16161d;
        --bg-card: rgba(30, 30, 40, 0.9);
        --bg-glass: rgba(255, 255, 255, 0.05);
        --text-primary: #ffffff;
        --text-secondary: #c4c4c8;
        --text-muted: #9ca3af;
        --text-label: #e5e7eb;
        --accent-electric: #00d4ff;
        --accent-gold: #fbbf24;
        --accent-green: #4ade80;
        --accent-red: #f87171;
        --accent-magenta: #f472b6;
        --border-glow: rgba(0, 212, 255, 0.3);
        --border-subtle: rgba(255, 255, 255, 0.12);
    }

    .stApp {
        background: var(--bg-deep) !important;
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary) !important;
    }

    /* 主内容区 */
    [data-testid="stMainBlockContainer"] {
        max-width: 1200px !important;
        padding: 1.5rem !important;
    }

    /* 隐藏顶部和底部 */
    #MainMenu, header, footer, [data-testid="stStatusWidget"] { display: none; }

    /* ========== 文字标签样式 - 关键修复 ========== */

    /* 所有label文字 */
    label, .stMarkdown label, [data-testid="stWidgetLabel"] {
        color: var(--text-label) !important;
        font-weight: 500 !important;
    }

    /* Streamlit组件标签 */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label,
    .stMultiSelect > label, .stNumberInput > label, .stCheckbox label {
        color: var(--text-label) !important;
    }

    /* 段落和普通文字 */
    p, span, div.stMarkdown {
        color: var(--text-primary) !important;
    }

    /* 标题 */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }

    /* ========== 输入框样式 ========== */

    .stTextInput input, .stTextArea textarea {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-electric) !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
    }

    /* ========== 下拉选择框 ========== */
    .stSelectbox div[data-baseweb="select"] > div {
        background: var(--bg-primary) !important;
        border-color: var(--border-subtle) !important;
    }

    .stMultiSelect div[data-baseweb="tag"] {
        background: rgba(0, 212, 255, 0.15) !important;
        color: var(--accent-electric) !important;
    }

    /* ========== 按钮样式 ========== */
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
        background: rgba(0,212,255,0.15) !important;
        box-shadow: 0 0 20px rgba(0,212,255,0.3) !important;
    }

    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #0891b2, #00d4ff) !important;
        border: none !important;
        color: var(--bg-deep) !important;
    }

    /* ========== 复选框 ========== */
    .stCheckbox label {
        color: var(--text-primary) !important;
    }

    .stCheckbox div[data-testid="stMarkdownContainer"] p {
        color: var(--text-primary) !important;
    }

    /* ========== 成功/错误提示 ========== */
    .stSuccess {
        background: rgba(74,222,128,0.15) !important;
        border: 1px solid var(--accent-green) !important;
        color: var(--accent-green) !important;
        border-radius: 8px !important;
    }

    .stError {
        background: rgba(248,113,113,0.15) !important;
        border: 1px solid var(--accent-red) !important;
        color: var(--accent-red) !important;
        border-radius: 8px !important;
    }

    .stInfo {
        background: rgba(0,212,255,0.15) !important;
        border: 1px solid var(--accent-electric) !important;
        color: var(--accent-electric) !important;
        border-radius: 8px !important;
    }

    .stWarning {
        background: rgba(251,191,36,0.15) !important;
        border: 1px solid var(--accent-gold) !important;
        color: var(--accent-gold) !important;
        border-radius: 8px !important;
    }

    /* ========== Tabs 标签页 ========== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        border-radius: 8px 8px 0 0 !important;
        border: 1px solid var(--border-subtle) !important;
        border-bottom: none !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--accent-electric) !important;
        border-color: var(--accent-electric) !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: var(--bg-primary) !important;
        color: var(--accent-electric) !important;
        border-color: var(--accent-electric) !important;
    }

    /* ========== 表格 ========== */
    .stDataFrame {
        background: var(--bg-card) !important;
    }

    .stDataFrame table {
        color: var(--text-primary) !important;
    }

    /* ========== 侧边栏样式 ========== */
    [data-testid="stSidebar"] {
        background: var(--bg-primary) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] label {
        color: var(--text-label) !important;
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