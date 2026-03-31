# frontend_nicegui/styles.py
"""样式配置 - Obsidian Terminal 暗黑科技风格"""

# 核心颜色配置
COLORS = {
    # 背景色
    "bg_primary": "#050508",
    "bg_secondary": "#16161d",
    "bg_card": "#1a1a24",
    "bg_hover": "rgba(255, 255, 255, 0.05)",

    # 强调色
    "accent_blue": "#00d4ff",
    "accent_gold": "#fbbf24",
    "accent_green": "#22c55e",
    "accent_red": "#ef4444",

    # 文本色
    "text_primary": "#f4f4f5",
    "text_secondary": "#c4c4c8",
    "text_muted": "#71717a",
    "text_disabled": "#52525b",

    # 边框色
    "border_default": "rgba(255, 255, 255, 0.12)",
    "border_focus": "#00d4ff",
}

# 字体配置
FONTS = {
    "mono": "JetBrains Mono, Consolas, monospace",
    "sans": "Inter, system-ui, sans-serif",
}

# 间距配置
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
}


def get_card_classes():
    """获取卡片样式类"""
    return (
        f"bg-[{COLORS['bg_card']}] "
        f"border border-[{COLORS['border_default']}] "
        "rounded-lg p-4"
    )


def get_button_classes(variant: str = "primary"):
    """获取按钮样式类"""
    base = "font-mono text-sm rounded px-4 py-2 transition-all "

    variants = {
        "primary": f"bg-[{COLORS['accent_blue']}] text-[#050508] hover:opacity-90",
        "secondary": f"bg-[{COLORS['bg_secondary']}] text-[{COLORS['text_secondary']}] "
                     f"border border-[{COLORS['border_default']}] hover:bg-[{COLORS['bg_hover']}]",
        "danger": f"bg-[{COLORS['accent_red']}] text-white hover:opacity-90",
        "ghost": f"bg-transparent text-[{COLORS['text_secondary']}] hover:bg-[{COLORS['bg_hover']}]",
    }

    return base + variants.get(variant, variants["primary"])


# 全局 CSS 样式 - Obsidian Terminal 暗黑科技风格
GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #050508;
        --bg-secondary: #16161d;
        --bg-card: #1a1a24;
        --accent-blue: #00d4ff;
        --accent-gold: #fbbf24;
        --text-primary: #f4f4f5;
        --text-secondary: #c4c4c8;
        --text-muted: #71717a;
        --border-default: rgba(255, 255, 255, 0.12);
    }

    /* 强制暗黑背景 - 覆盖 Quasar 默认 */
    html, body, .q-page, .q-layout, main, .q-drawer-container {
        background: var(--bg-primary) !important;
        background-color: var(--bg-primary) !important;
    }

    body {
        font-family: 'DM Sans', sans-serif;
        color: var(--text-primary) !important;
    }

    /* NiceGUI 侧边栏 */
    .q-drawer {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-default) !important;
    }

    .q-drawer .q-item {
        color: var(--text-secondary) !important;
    }

    .q-drawer .q-item:hover {
        background: rgba(255, 255, 255, 0.05) !important;
    }

    /* 卡片样式 */
    .q-card {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        color: var(--text-primary) !important;
    }

    /* 标签/文字 */
    .q-label, label, .q-item-label, .q-tab__label {
        color: var(--text-primary) !important;
    }

    /* Tab 样式 */
    .q-tabs {
        background: transparent !important;
    }

    .q-tab {
        color: var(--text-secondary) !important;
    }

    .q-tab--active .q-tab__label {
        color: var(--accent-blue) !important;
    }

    /* 输入框 */
    .q-field__label {
        color: var(--text-secondary) !important;
    }

    .q-input, .q-select, .q-field {
        color: var(--text-primary) !important;
    }

    .q-field__control {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
    }

    /* 按钮样式 */
    .action-btn {
        background: var(--bg-card) !important;
        border: 1px solid var(--accent-blue) !important;
        color: var(--accent-blue) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
    }

    .action-btn:hover {
        background: rgba(0, 212, 255, 0.15) !important;
    }

    .primary-btn {
        background: linear-gradient(135deg, #0891b2, #00d4ff) !important;
        color: var(--bg-primary) !important;
        border: none !important;
    }

    /* 隐藏 Quasar 默认头部 */
    .q-header {
        display: none !important;
    }

    /* Badge 样式 */
    .q-badge {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Alert/通知 */
    .q-notification {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
    }
</style>
"""


def apply_styles():
    """应用全局样式"""
    from nicegui import ui
    ui.add_head_html(GLOBAL_CSS)
    ui.dark = True
