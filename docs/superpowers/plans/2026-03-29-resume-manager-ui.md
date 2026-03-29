# 多简历管理实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现完整的多简历管理功能，包括简历列表、上传、编辑、删除、设置主简历

**Architecture:** 前端简历管理页面 + 后端API整合

**Tech Stack:** Streamlit, FastAPI, SQLAlchemy

**依赖:** 计划1 (数据模型) + 计划2 (简历解析)

---

## Files Structure

```
frontend/
├── app.py                   # 修改: 添加简历管理页面
└── pages/
    └── resume_manager.py    # 新增: 简历管理组件

backend/api/
└── resume.py                # 已在计划1中更新
```

---

## Task 1: 简历管理组件

**Files:**
- Create: `frontend/pages/resume_manager.py`

- [ ] **Step 1: 创建简历管理组件**

创建 `frontend/pages/resume_manager.py`：

```python
"""简历管理组件"""

import streamlit as st
import requests
from typing import Optional, List, Dict, Any
import os

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


def render_resume_manager():
    """渲染简历管理页面"""

    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 600; color: var(--accent-electric);">
            📄 简历管理
        </div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">
            多简历管理 · 版本切换 · 解析编辑
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 操作选择
    tab1, tab2, tab3 = st.tabs(["简历列表", "上传简历", "粘贴文本"])

    with tab1:
        render_resume_list()

    with tab2:
        render_upload_section()

    with tab3:
        render_paste_section()


def render_resume_list():
    """渲染简历列表"""

    # 获取简历列表
    resumes = fetch_resume_list()

    if not resumes:
        st.info("暂无简历，请上传或粘贴简历内容")
        return

    st.markdown(f"**共 {len(resumes)} 份简历**")

    for resume in resumes:
        render_resume_card(resume)


def render_resume_card(resume: Dict[str, Any]):
    """渲染单个简历卡片"""

    profile = resume.get("profile") or {}
    is_primary = resume.get("is_primary", False)

    # 卡片样式
    border_color = "var(--accent-green)" if is_primary else "var(--border-subtle)"
    primary_badge = '<span style="background: var(--accent-green); color: var(--bg-deep); padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.7rem; margin-left: 0.5rem;">主简历</span>' if is_primary else ""

    st.markdown(f"""
    <div style="
        background: var(--bg-card);
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-family: 'JetBrains Mono'; font-weight: 600; color: var(--text-primary);">
                    {resume.get('name', '未命名')}
                </span>
                {primary_badge}
                <div style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">
                    {profile.get('current_position', '-') if profile else '-'} · {profile.get('experience_years', '-') if profile else '-'}年经验
                </div>
            </div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.75rem; color: var(--text-muted);">
                {resume.get('file_type', 'unknown').upper()}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 操作按钮
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("查看详情", key=f"view_{resume['id']}"):
            st.session_state._view_resume_id = resume["id"]
            st.rerun()

    with col2:
        if not is_primary and st.button("设为主简历", key=f"primary_{resume['id']}"):
            set_primary_resume(resume["id"])

    with col3:
        if st.button("编辑", key=f"edit_{resume['id']}"):
            st.session_state._edit_resume_id = resume["id"]
            st.rerun()

    with col4:
        if st.button("删除", key=f"delete_{resume['id']}"):
            delete_resume(resume["id"])


def render_upload_section():
    """渲染上传区域"""

    st.markdown("**上传简历文件**")

    uploaded = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "md", "txt"],
        help="支持 PDF、Word(.docx)、Markdown(.md)、纯文本(.txt)"
    )

    use_ai = st.checkbox("使用 AI 模式解析（更准确）", value=False)

    if uploaded and st.button("解析简历", type="primary"):
        result = upload_resume(uploaded, use_ai)

        if result.get("success"):
            st.success(f"解析成功！简历ID: {result.get('resume_id')}")
            st.rerun()
        else:
            st.error(result.get("error", "解析失败"))


def render_paste_section():
    """渲染粘贴区域"""

    st.markdown("**粘贴简历内容**")

    text = st.text_area(
        "简历内容",
        height=300,
        placeholder="直接粘贴简历文本内容..."
    )

    use_ai = st.checkbox("使用 AI 模式解析（更准确）", value=False, key="paste_ai")

    if text and st.button("解析文本", type="primary"):
        result = parse_text_resume(text, use_ai)

        if result.get("success"):
            st.success(f"解析成功！简历ID: {result.get('resume_id')}")
            st.rerun()
        else:
            st.error(result.get("error", "解析失败"))


# ========== API 调用 ==========

def fetch_resume_list() -> List[Dict[str, Any]]:
    """获取简历列表"""
    try:
        r = requests.get(f"{API_BASE}/resume/list", timeout=10)
        if r.ok:
            return r.json().get("items", [])
    except Exception as e:
        st.error(f"获取简历列表失败: {e}")
    return []


def upload_resume(file, use_ai: bool) -> Dict[str, Any]:
    """上传简历"""
    try:
        files = {"file": (file.name, file)}
        data = {"use_ai": str(use_ai).lower()}
        r = requests.post(f"{API_BASE}/resume/upload", files=files, data=data, timeout=60)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def parse_text_resume(text: str, use_ai: bool) -> Dict[str, Any]:
    """解析粘贴的文本"""
    try:
        r = requests.post(f"{API_BASE}/resume/parse-text", json={
            "text": text,
            "use_ai": use_ai,
        }, timeout=60)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_primary_resume(resume_id: int):
    """设置主简历"""
    try:
        r = requests.post(f"{API_BASE}/resume/{resume_id}/set-primary", timeout=10)
        if r.ok:
            st.success("已设为主简历")
            st.rerun()
        else:
            st.error("设置失败")
    except Exception as e:
        st.error(f"设置失败: {e}")


def delete_resume(resume_id: int):
    """删除简历"""
    try:
        r = requests.delete(f"{API_BASE}/resume/{resume_id}", timeout=10)
        if r.ok:
            st.success("简历已删除")
            st.rerun()
        else:
            st.error("删除失败")
    except Exception as e:
        st.error(f"删除失败: {e}")
```

