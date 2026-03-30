"""
设置页面 - AI配置、平台登录、系统设置
"""

import os
import streamlit as st
import requests

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


# ========== API Functions ==========

def fetch_platform_status():
    """获取平台登录状态"""
    try:
        r = requests.get(f"{API_BASE}/system/platforms", timeout=10)
        if r.ok:
            return r.json()
        return []
    except:
        return []


def start_platform_login(platform):
    """启动平台登录"""
    try:
        r = requests.post(f"{API_BASE}/system/login/{platform}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def logout_platform(platform):
    """退出平台登录"""
    try:
        r = requests.post(f"{API_BASE}/system/logout/{platform}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_config_items(category=None):
    """获取配置项"""
    try:
        params = {"category": category} if category else {}
        r = requests.get(f"{API_BASE}/settings/items", params=params, timeout=10)
        if r.ok:
            return r.json()
        return {}
    except:
        return {}


def update_config_item(key, value):
    """更新配置项"""
    try:
        r = requests.put(
            f"{API_BASE}/settings/items/{key}",
            json={"value": value},
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def reset_config_item(key):
    """重置配置项"""
    try:
        r = requests.post(f"{API_BASE}/settings/reset/{key}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ========== Main Render Function ==========

def render_settings_page():
    """渲染设置页面"""

    # 页面标题
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 700; color: #00d4ff;">
            SETTINGS
        </div>
        <div style="font-size: 0.8rem; color: #71717a; margin-top: 0.25rem;">
            系统配置 · AI模型 · 平台登录
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 处理消息提示
    if "_settings_msg" in st.session_state:
        msg_type, msg_text = st.session_state._settings_msg
        if msg_type == "success":
            st.success(msg_text)
        else:
            st.error(msg_text)
        del st.session_state._settings_msg

    # Tabs 布局
    tab1, tab2, tab3 = st.tabs(["平台登录", "AI配置", "系统设置"])

    with tab1:
        _render_platform_login()

    with tab2:
        _render_ai_config()

    with tab3:
        _render_system_config()


def _render_platform_login():
    """渲染平台登录状态"""

    # 刷新按钮
    if st.button("🔄 刷新状态", key="refresh_platform"):
        if "_platform_cache" in st.session_state:
            del st.session_state._platform_cache

    # 获取平台状态（带缓存）
    if "_platform_cache" not in st.session_state:
        st.session_state._platform_cache = fetch_platform_status()

    platforms = st.session_state._platform_cache

    # 平台名称映射
    platform_names = {
        "boss": "BOSS直聘",
        "liepin": "猎聘",
        "maimai": "脉脉",
    }

    st.markdown("""
    **平台登录状态**

    点击"登录"按钮后，系统会打开浏览器窗口，请在浏览器中手动输入手机号和验证码完成登录。登录成功后Cookie会自动保存。
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    for platform in platforms:
        platform_id = platform.get("platform")
        platform_name = platform_names.get(platform_id, platform_id)
        cookie_saved = platform.get("cookie_saved", False)

        # 状态指示
        status_icon = "✅" if cookie_saved else "❌"
        status_text = "已登录 (Cookie已保存)" if cookie_saved else "未登录"

        # 卡片样式
        st.markdown(f"""
        <div style="
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 600; color: var(--text-primary);">{platform_name}</span>
                    <span style="margin-left: 0.5rem; font-size: 0.8rem; color: {('#4ade80' if cookie_saved else '#f87171')};">
                        {status_icon} {status_text}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 操作按钮
        col1, col2 = st.columns(2)

        with col1:
            if st.button("登录", key=f"login_{platform_id}", use_container_width=True):
                result = start_platform_login(platform_id)
                if result.get("status") == "started":
                    st.session_state._settings_msg = ("success", f"登录已启动，请在打开的浏览器中完成登录")
                elif result.get("status") == "already_running":
                    st.session_state._settings_msg = ("success", "登录任务正在进行中")
                else:
                    st.session_state._settings_msg = ("error", result.get("error", "启动登录失败"))
                st.rerun()

        with col2:
            if cookie_saved:
                if st.button("退出登录", key=f"logout_{platform_id}", use_container_width=True):
                    result = logout_platform(platform_id)
                    if "error" not in result:
                        st.session_state._settings_msg = ("success", f"{platform_name} Cookie已清除")
                        if "_platform_cache" in st.session_state:
                            del st.session_state._platform_cache
                    else:
                        st.session_state._settings_msg = ("error", result.get("error", "退出失败"))
                    st.rerun()


def _render_ai_config():
    """渲染AI配置"""

    st.markdown("""
    **AI模型配置**

    配置OpenAI或Ollama用于智能匹配和生成打招呼语。敏感配置保存后会加密存储。
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    # 获取AI配置项
    if "_ai_config_cache" not in st.session_state:
        st.session_state._ai_config_cache = fetch_config_items("ai")

    ai_items = st.session_state._ai_config_cache

    if not ai_items:
        st.warning("加载配置失败")
        return

    # OpenAI配置
    st.markdown("**OpenAI**")

    openai_key = ai_items.get("openai_api_key", {})
    key_value = openai_key.get("value", "") or ""

    col1, col2 = st.columns([3, 1])
    with col1:
        new_key = st.text_input(
            "OpenAI API Key",
            value=key_value,
            type="password",
            key="inp_openai_key",
            help=openai_key.get("description", ""),
        )
    with col2:
        st.caption("")  # spacer

    openai_model = ai_items.get("openai_model", {})
    model_options = openai_model.get("options", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
    current_model = openai_model.get("value", "gpt-4") or "gpt-4"

    new_model = st.selectbox(
        "OpenAI模型",
        options=model_options,
        index=model_options.index(current_model) if current_model in model_options else 0,
        key="inp_openai_model",
        help=openai_model.get("description", ""),
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Ollama配置
    st.markdown("**Ollama (本地模型)**")

    ollama_url = ai_items.get("ollama_base_url", {})
    url_value = ollama_url.get("value", "") or ""

    new_url = st.text_input(
        "Ollama服务地址",
        value=url_value,
        key="inp_ollama_url",
        help=ollama_url.get("description", "例如: http://localhost:11434"),
    )

    ollama_model = ai_items.get("ollama_model", {})
    model_value = ollama_model.get("value", "") or ""

    new_ollama_model = st.text_input(
        "Ollama模型名称",
        value=model_value,
        key="inp_ollama_model",
        help=ollama_model.get("description", "例如: llama3, qwen2"),
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 保存按钮
    if st.button("保存AI配置", type="primary", key="save_ai_config"):
        errors = []
        success_count = 0

        # 保存OpenAI Key（如果有变化）
        if new_key and new_key != key_value:
            result = update_config_item("openai_api_key", new_key)
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"OpenAI Key: {result.get('error')}")

        # 保存模型
        if new_model != current_model:
            result = update_config_item("openai_model", new_model)
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"模型: {result.get('error')}")

        # 保存Ollama URL
        if new_url != url_value:
            result = update_config_item("ollama_base_url", new_url)
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"Ollama URL: {result.get('error')}")

        # 保存Ollama模型
        if new_ollama_model != model_value:
            result = update_config_item("ollama_model", new_ollama_model)
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"Ollama模型: {result.get('error')}")

        if errors:
            st.session_state._settings_msg = ("error", f"部分配置保存失败: {', '.join(errors)}")
        elif success_count > 0:
            st.session_state._settings_msg = ("success", f"已保存 {success_count} 个配置项")
            if "_ai_config_cache" in st.session_state:
                del st.session_state._ai_config_cache
        else:
            st.session_state._settings_msg = ("success", "配置无变化")
        st.rerun()


def _render_system_config():
    """渲染系统配置"""

    st.markdown("""
    **基础系统配置**

    调整应用运行参数。
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    # 获取基础配置项
    if "_basic_config_cache" not in st.session_state:
        st.session_state._basic_config_cache = fetch_config_items("basic")

    basic_items = st.session_state._basic_config_cache

    if not basic_items:
        st.warning("加载配置失败")
        return

    # 调试模式
    debug_item = basic_items.get("debug", {})
    debug_value = debug_item.get("value", "false") or "false"
    debug_enabled = debug_value.lower() == "true"

    new_debug = st.checkbox(
        "启用调试模式",
        value=debug_enabled,
        key="inp_debug",
        help=debug_item.get("description", ""),
    )

    # 日志级别
    log_item = basic_items.get("log_level", {})
    log_options = log_item.get("options", ["DEBUG", "INFO", "WARNING", "ERROR"])
    current_log = log_item.get("value", "INFO") or "INFO"

    new_log = st.selectbox(
        "日志级别",
        options=log_options,
        index=log_options.index(current_log) if current_log in log_options else 1,
        key="inp_log_level",
        help=log_item.get("description", ""),
    )

    # 调度器
    scheduler_item = basic_items.get("scheduler_enabled", {})
    scheduler_value = scheduler_item.get("value", "false") or "false"
    scheduler_enabled = scheduler_value.lower() == "true"

    new_scheduler = st.checkbox(
        "启用定时调度",
        value=scheduler_enabled,
        key="inp_scheduler",
        help=scheduler_item.get("description", "自动定时搜索投递"),
    )

    # 最大并发数
    concurrent_item = basic_items.get("max_concurrent_jobs", {})
    concurrent_value = int(concurrent_item.get("value", "5") or "5")

    new_concurrent = st.slider(
        "最大并发数",
        min_value=1,
        max_value=20,
        value=concurrent_value,
        key="inp_concurrent",
        help=concurrent_item.get("description", ""),
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 保存按钮
    if st.button("保存系统配置", type="primary", key="save_basic_config"):
        errors = []
        success_count = 0

        # 保存调试模式
        debug_str = "true" if new_debug else "false"
        if debug_str != debug_value.lower():
            result = update_config_item("debug", debug_str)
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"调试模式: {result.get('error')}")

        # 保存日志级别
        if new_log != current_log:
            result = update_config_item("log_level", new_log)
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"日志级别: {result.get('error')}")

        # 保存调度器
        scheduler_str = "true" if new_scheduler else "false"
        if scheduler_str != scheduler_value.lower():
            result = update_config_item("scheduler_enabled", scheduler_str)
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"调度器: {result.get('error')}")

        # 保存并发数
        if new_concurrent != concurrent_value:
            result = update_config_item("max_concurrent_jobs", str(new_concurrent))
            if "error" not in result:
                success_count += 1
            else:
                errors.append(f"并发数: {result.get('error')}")

        if errors:
            st.session_state._settings_msg = ("error", f"部分配置保存失败: {', '.join(errors)}")
        elif success_count > 0:
            st.session_state._settings_msg = ("success", f"已保存 {success_count} 个配置项")
            if "_basic_config_cache" in st.session_state:
                del st.session_state._basic_config_cache
        else:
            st.session_state._settings_msg = ("success", "配置无变化")
        st.rerun()