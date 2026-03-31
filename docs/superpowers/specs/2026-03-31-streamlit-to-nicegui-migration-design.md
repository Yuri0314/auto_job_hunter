# Streamlit → NiceGUI 迁移设计规格

## 背景

当前前端使用 Streamlit，存在严重问题：
- 按钮**点击无响应**，刷新后仍无效
- UI 在 API 调用时**冻结阻塞**
- 状态管理脆弱，rerun 时易出错
- 单线程模型，无法处理复杂交互

这是 Streamlit 的已知缺陷（[GitHub #8725](https://github.com/streamlit/streamlit/issues/8725)），无法通过代码修复解决。

## 目标

- 彻底解决 UI 响应问题
- 保持现有 Obsidian Terminal 暗黑风格
- 合并前后端为单服务，简化部署
- 保持所有现有功能

## 方案：渐进迁移

分阶段迁移，每阶段可独立验证：

| 阶段 | 内容 | 估计工作量 |
|------|------|------------|
| 1 | NiceGUI 入口 + 基础布局 | 中 |
| 2 | Dashboard 页面 | 低 |
| 3 | Resume Manager 页面 | 中 |
| 4 | Search 页面 | 低 |
| 5 | Applications + Messages 页面 | 中 |
| 6 | Settings 页面 | 中 |
| 7 | 清理 Streamlit 依赖 | 低 |

## 技术架构

### 当前架构

```
Streamlit (port 8501) ← HTTP → FastAPI Backend (port 8000)
                          ↑
                      requests 库调用 API
```

### 目标架构

```
NiceGUI + FastAPI 合并为单服务 (port 8000)
    ├── NiceGUI 页面路由 (/ui/*)
    ├── API 路由 (/api/*) - 保留给外部调用
    └── 页面直接调用后端 service 函数，无需 HTTP
```

### 关键优势

1. **UI 不阻塞**：NiceGUI 基于 Quasar/Vue，异步事件驱动
2. **状态管理清晰**：基于 `app.storage.user` 和响应式绑定
3. **合并部署**：单端口、单进程，简化运维
4. **保留 API**：外部脚本仍可通过 `/api/*` 调用

## 目录结构

迁移后目录：

```
frontend_nicegui/
├── __init__.py
├── app.py                 # NiceGUI 入口，挂载到 FastAPI
├── layout.py              # 侧边栏布局 + 路由控制
├── styles.py              # CSS 变量 + Tailwind 配置
├── pages/
│   ├── __init__.py
│   ├── dashboard.py       # 仪表盘
│   ├── resume_manager.py  # 简历管理
│   ├── search.py          # 搜索职位
│   ├── applications.py    # 投递记录
│   ├── messages.py        # 消息中心
│   └── settings.py        # 设置页面
└── components/
│   ├── __init__.py
│   ├── cards.py           # 统计卡片、状态指示器
│   ├── buttons.py         # 操作按钮
│   └── modals.py          # 弹窗、确认框
```

## UI 风格保持

### 暗黑主题

```python
from nicegui import ui

ui.dark = True  # 启用 Quasar 暗黑主题
```

### CSS 变量注入

```python
ui.add_head_html('''
<style>
    :root {
        --bg-deep: #0f0f14;
        --bg-primary: #16161d;
        --bg-card: rgba(30, 30, 40, 0.9);
        --accent-electric: #00d4ff;
        --accent-gold: #fbbf24;
        --accent-green: #4ade80;
        --accent-red: #f87171;
        --text-primary: #ffffff;
        --text-secondary: #c4c4c8;
        --border-subtle: rgba(255, 255, 255, 0.12);
    }

    /* JetBrains Mono 字体 */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    body {
        font-family: 'DM Sans', sans-serif;
        background: var(--bg-deep);
    }
</style>
''')
```

### 组件样式示例

```python
# 按钮
ui.button('搜索职位').classes(
    'px-4 py-2 rounded-lg '
    'bg-[#16161d] border border-[#00d4ff] '
    'text-[#00d4ff] font-mono font-semibold '
    'hover:bg-[rgba(0,212,255,0.15)] '
    'transition-colors duration-200'
)

# 卡片
with ui.card().classes(
    'p-4 rounded-lg '
    'bg-[rgba(30,30,40,0.9)] '
    'border border-[rgba(255,255,255,0.12)]'
):
    ui.label('内容')
```

## 页面迁移详情

### Phase 1: 入口 + 布局

**核心代码结构：**

```python
# frontend_nicegui/app.py
from nicegui import ui, app
from fastapi import FastAPI

def setup_ui(fastapi_app: FastAPI):
    """将 NiceGUI 挂载到现有 FastAPI"""

    # 全局样式
    ui.add_head_html(CSS_STYLES)
    ui.dark = True

    # 侧边栏布局
    with ui.left_drawer().classes('w-64 bg-[#16161d]') as sidebar:
        # Logo
        ui.label('AUTO_JOB_HUNTER').classes(
            'text-[#00d4ff] font-mono font-bold text-center my-4'
        )
        # 导航菜单
        nav_items = [
            ('仪表盘', 'dashboard', '🏠'),
            ('管理简历', 'resumes', '📄'),
            ('搜索职位', 'search', '🔍'),
            ('投递记录', 'applications', '📊'),
            ('消息中心', 'messages', '💬'),
            ('设置', 'settings', '⚙️'),
        ]
        for label, page_id, icon in nav_items:
            ui.button(f'{icon} {label}', on_click=lambda p=page_id: navigate(p))

    # 主内容区
    @ui.page('/')
    def index():
        render_page('dashboard')

    @ui.page('/{page_id}')
    def page_route(page_id: str):
        render_page(page_id)

    ui.run_with(fastapi_app, mount_path='/ui')
```

### Phase 3: Resume Manager（核心功能）

**当前 Streamlit 问题：**
- 复选框状态同步失败
- 批量删除弹窗状态管理混乱
- 每次操作都 `st.rerun()`

**NiceGUI 解决方案：**
- 使用 `ui.checkbox().bind_value(app.storage.user, 'selected_ids')`
- 弹窗用 `ui.dialog()` + `.open()` / `.close()`
- 列表更新用响应式绑定，无需手动刷新

```python
# frontend_nicegui/pages/resume_manager.py
from nicegui import ui, app
from backend.services.resume_service import ResumeService

async def render_resume_manager():
    ui.label('简历管理').classes('text-2xl font-bold text-center mb-4')

    # Tab 切换
    with ui.tabs().classes('w-full') as tabs:
        ui.tab('列表', icon='list')
        ui.tab('上传', icon='upload')
        ui.tab('粘贴', icon='edit')

    with ui.tab_panels(tabs).classes('w-full'):
        with ui.tab_panel('列表'):
            await render_resume_list()

        with ui.tab_panel('上传'):
            render_upload_section()

        with ui.tab_panel('粘贴'):
            render_paste_section()

async def render_resume_list():
    # 直接调用 service（无需 HTTP）
    resumes = await ResumeService.list_resumes()

    # 复选框状态
    selected = app.storage.user.get('selected_ids', set())

    # 简历卡片
    for resume in resumes:
        with ui.card().classes('w-full mb-2'):
            with ui.row().classes('w-full items-center'):
                # 复选框
                cb = ui.checkbox().bind_value_from(
                    app.storage.user, 'selected_ids',
                    lambda s: resume.id in s,
                    lambda v, s: s.add(resume.id) if v else s.discard(resume.id)
                )
                # 信息
                ui.label(resume.name).classes('font-semibold')
                ui.label(f'{resume.file_type} · {resume.created_at[:10]}').classes('text-sm text-gray-400')

            # 操作按钮
            with ui.row():
                ui.button('查看', on_click=lambda: show_detail(resume.id))
                ui.button('编辑', on_click=lambda: edit_resume(resume.id))
                if not resume.is_primary:
                    ui.button('设为主简历', on_click=lambda: set_primary(resume.id))
                ui.button('删除', on_click=lambda: confirm_delete(resume.id))
```

### Phase 4: Search 页面

```python
async def render_search():
    ui.label('搜索职位').classes('text-2xl font-bold mb-4')

    # 搜索表单
    with ui.card().classes('w-full p-4'):
        keywords = ui.input('关键词', placeholder='Python后端')
        platforms = ui.select(['boss', 'liepin'], label='平台', multiple=True)
        city = ui.input('城市', placeholder='北京')
        auto_apply = ui.checkbox('自动投递')

        ui.button('开始搜索', on_click=lambda: do_search())

    # 结果展示
    results_area = ui.column()

    async def do_search():
        results_area.clear()
        with results_area:
            ui.spinner(size='lg')
            # 异步调用，不阻塞 UI
            result = await SearchService.search(
                keywords.value,
                platforms.value,
                city.value,
                auto_apply.value
            )
            ui.spinner(visible=False)
            render_results(result)
```

## 状态管理

NiceGUI 提供三种状态存储：

| 存储 | 用途 | 生命周期 |
|------|------|----------|
| `app.storage.user` | 用户会话状态（选中项、当前页） | 浏览器会话 |
| `app.storage.general` | 全局状态（配置、缓存） | 应用生命周期 |
| 响应式绑定 `.bind_value()` | UI 元素同步 | 元素存在期间 |

**迁移映射：**

| Streamlit `st.session_state` | NiceGUI |
|------------------------------|---------|
| `page` | `app.storage.user['page']` + 路由 |
| `resume.xxx` | `app.storage.user['resume_*']` |
| `search.xxx` | `app.storage.user['search_*']` |

## 启动方式变化

### 当前方式

```bash
# 两个进程
python run.py web              # FastAPI (port 8000)
streamlit run frontend/app.py  # Streamlit (port 8501)

# 或一键启动
python run.py gui              # 同时启动两个
```

### 迁移后

```bash
# 单进程
python run.py web              # FastAPI + NiceGUI (port 8000)

# UI 访问地址
http://localhost:8000/ui       # NiceGUI 界面
http://localhost:8000/api/*    # API 端点（保留）
```

## 依赖变化

### 新增

```toml
nicegui >= 1.4.0
```

### 删除

```toml
streamlit      # 删除
```

## 验收标准

1. **UI 响应正常**：所有按钮点击立即响应，无卡顿
2. **功能完整**：所有现有功能正常工作
3. **风格一致**：保持 Obsidian Terminal 暗黑风格
4. **单服务部署**：单进程运行，单端口访问
5. **API 保留**：CLI 和外部脚本仍可调用 `/api/*`

## 风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| NiceGUI 学习曲线 | 开发速度暂时降低 | 渐进迁移，边学边做 |
| 部分组件无直接替代 | 需自定义实现 | 用 HTML + CSS 构建 |
| 后端函数调用需调整 | Service 层需暴露接口 | 逐步暴露 async 函数 |

## 时间规划

| 阶段 | 优先级 | 说明 |
|------|--------|------|
| Phase 1-3 | P0 | 核心功能，必须完成 |
| Phase 4-6 | P1 | 常用功能，重要 |
| Phase 7 | P2 | 清理，最后处理 |