- [ ] **Step 2: Commit**

```bash
git add frontend/pages/resume_manager.py
git commit -m "feat: 添加简历管理前端组件"
```

---

## Task 2: 集成到主应用

**Files:**
- Modify: `frontend/app.py`

- [ ] **Step 1: 在主应用中集成简历管理页面**

在 `frontend/app.py` 中添加简历管理页面的入口。

在底部导航或快速操作区域添加简历管理按钮：

```python
# 在快速操作区域添加
if st.button("📄 管理简历", use_container_width=True):
    st.session_state.step = 6  # 简历管理页面
    st.rerun()
```

添加简历管理页面的渲染：

```python
elif step == 6:
    from frontend.pages.resume_manager import render_resume_manager
    render_resume_manager()
```

- [ ] **Step 2: 测试集成**

启动前端验证简历管理功能：

```bash
cd /d E:\Code\auto_job_hunter && streamlit run frontend/app.py
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app.py
git commit -m "feat: 集成简历管理页面到主应用"
```

---

## Task 3: 简历编辑模态框

**Files:**
- Modify: `frontend/pages/resume_manager.py`

- [ ] **Step 1: 添加简历编辑功能**

在 `frontend/pages/resume_manager.py` 中添加编辑模态框：

```python
def render_edit_modal(resume_id: int):
    """渲染编辑模态框"""

    # 获取简历详情
    detail = fetch_resume_detail(resume_id)
    if not detail:
        st.error("获取简历详情失败")
        return

    profile = detail.get("profile", {})

    st.markdown("### 编辑简历信息")

    with st.form("edit_profile"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("姓名", value=profile.get("name", ""))
            phone = st.text_input("手机号", value=profile.get("phone", ""))
            email = st.text_input("邮箱", value=profile.get("email", ""))
            experience_years = st.number_input("工作年限", value=profile.get("experience_years") or 0, min_value=0, max_value=50)

        with col2:
            education = st.text_input("学历", value=profile.get("education", ""))
            school = st.text_input("学校", value=profile.get("school", ""))
            current_position = st.text_input("当前职位", value=profile.get("current_position", ""))

        # 目标职位和城市
        target_positions = st.text_input(
            "目标职位（逗号分隔）",
            value=",".join(profile.get("target_positions", []))
        )
        preferred_cities = st.text_input(
            "意向城市（逗号分隔）",
            value=",".join(profile.get("preferred_cities", []))
        )

        # 技能
        skills = st.text_input(
            "技能（逗号分隔）",
            value=",".join(profile.get("skills", []))
        )

        # 薪资
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            salary_min = st.number_input("期望薪资下限(K)", value=profile.get("salary_min") or 0, min_value=0)
        with col_s2:
            salary_max = st.number_input("期望薪资上限(K)", value=profile.get("salary_max") or 0, min_value=0)

        submitted = st.form_submit_button("保存修改")

        if submitted:
            update_data = {
                "name": name or None,
                "phone": phone or None,
                "email": email or None,
                "experience_years": experience_years or None,
                "education": education or None,
                "school": school or None,
                "current_position": current_position or None,
                "target_positions": [p.strip() for p in target_positions.split(",") if p.strip()],
                "preferred_cities": [c.strip() for c in preferred_cities.split(",") if c.strip()],
                "skills": [s.strip() for s in skills.split(",") if s.strip()],
                "salary_min": salary_min or None,
                "salary_max": salary_max or None,
            }

            success = update_resume_profile(resume_id, update_data)
            if success:
                st.success("保存成功")
                st.session_state._edit_resume_id = None
                st.rerun()
            else:
                st.error("保存失败")


def fetch_resume_detail(resume_id: int) -> Optional[Dict[str, Any]]:
    """获取简历详情"""
    try:
        r = requests.get(f"{API_BASE}/resume/{resume_id}", timeout=10)
        if r.ok:
            return r.json()
    except:
        pass
    return None


def update_resume_profile(resume_id: int, data: Dict[str, Any]) -> bool:
    """更新简历画像"""
    try:
        r = requests.put(f"{API_BASE}/resume/{resume_id}/profile", json=data, timeout=10)
        return r.ok
    except:
        return False
```

