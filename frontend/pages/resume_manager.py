"""
简历管理前端组件 - 简化版

移除了复杂的loading状态管理，使用同步渲染
状态变量使用命名空间 resume.xxx，便于统一清理
"""

import os
import streamlit as st
import requests
from datetime import datetime

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


# ========== 状态变量命名规范 ==========
# 本页面所有session_state变量使用 resume.xxx 命名空间
# - resume.active_tab: 当前tab索引 (0=列表, 1=上传, 2=粘贴)
# - resume.list_cache: 简历列表缓存
# - resume.selected_ids: 选中的简历ID列表
# - resume.highlight_id: 需要高亮的简历ID
# - resume.view_id: 查看详情的简历ID
# - resume.edit_id: 编辑详情的简历ID
# - resume.confirm_delete_id: 待删除确认的简历ID
# - resume.show_batch_delete: 批量删除确认弹窗状态
# - resume.msg: 消息提示 (type, text)


# ========== API Functions ==========

def fetch_resume_list():
    """获取简历列表"""
    try:
        r = requests.get(f"{API_BASE}/resume/list", timeout=10)
        if r.ok:
            return r.json()
        return {"items": [], "total": 0}
    except Exception as e:
        return {"items": [], "total": 0}


def get_resume_detail(resume_id):
    """获取简历详情"""
    try:
        r = requests.get(f"{API_BASE}/resume/{resume_id}", timeout=10)
        if r.ok:
            return r.json()
        return None
    except:
        return None


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


def batch_delete_resumes(ids):
    """批量删除简历"""
    try:
        r = requests.post(
            f"{API_BASE}/resume/batch-delete",
            json={"ids": ids},
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


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


# ========== Helper Functions ==========

def _get_state(key: str, default=None):
    """获取命名空间状态"""
    return st.session_state.get(f"resume.{key}", default)


def _set_state(key: str, value):
    """设置命名空间状态"""
    st.session_state[f"resume.{key}"] = value


def _del_state(key: str):
    """删除命名空间状态"""
    full_key = f"resume.{key}"
    if full_key in st.session_state:
        del st.session_state[full_key]


def _clear_list_cache():
    """清除列表缓存"""
    _del_state("list_cache")


# ========== Main Render Function ==========

def render_resume_manager():
    """主渲染函数 - 简化版，无复杂状态管理"""

    # 页面标题
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 700; color: #00d4ff;">
            RESUME_MANAGER
        </div>
        <div style="font-size: 0.8rem; color: #71717a; margin-top: 0.25rem;">
            简历管理 · 多简历支持 · 智能解析
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 处理消息提示
    msg = _get_state("msg")
    if msg:
        msg_type, msg_text = msg
        if msg_type == "success":
            st.success(msg_text)
        else:
            st.error(msg_text)
        _del_state("msg")

    # 自定义Tab切换（支持程序化切换）
    if _get_state("active_tab") is None:
        _set_state("active_tab", 0)

    tab_labels = ["简历列表", "上传简历", "粘贴文本"]
    tab_cols = st.columns(3)
    for i, (col, label) in enumerate(zip(tab_cols, tab_labels)):
        with col:
            is_active = _get_state("active_tab") == i
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"tab_{i}", type=btn_type, use_container_width=True):
                _set_state("active_tab", i)
                st.rerun()

    st.divider()

    # 根据选中tab渲染内容
    if _get_state("active_tab") == 0:
        _render_resume_list()
    elif _get_state("active_tab") == 1:
        _render_upload_section()
    else:
        _render_paste_section()


