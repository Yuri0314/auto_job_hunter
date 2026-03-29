"""公共UI组件"""

import streamlit as st
from .styles import COLORS


def render_stat_card(label: str, value: str, color: str = None):
    """渲染统计卡片"""
    color = color or COLORS["accent_electric"]

    st.markdown(f"""
    <div style="
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    ">
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 1.5rem;
            font-weight: 700;
            color: {color};
        ">{value}</div>
        <div style="
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        ">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_indicator(label: str, is_ok: bool):
    """渲染状态指示器"""
    icon = "●" if is_ok else "○"
    color = COLORS["accent_green"] if is_ok else COLORS["text_muted"]
    text = label

    st.markdown(f"""
    <div style="
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    ">
        <span style="color: {color}; font-size: 0.85rem;">{icon}</span>
        <span style="color: var(--text-primary); font-size: 0.85rem;">{text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = None):
    """渲染区块标题"""
    subtitle_html = f'<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''

    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent-electric);
        ">{title}</div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_action_button(label: str, icon: str, key: str, primary: bool = False):
    """渲染操作按钮"""
    button_type = "primary" if primary else "secondary"
    return st.button(f"{icon} {label}", key=key, type=button_type, use_container_width=True)


def render_job_item(job: dict):
    """渲染职位条目"""
    status_colors = {
        "submitted": COLORS["accent_electric"],
        "read": COLORS["accent_gold"],
        "replied": COLORS["accent_green"],
        "interview": COLORS["accent_magenta"],
        "rejected": COLORS["accent_red"],
    }

    status = job.get("status", "submitted")
    status_color = status_colors.get(status, COLORS["text_muted"])
    status_text = {
        "submitted": "已投递",
        "read": "HR已读",
        "replied": "HR回复",
        "interview": "面试邀约",
        "rejected": "不合适",
    }.get(status, status)

    st.markdown(f"""
    <div style="
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <div style="font-weight: 600; color: var(--text-primary);">{job.get('title', '-')}</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">{job.get('company', '-')} · {job.get('city', '-')}</div>
        </div>
        <div style="font-family: 'JetBrains Mono'; font-size: 0.85rem; color: {status_color};">{status_text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_loading_screen(message: str = "加载中..."):
    """渲染全屏加载"""
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
            font-size: 2rem;
            color: var(--accent-electric);
            animation: pulse 1.5s ease-in-out infinite;
        ">⚡</div>
        <div style="
            font-family: 'JetBrains Mono';
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 1rem;
        ">{message}</div>
    </div>
    <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
        }}
    </style>
    """, unsafe_allow_html=True)