- [ ] **Step 2: 在简历列表中调用编辑模态框**

修改 `render_resume_list` 函数，在末尾添加：

```python
    # 显示编辑模态框
    if st.session_state.get("_edit_resume_id"):
        render_edit_modal(st.session_state._edit_resume_id)

    # 显示详情模态框
    if st.session_state.get("_view_resume_id"):
        render_detail_modal(st.session_state._view_resume_id)
```

- [ ] **Step 3: Commit**

```bash
git add frontend/pages/resume_manager.py
git commit -m "feat: 添加简历编辑和详情查看功能"
```

---

## Verification

- [ ] **启动后端服务**

```bash
cd /d E:\Code\auto_job_hunter && python run.py web
```

- [ ] **启动前端服务**

```bash
streamlit run frontend/app.py
```

- [ ] **验证功能**
- 上传 PDF/Word/MD/TXT 文件
- 粘贴简历文本
- 查看简历列表
- 编辑简历信息
- 设置主简历
- 删除简历

---

## Summary

完成本计划后：

1. **简历管理页面**: 列表、上传、粘贴三种操作入口
2. **多格式支持**: PDF、Word、Markdown、纯文本
3. **编辑功能**: 可编辑简历的各项信息
4. **主简历设置**: 可设置默认使用的简历
5. **删除功能**: 可删除不需要的简历

用户可以管理多份简历，在求职时选择使用哪一份。