def _render_resume_list():
    """渲染简历列表"""

    # 获取简历列表（带缓存）
    if _get_state("list_cache") is None:
        _set_state("list_cache", fetch_resume_list())

    data = _get_state("list_cache")
    resumes = data.get("items", [])

    if not resumes:
        st.info("暂无简历，请上传或粘贴简历内容")
        return

    # 初始化选中状态（使用list，Streamlit不支持set序列化）
    if _get_state("selected_ids") is None:
        _set_state("selected_ids", [])

    # 工具栏
    col_t1, col_t2, col_t3, col_t4 = st.columns([1, 1, 1, 2])

    with col_t1:
        all_ids = [r.get("id") for r in resumes]
        if st.button("全选", key="select_all", use_container_width=True):
            _set_state("selected_ids", all_ids)
            st.rerun()

    with col_t2:
        if st.button("取消全选", key="clear_selection", use_container_width=True):
            _set_state("selected_ids", [])
            st.rerun()

    with col_t3:
        selected_ids = _get_state("selected_ids", [])
        if len(selected_ids) > 0:
            if st.button(f"批量删除 ({len(selected_ids)})", key="batch_delete_btn", use_container_width=True):
                _set_state("show_batch_delete", True)
                st.rerun()

    with col_t4:
        if st.button("刷新列表", key="refresh_list", use_container_width=True):
            _clear_list_cache()
            st.rerun()

    # 批量删除确认弹窗
    if _get_state("show_batch_delete"):
        selected_ids = _get_state("selected_ids", [])
        st.warning(f"确认删除 {len(selected_ids)} 条简历？此操作不可撤销。")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("确认删除", key="confirm_batch_delete", type="primary"):
                result = batch_delete_resumes(selected_ids)
                if result.get("success"):
                    deleted = result.get("deleted", 0)
                    _set_state("msg", ("success", f"已删除 {deleted} 条简历"))
                    _set_state("selected_ids", [])
                    _clear_list_cache()
                else:
                    _set_state("msg", ("error", result.get("error", "删除失败")))
                _del_state("show_batch_delete")
                st.rerun()
        with c2:
            if st.button("取消", key="cancel_batch_delete"):
                _del_state("show_batch_delete")
                st.rerun()

    # 显示简历卡片
    for resume in resumes:
        _render_resume_card(resume)

    # 处理模态框
    if _get_state("view_id"):
        _render_detail_modal(_get_state("view_id"), readonly=True)

    if _get_state("edit_id"):
        _render_detail_modal(_get_state("edit_id"), readonly=False)


def _render_resume_card(resume):
    """渲染简历卡片"""
    resume_id = resume.get("id")
    is_primary = resume.get("is_primary", False)
    profile = resume.get("profile") or {}

    # 检查是否需要高亮（新解析的简历）
    highlight_id = _get_state("highlight_id")
    is_highlighted = highlight_id == resume_id
    if is_highlighted:
        # 清除高亮状态（只高亮一次）
        _del_state("highlight_id")
        # 显示高亮边框
        st.markdown("""
        <div style="border: 2px solid #00d4ff; border-radius: 8px; padding: 8px; margin-bottom: 8px; background: rgba(0, 212, 255, 0.1);">
            <span style="color: #00d4ff; font-size: 0.8rem;">✨ 新解析的简历</span>
        </div>
        """, unsafe_allow_html=True)

    # 复选框列
    check_col, content_col = st.columns([1, 4])

    with check_col:
        selected_ids = _get_state("selected_ids", [])
        is_selected = resume_id in selected_ids
        new_state = st.checkbox("", value=is_selected, key=f"check_{resume_id}", label_visibility="collapsed")
        if new_state != is_selected:
            if new_state:
                _set_state("selected_ids", selected_ids + [resume_id])
            else:
                _set_state("selected_ids", [x for x in selected_ids if x != resume_id])
            st.rerun()

    with content_col:
        # 卡片容器
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                # 基本信息
                name = resume.get("name", "未命名简历")
                file_type = resume.get("file_type", "-").upper()
                created = resume.get("created_at", "")[:10] if resume.get("created_at") else "-"

                primary_badge = " ⭐主简历" if is_primary else ""
                st.markdown(f"**{name}**{primary_badge}")
                st.caption(f"{file_type} · {created}")

                # 画像信息
                if profile:
                    position = profile.get("current_position", "-") or "-"
                    exp = profile.get("experience_years", "-") or "-"
                    st.caption(f"{position} · {exp}年经验")

            with col2:
                st.caption("")  # spacer

            # 操作按钮
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

            with btn_col1:
                if st.button("查看", key=f"view_{resume_id}", use_container_width=True):
                    _set_state("view_id", resume_id)
                    st.rerun()

            with btn_col2:
                if st.button("编辑", key=f"edit_{resume_id}", use_container_width=True):
                    _set_state("edit_id", resume_id)
                    st.rerun()

            with btn_col3:
                if not is_primary:
                    if st.button("设为主简历", key=f"primary_{resume_id}", use_container_width=True):
                        result = set_primary_resume(resume_id)
                        if result.get("success"):
                            _set_state("msg", ("success", "设置成功"))
                            _clear_list_cache()
                        else:
                            _set_state("msg", ("error", result.get("error", "设置失败")))
                        st.rerun()

            with btn_col4:
                if st.button("删除", key=f"del_{resume_id}", use_container_width=True):
                    _set_state("confirm_delete_id", resume_id)
                    st.rerun()

            # 删除确认
            if _get_state("confirm_delete_id") == resume_id:
                st.warning(f"确认删除 '{resume.get('name')}'？")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("确认", key=f"confirm_{resume_id}"):
                        result = delete_resume(resume_id)
                        if result.get("success"):
                            _set_state("msg", ("success", "删除成功"))
                            _clear_list_cache()
                        else:
                            _set_state("msg", ("error", result.get("error", "删除失败")))
                        _del_state("confirm_delete_id")
                        st.rerun()
                with c2:
                    if st.button("取消", key=f"cancel_{resume_id}"):
                        _del_state("confirm_delete_id")
                        st.rerun()

            st.divider()


