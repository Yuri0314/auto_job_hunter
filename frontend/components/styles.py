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