def _render_upload_section():
    """渲染上传区域"""
    st.markdown("**上传简历文件**")
    st.caption("支持 PDF、Word、Markdown、TXT 格式")

    uploaded_file = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "doc", "md", "txt"],
        key="upload_file"
    )

    use_ai = st.checkbox("使用AI模式解析（更准确）", value=False, key="upload_ai")

    if uploaded_file:
        if st.button("解析简历", type="primary", key="parse_upload"):
            with st.spinner("解析中..."):
                result = upload_resume(uploaded_file, use_ai)
                if result.get("success"):
                    resume_id = result.get("resume_id")
                    _set_state("msg", ("success", "简历解析成功！"))
                    _set_state("active_tab", 0)  # 跳转到简历列表
                    _set_state("highlight_id", resume_id)  # 高亮新简历
                    _clear_list_cache()
                    st.rerun()
                else:
                    st.error(f"解析失败: {result.get('error', '未知错误')}")


def _render_paste_section():
    """渲染粘贴区域"""
    st.markdown("**粘贴简历内容**")

    text_content = st.text_area(
        "简历内容",
        placeholder="粘贴您的简历内容...",
        height=300,
        key="paste_text"
    )

    use_ai = st.checkbox("使用AI模式解析（更准确）", value=False, key="paste_ai")

    if st.button("解析文本", type="primary", key="parse_paste"):
        if len(text_content) < 50:
            st.warning("内容太少，请提供完整简历")
        else:
            with st.spinner("解析中..."):
                result = parse_text_resume(text_content, use_ai)
                if result.get("success"):
                    resume_id = result.get("resume_id")
                    _set_state("msg", ("success", "简历解析成功！"))
                    _set_state("active_tab", 0)  # 跳转到简历列表
                    _set_state("highlight_id", resume_id)  # 高亮新简历
                    _clear_list_cache()
                    st.rerun()
                else:
                    st.error(f"解析失败: {result.get('error', '未知错误')}")


def _render_detail_modal(resume_id: int, readonly: bool = False):
    """渲染详情模态框"""

    detail = get_resume_detail(resume_id)
    if not detail:
        st.error("加载失败")
        if st.button("关闭", key=f"close_err_{resume_id}"):
            _del_state("view_id")
            _del_state("edit_id")
            st.rerun()
        return

    profile = detail.get("profile") or {}

    st.markdown("---")
    st.markdown(f"**{'查看' if readonly else '编辑'}简历详情**")

    # 基本信息
    col1, col2 = st.columns(2)

    with col1:
        if readonly:
            st.text_input("姓名", value=profile.get("name") or "", disabled=True)
            st.text_input("电话", value=profile.get("phone") or "", disabled=True)
        else:
            name_val = st.text_input("姓名", value=profile.get("name") or "", key=f"inp_name_{resume_id}")
            phone_val = st.text_input("电话", value=profile.get("phone") or "", key=f"inp_phone_{resume_id}")

    with col2:
        if readonly:
            st.text_input("邮箱", value=profile.get("email") or "", disabled=True)
        else:
            email_val = st.text_input("邮箱", value=profile.get("email") or "", key=f"inp_email_{resume_id}")

    # 操作按钮
    c1, c2 = st.columns(2)
    with c1:
        if not readonly:
            if st.button("保存", type="primary", key=f"save_detail_{resume_id}"):
                profile_data = {
                    "name": st.session_state.get(f"inp_name_{resume_id}", ""),
                    "phone": st.session_state.get(f"inp_phone_{resume_id}", ""),
                    "email": st.session_state.get(f"inp_email_{resume_id}", ""),
                }
                result = update_resume_profile(resume_id, profile_data)
                if result.get("success"):
                    st.success("保存成功")
                    _del_state("edit_id")
                    _clear_list_cache()
                    st.rerun()
                else:
                    st.error(f"保存失败: {result.get('error')}")

    with c2:
        if st.button("关闭", key=f"close_detail_{resume_id}"):
            _del_state("view_id")
            _del_state("edit_id")
            st.rerun()