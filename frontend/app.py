"""
Auto Job Hunter - Streamlit Web GUI

启动方式: streamlit run frontend/app.py
"""

import streamlit as st
import requests
from datetime import datetime

# API Base URL - 与后端默认端口保持一致
API_BASE = "http://localhost:8888/api"


def init_session_state():
    """初始化会话状态"""
    if "jobs" not in st.session_state:
        st.session_state.jobs = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "applications" not in st.session_state:
        st.session_state.applications = []


def fetch_jobs(status=None, keyword=None, page=1):
    """获取职位列表"""
    params = {"page": page, "page_size": 20}
    if status:
        params["status"] = status
    if keyword:
        params["keyword"] = keyword

    response = requests.get(f"{API_BASE}/jobs", params=params)
    return response.json()


def fetch_applications(page=1):
    """获取投递记录"""
    response = requests.get(f"{API_BASE}/applications", params={"page": page})
    return response.json()


def fetch_messages(page=1):
    """获取消息列表"""
    response = requests.get(f"{API_BASE}/messages", params={"page": page})
    return response.json()


def fetch_profile():
    """获取用户画像"""
    response = requests.get(f"{API_BASE}/user/profile")
    return response.json()


def update_profile(data):
    """更新用户画像"""
    response = requests.put(f"{API_BASE}/user/profile", json=data)
    return response.json()


def search_and_apply(keywords, platforms, city, salary_min, salary_max, max_count, auto_apply, greeting):
    """搜索并投递"""
    data = {
        "keywords": keywords,
        "platforms": platforms,
        "city": city if city else None,
        "salary_min": salary_min if salary_min else None,
        "salary_max": salary_max if salary_max else None,
        "max_count": max_count,
        "auto_apply": auto_apply,
        "greeting_template": greeting if greeting else None,
    }
    # 搜索需要启动浏览器、翻页等，可能需要较长时间
    response = requests.post(f"{API_BASE}/applications/search-and-apply", json=data, timeout=300.0)
    return response.json()


def fetch_system_status():
    """获取系统状态"""
    response = requests.get(f"{API_BASE}/system/status")
    return response.json()


def fetch_config_items(category=None):
    """获取配置项"""
    params = {}
    if category:
        params["category"] = category
    response = requests.get(f"{API_BASE}/settings/items", params=params)
    return response.json()


def fetch_config_categories():
    """获取配置分类"""
    response = requests.get(f"{API_BASE}/settings/categories")
    return response.json()


def update_config_item(key, value):
    """更新单个配置项"""
    response = requests.put(
        f"{API_BASE}/settings/items/{key}",
        json={"value": value}
    )
    return response.json()


def batch_update_config(items):
    """批量更新配置项"""
    response = requests.put(
        f"{API_BASE}/settings/batch",
        json={"items": items}
    )
    return response.json()


def reset_config_item(key):
    """重置配置项"""
    response = requests.post(f"{API_BASE}/settings/reset/{key}")
    return response.json()


def fetch_platform_status():
    """获取平台登录状态"""
    response = requests.get(f"{API_BASE}/system/platforms")
    return response.json()


def trigger_login(platform):
    """触发平台登录"""
    response = requests.post(f"{API_BASE}/system/login/{platform}")
    return response.json()


def fetch_login_status(platform):
    """获取登录任务状态"""
    response = requests.get(f"{API_BASE}/system/login-status/{platform}")
    return response.json()


def logout_platform(platform):
    """退出登录（清除Cookie）"""
    response = requests.post(f"{API_BASE}/system/logout/{platform}")
    return response.json()


# ========== 简历解析相关API ==========

def parse_resume_file(file_path: str, use_ai: bool = False):
    """解析指定路径的简历文件"""
    response = requests.post(
        f"{API_BASE}/resume/parse-file",
        params={"file_path": file_path, "use_ai": use_ai},
    )
    return response.json()


def upload_resume_file(file, use_ai: bool = False):
    """上传并解析简历"""
    files = {"file": file}
    response = requests.post(
        f"{API_BASE}/resume/upload",
        files=files,
        params={"use_ai": use_ai},
    )
    return response.json()


def get_resume_status():
    """获取简历状态"""
    response = requests.get(f"{API_BASE}/resume/status")
    return response.json()


def confirm_resume_result(data):
    """确认简历解析结果"""
    response = requests.put(
        f"{API_BASE}/resume/confirm",
        json={"extracted_data": data},
    )
    return response.json()


def start_one_click_job(platforms, auto_apply, max_apply, use_ai_keywords):
    """一键求职"""
    response = requests.post(
        f"{API_BASE}/resume/one-click-job",
        json={
            "platforms": platforms,
            "auto_apply": auto_apply,
            "max_apply": max_apply,
            "use_ai_keywords": use_ai_keywords,
        },
        timeout=300.0,
    )
    return response.json()


def main():
    """主函数"""
    st.set_page_config(
        page_title="Auto Job Hunter",
        page_icon="🎯",
        layout="wide",
    )

    # 初始化
    init_session_state()

    # 侧边栏
    st.sidebar.title("🎯 Auto Job Hunter")
    st.sidebar.caption("自动求职投递系统")

    page = st.sidebar.radio(
        "导航",
        ["仪表盘", "简历解析", "职位搜索", "投递记录", "消息中心", "用户配置", "系统设置"],
    )

    # 根据页面显示内容
    if page == "仪表盘":
        show_dashboard()
    elif page == "简历解析":
        show_resume_parser()
    elif page == "职位搜索":
        show_job_search()
    elif page == "投递记录":
        show_applications()
    elif page == "消息中心":
        show_messages()
    elif page == "用户配置":
        show_user_config()
    elif page == "系统设置":
        show_system_settings()


def show_resume_parser():
    """简历解析页面"""
    st.title("📄 简历解析")

    st.info("""
    上传您的PDF简历，系统将自动提取关键信息并填充到用户画像。
    解析成功后可以一键启动智能求职搜索。
    """)

    # 获取当前简历状态
    try:
        status = get_resume_status()
        if status.get("has_resume"):
            st.success("✅ 已有简历解析记录")
            if status.get("resume_file"):
                st.write(f"简历文件: `{status['resume_file']}`")
    except:
        pass

    st.divider()

    # 解析方式选择
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("方式一：上传PDF文件")
        uploaded_file = st.file_uploader(
            "选择PDF简历文件",
            type=["pdf"],
            key="resume_uploader",
        )

        use_ai = st.checkbox("使用AI模式提取", value=False, help="AI模式更准确但需要配置API Key，规则模式更快且免费")

        if uploaded_file and st.button("解析上传的简历", type="primary"):
            with st.spinner("正在解析简历..."):
                try:
                    result = upload_resume_file(uploaded_file, use_ai=use_ai)
                    if result.get("success"):
                        st.session_state["resume_result"] = result
                        st.success("简历解析成功！")
                        st.rerun()
                    else:
                        st.error(f"解析失败: {result.get('error', '未知错误')}")
                except Exception as e:
                    st.error(f"解析失败: {str(e)}")

    with col2:
        st.subheader("方式二：指定本地文件路径")
        local_path = st.text_input(
            "简历文件路径",
            value=r"C:\Users\惠天宇\Documents\【简历】朱荣+27岁+3年工作经验+北京上海.pdf",
            key="local_resume_path",
        )

        use_ai_local = st.checkbox("使用AI模式提取", value=False, key="use_ai_local")

        if st.button("解析本地简历", type="primary", key="parse_local"):
            if local_path:
                with st.spinner("正在解析简历..."):
                    try:
                        result = parse_resume_file(local_path, use_ai=use_ai_local)
                        if result.get("success"):
                            st.session_state["resume_result"] = result
                            st.success("简历解析成功！")
                            st.rerun()
                        else:
                            st.error(f"解析失败: {result.get('error', '未知错误')}")
                    except Exception as e:
                        st.error(f"解析失败: {str(e)}")
            else:
                st.warning("请输入简历文件路径")

    # 显示解析结果
    if "resume_result" in st.session_state:
        st.divider()
        st.subheader("📋 解析结果")

        result = st.session_state["resume_result"]
        data = result.get("extracted_data", {})

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**姓名**: {data.get('name', '-')}")
            st.write(f"**年龄**: {data.get('age', '-')}")
            st.write(f"**性别**: {data.get('gender', '-')}")
            st.write(f"**手机**: {data.get('phone', '-')}")
            st.write(f"**邮箱**: {data.get('email', '-')}")
            st.write(f"**学历**: {data.get('education', '-')}")
            st.write(f"**学校**: {data.get('school', '-')}")

        with col2:
            st.write(f"**工作年限**: {data.get('experience_years', '-')}年")
            st.write(f"**所在城市**: {data.get('city', '-')}")
            positions = data.get("target_positions", [])
            st.write(f"**目标职位**: {', '.join(positions) if positions else '-'}")
            cities = data.get("target_cities", [])
            st.write(f"**目标城市**: {', '.join(cities) if cities else '-'}")
            sal_min = data.get("expected_salary_min")
            sal_max = data.get("expected_salary_max")
            st.write(f"**期望薪资**: {sal_min or '?'}-{sal_max or '?'}K")

        # 技能
        skills = data.get("skills", [])
        if skills:
            st.write(f"**核心技能**: {', '.join(skills[:10])}")

        # 简历文本预览
        with st.expander("查看简历文本"):
            resume_text = result.get("resume_text", "")
            st.text_area("简历内容", resume_text[:3000], height=200)

        # 一键求职
        st.divider()
        st.subheader("🚀 一键启动求职")

        col1, col2 = st.columns(2)

        with col1:
            platforms = st.multiselect(
                "选择平台",
                ["boss", "liepin"],
                default=["boss"],
                key="one_click_platforms",
            )
            auto_apply = st.checkbox("自动投递", value=False, key="one_click_auto_apply")

        with col2:
            max_apply = st.slider("最大投递数", 5, 50, 20, key="one_click_max_apply")
            use_ai_keywords = st.checkbox("使用AI生成搜索关键词", value=False, key="one_click_use_ai")

        if st.button("启动智能求职", type="primary", key="start_one_click"):
            if not platforms:
                st.warning("请至少选择一个平台")
            else:
                with st.spinner("正在搜索职位..."):
                    try:
                        job_result = start_one_click_job(
                            platforms=platforms,
                            auto_apply=auto_apply,
                            max_apply=max_apply,
                            use_ai_keywords=use_ai_keywords,
                        )

                        if job_result.get("success"):
                            st.success("搜索完成！")

                            col1, col2, col3 = st.columns(3)
                            col1.metric("使用关键词", ", ".join(job_result.get("keywords_used", [])))
                            col2.metric("发现职位", job_result.get("total_found", 0))
                            col3.metric("已投递", job_result.get("total_applied", 0))
                        else:
                            st.error(f"搜索失败: {job_result.get('error', '未知错误')}")

                    except Exception as e:
                        st.error(f"搜索失败: {str(e)}")


def show_dashboard():
    """显示仪表盘"""
    st.title("📊 仪表盘")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("今日发现", "128", "+12")
    with col2:
        st.metric("今日投递", "35", "+5")
    with col3:
        st.metric("未读消息", "3", "-2")

    st.divider()

    # 最近职位
    st.subheader("最近职位")
    try:
        result = fetch_jobs(page=1)
        jobs = result.get("items", [])

        if jobs:
            for job in jobs[:5]:
                with st.container():
                    cols = st.columns([3, 2, 1, 1])
                    cols[0].write(f"**{job['title']}**")
                    cols[1].write(job['company'])
                    cols[2].write(job.get('salary', '面议'))
                    cols[3].write(job['city'] or '未知')
        else:
            st.info("暂无职位数据")
    except Exception as e:
        st.error(f"加载失败: {e}")

    # 投递统计
    st.subheader("投递统计")
    col1, col2 = st.columns(2)

    with col1:
        # 按平台统计
        st.bar_chart({
            "BOSS直聘": 45,
            "猎聘": 23,
            "脉脉": 12,
        })

    with col2:
        # 按状态统计
        st.bar_chart({
            "已投递": 67,
            "已回复": 23,
            "已拒绝": 8,
        })


def show_job_search():
    """显示职位搜索页面"""
    st.title("🔍 职位搜索")

    with st.form("search_form"):
        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_input("搜索关键词", placeholder="如: Python后端")
            city = st.text_input("城市", placeholder="如: 北京")

        with col2:
            platforms = st.multiselect(
                "选择平台",
                ["boss", "liepin"],
                default=["boss", "liepin"],
            )
            col_sal1, col_sal2 = st.columns(2)
            with col_sal1:
                salary_min = st.number_input("最低薪资(K)", min_value=0, max_value=200, value=0)
            with col_sal2:
                salary_max = st.number_input("最高薪资(K)", min_value=0, max_value=200, value=0)

        col3, col4 = st.columns(2)
        with col3:
            max_count = st.slider("最大投递数", 1, 50, 20)
            auto_apply = st.checkbox("自动投递", value=False)

        with col4:
            greeting = st.text_area(
                "打招呼语模板",
                placeholder="您好，我对贵公司的{position}职位很感兴趣...",
                height=100,
            )

        submitted = st.form_submit_button("搜索并投递", type="primary")

    if submitted:
        if not keywords:
            st.error("请输入搜索关键词")
        elif not platforms:
            st.error("请选择至少一个平台")
        else:
            with st.spinner("正在搜索职位..."):
                try:
                    result = search_and_apply(
                        keywords=keywords,
                        platforms=platforms,
                        city=city,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        max_count=max_count,
                        auto_apply=auto_apply,
                        greeting=greeting,
                    )

                    st.success(f"搜索完成! 发现 {result['total_found']} 个职位，过滤后 {result['filtered']} 个")

                    if result.get('applied', 0) > 0:
                        st.info(f"已投递 {result['applied']} 个职位")

                    # 显示职位列表
                    if result.get('jobs'):
                        st.subheader("发现的职位")
                        for job in result['jobs']:
                            with st.container():
                                cols = st.columns([3, 2, 1, 1])
                                cols[0].write(f"**{job['title']}**")
                                cols[1].write(job['company'])
                                cols[2].write(job.get('salary', '面议'))
                                cols[3].write(job.get('city', '未知'))

                except Exception as e:
                    st.error(f"搜索失败: {e}")


def show_applications():
    """显示投递记录页面"""
    st.title("📝 投递记录")

    # 筛选条件
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部", "success", "pending", "failed"],
        )
    with col2:
        platform_filter = st.selectbox(
            "平台筛选",
            ["全部", "boss", "liepin"],
        )

    # 获取投递记录
    try:
        result = fetch_applications(page=1)
        applications = result.get("items", [])

        if applications:
            for app in applications:
                with st.container():
                    cols = st.columns([3, 2, 1, 1])
                    cols[0].write(f"**职位ID**: {app['job_id']}")
                    cols[1].write(app['platform'])
                    cols[2].write(app['status'])

                    # 状态颜色
                    if app['status'] == 'success':
                        cols[3].success("成功")
                    elif app['status'] == 'failed':
                        cols[3].error("失败")
                    else:
                        cols[3].warning("待处理")

                    st.divider()

            st.write(f"总计: {result['total']} 条记录")
        else:
            st.info("暂无投递记录")

    except Exception as e:
        st.error(f"加载失败: {e}")


def show_messages():
    """显示消息中心页面"""
    st.title("💬 消息中心")

    # 获取消息
    try:
        result = fetch_messages(page=1)
        messages = result.get("items", [])

        # 显示未读数
        if result.get("unread", 0) > 0:
            st.info(f"您有 {result['unread']} 条未读消息")

        if messages:
            for msg in messages:
                with st.container():
                    # 消息头部
                    cols = st.columns([3, 2, 1])
                    cols[0].write(f"**{msg.get('sender_name', '未知')}** - {msg.get('company', '')}")
                    cols[1].write(msg.get('job_title', ''))
                    cols[2].write(msg.get('platform', ''))

                    # 消息内容
                    st.write(msg['content'])

                    # 操作按钮
                    if not msg.get('is_replied'):
                        if st.button("回复", key=f"reply_{msg['id']}"):
                            st.text_input("回复内容", key=f"reply_text_{msg['id']}")

                    st.divider()
        else:
            st.info("暂无消息")

    except Exception as e:
        st.error(f"加载失败: {e}")


def show_user_config():
    """显示用户配置页面"""
    st.title("⚙️ 用户配置")

    # 获取用户画像
    try:
        profile = fetch_profile()
    except Exception as e:
        st.error(f"加载用户信息失败: {e}")
        profile = {}

    # 基本信息
    st.subheader("基本信息")
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("姓名", value=profile.get("name", ""))
        phone = st.text_input("手机号", value=profile.get("phone", ""))
        city = st.text_input("所在城市", value=profile.get("city", ""))

    with col2:
        email = st.text_input("邮箱", value=profile.get("email", ""))
        experience = st.number_input("工作年限", value=profile.get("experience_years") or 0, min_value=0, max_value=50)
        education = st.selectbox(
            "学历",
            ["高中", "大专", "本科", "硕士", "博士"],
            index=["高中", "大专", "本科", "硕士", "博士"].index(profile.get("education", "本科")) if profile.get("education") else 2,
        )

    # 求职意向
    st.subheader("求职意向")
    col1, col2 = st.columns(2)

    with col1:
        target_positions = st.text_area(
            "目标职位 (每行一个)",
            value="\n".join(profile.get("target_positions") or []),
        )
        target_cities = st.text_area(
            "目标城市 (每行一个)",
            value="\n".join(profile.get("target_cities") or []),
        )

    with col2:
        sal_col1, sal_col2 = st.columns(2)
        with sal_col1:
            sal_min = st.number_input("期望薪资下限(K)", value=profile.get("expected_salary_min") or 15, min_value=0)
        with sal_col2:
            sal_max = st.number_input("期望薪资上限(K)", value=profile.get("expected_salary_max") or 30, min_value=0)

        skills = st.text_area(
            "技能标签 (每行一个)",
            value="\n".join(profile.get("skills") or []),
        )

    # 投递设置
    st.subheader("投递设置")
    col1, col2 = st.columns(2)

    with col1:
        strategy = st.selectbox(
            "投递策略",
            ["simple", "smart", "hybrid"],
            index=["simple", "smart", "hybrid"].index(profile.get("strategy", "simple")) if profile.get("strategy") else 0,
        )
        daily_limit = st.number_input("每日投递上限", value=profile.get("daily_application_limit") or 50, min_value=1, max_value=200)

    with col2:
        auto_reply = st.checkbox("自动回复HR消息", value=profile.get("auto_reply_enabled", False))

    # 保存按钮
    if st.button("保存配置", type="primary"):
        update_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "city": city,
            "experience_years": experience,
            "education": education,
            "target_positions": [p.strip() for p in target_positions.split("\n") if p.strip()],
            "target_cities": [c.strip() for c in target_cities.split("\n") if c.strip()],
            "expected_salary_min": sal_min,
            "expected_salary_max": sal_max,
            "skills": [s.strip() for s in skills.split("\n") if s.strip()],
            "strategy": strategy,
            "daily_application_limit": daily_limit,
            "auto_reply_enabled": auto_reply,
        }

        try:
            update_profile(update_data)
            st.success("配置已保存!")
        except Exception as e:
            st.error(f"保存失败: {e}")


def show_system_settings():
    """显示系统设置页面"""
    st.title("🔧 系统设置")

    # 系统状态概览
    st.subheader("系统状态")
    try:
        status = fetch_system_status()
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"版本: {status.get('version', 'unknown')}")
            st.info(f"状态: {status.get('status', 'unknown')}")

        with col2:
            st.info(f"数据库: {status.get('database', 'unknown')}")
            st.info(f"AI配置: {'已配置' if status.get('ai_configured') else '未配置'}")

        with col3:
            if status.get('platforms_configured'):
                st.write(f"已配置平台: {', '.join(status['platforms_configured'])}")

    except Exception as e:
        st.error(f"获取系统状态失败: {e}")

    st.divider()

    # 创建 Tab 结构
    tab1, tab2, tab3, tab4 = st.tabs([
        "基础配置", "平台账号", "AI配置", "高级设置"
    ])

    with tab1:
        show_basic_config()

    with tab2:
        show_platform_accounts()

    with tab3:
        show_ai_config()

    with tab4:
        show_advanced_config()


def show_basic_config():
    """基础配置"""
    try:
        configs = fetch_config_items(category="basic")
    except Exception as e:
        st.error(f"加载配置失败: {e}")
        return

    st.subheader("应用基本设置")

    # 调试模式
    debug_config = configs.get("debug", {})
    debug_enabled = st.checkbox(
        "调试模式",
        value=str(debug_config.get("effective_value", "false")).lower() == "true",
        help=debug_config.get("description", ""),
    )

    # 日志级别
    log_level_config = configs.get("log_level", {})
    log_options = log_level_config.get("options", ["DEBUG", "INFO", "WARNING", "ERROR"])
    current_log_level = log_level_config.get("effective_value", "INFO")
    log_level = st.selectbox(
        "日志级别",
        log_options,
        index=log_options.index(current_log_level) if current_log_level in log_options else 1,
        help=log_level_config.get("description", ""),
    )

    # 调度开关
    scheduler_config = configs.get("scheduler_enabled", {})
    scheduler_enabled = st.checkbox(
        "启用自动调度",
        value=str(scheduler_config.get("effective_value", "true")).lower() == "true",
        help=scheduler_config.get("description", ""),
    )

    # 最大并发数
    max_jobs_config = configs.get("max_concurrent_jobs", {})
    max_jobs = st.slider(
        "最大并发任务数",
        min_value=1,
        max_value=20,
        value=int(max_jobs_config.get("effective_value", 5)),
        help=max_jobs_config.get("description", ""),
    )

    # 保存按钮
    if st.button("保存基础配置", type="primary"):
        try:
            batch_update_config({
                "debug": str(debug_enabled).lower(),
                "log_level": log_level,
                "scheduler_enabled": str(scheduler_enabled).lower(),
                "max_concurrent_jobs": str(max_jobs),
            })
            st.success("配置已保存!")
            st.rerun()
        except Exception as e:
            st.error(f"保存失败: {e}")


def show_platform_accounts():
    """平台账号配置"""
    # 使用说明
    st.info("""
    **使用流程：**
    1. 点击「登录」按钮 → 系统会打开浏览器窗口
    2. 在浏览器中输入手机号 + 验证码完成登录
    3. 登录成功后系统自动保存登录状态（Cookie）
    """)

    try:
        platform_status = fetch_platform_status()
    except Exception as e:
        st.error(f"加载状态失败: {e}")
        return

    platforms = [
        {"name": "BOSS直聘", "prefix": "boss", "login_url": "https://www.zhipin.com"},
        {"name": "猎聘", "prefix": "liepin", "login_url": "https://www.liepin.com"},
        {"name": "脉脉", "prefix": "maimai", "login_url": "https://maimai.cn"},
    ]

    for platform in platforms:
        prefix = platform["prefix"]
        st.subheader(platform["name"])

        # 获取平台状态
        status_info = next(
            (p for p in platform_status if p["platform"] == prefix),
            {"cookie_saved": False}
        )

        # 显示登录状态
        if status_info.get("cookie_saved"):
            st.success("✅ 登录状态: 已登录")
        else:
            st.warning("⏳ 登录状态: 未登录")

        # 登录操作按钮
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if st.button(f"🔐 登录 {platform['name']}", key=f"login_{prefix}", type="primary"):
                try:
                    result = trigger_login(prefix)
                    if result.get("status") == "started":
                        st.success("浏览器已打开，请在浏览器中完成登录")
                        st.info(f"登录地址: {platform['login_url']}")
                    elif result.get("status") == "already_running":
                        st.warning("登录任务正在进行中，请在浏览器中完成登录")
                    else:
                        st.error(f"启动失败: {result}")
                except Exception as e:
                    st.error(f"登录失败: {e}")

        with col2:
            if st.button(f"🔄 刷新", key=f"refresh_{prefix}"):
                st.rerun()

        with col3:
            if st.button(f"🚪 退出", key=f"logout_{prefix}"):
                try:
                    logout_platform(prefix)
                    st.success("已退出登录")
                    st.rerun()
                except Exception as e:
                    st.error(f"操作失败: {e}")

        st.divider()


def show_ai_config():
    """AI配置"""
    try:
        configs = fetch_config_items(category="ai")
    except Exception as e:
        st.error(f"加载配置失败: {e}")
        return

    st.subheader("AI 服务配置")

    # 判断当前使用的提供商
    openai_key_config = configs.get("openai_api_key", {})
    ollama_url_config = configs.get("ollama_base_url", {})

    has_openai = openai_key_config.get("effective_value")
    has_ollama = ollama_url_config.get("effective_value")

    # 选择提供商
    provider_options = ["OpenAI", "Ollama (本地)"]
    current_provider = "OpenAI" if has_openai else ("Ollama (本地)" if has_ollama else "OpenAI")

    provider = st.radio(
        "AI服务提供商",
        provider_options,
        index=provider_options.index(current_provider),
    )

    if provider == "OpenAI":
        st.subheader("OpenAI 配置")

        # API Key 状态
        if has_openai:
            st.success("API Key: 已配置")
        else:
            st.warning("API Key: 未配置")

        # 输入新 API Key
        new_key = st.text_input(
            "OpenAI API Key（填写则更新）",
            value="",
            type="password",
            placeholder="sk-...",
            help="更新 OpenAI API 密钥",
        )

        # 模型选择
        model_config = configs.get("openai_model", {})
        model_options = model_config.get("options", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
        current_model = model_config.get("effective_value", "gpt-4")

        model = st.selectbox(
            "模型",
            model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="选择使用的 GPT 模型",
        )

        if st.button("保存 OpenAI 配置", type="primary"):
            try:
                updates = {"openai_model": model}
                if new_key:
                    updates["openai_api_key"] = new_key
                batch_update_config(updates)
                st.success("配置已保存!")
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")

        if st.button("重置 OpenAI API Key"):
            try:
                reset_config_item("openai_api_key")
                st.success("API Key 已重置!")
                st.rerun()
            except Exception as e:
                st.error(f"重置失败: {e}")

    else:
        st.subheader("Ollama 本地模型配置")

        # Ollama 服务地址
        ollama_url = st.text_input(
            "Ollama 服务地址",
            value=ollama_url_config.get("effective_value", "http://localhost:11434"),
            placeholder="http://localhost:11434",
            help="本地 Ollama 服务地址",
        )

        # Ollama 模型
        ollama_model_config = configs.get("ollama_model", {})
        ollama_model = st.text_input(
            "模型名称",
            value=ollama_model_config.get("effective_value", "llama2"),
            placeholder="llama2, llama3, mistral 等",
            help="本地 Ollama 模型名称",
        )

        if st.button("保存 Ollama 配置", type="primary"):
            try:
                batch_update_config({
                    "ollama_base_url": ollama_url,
                    "ollama_model": ollama_model,
                })
                st.success("配置已保存!")
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")


def show_advanced_config():
    """高级设置"""
    try:
        configs = fetch_config_items(category="advanced")
    except Exception as e:
        st.error(f"加载配置失败: {e}")
        return

    st.subheader("高级设置")

    # Webhook URL
    webhook_config = configs.get("webhook_url", {})
    webhook_url = st.text_input(
        "Webhook URL",
        value=webhook_config.get("effective_value", ""),
        placeholder="https://your-webhook-url",
        help="通知推送地址",
    )

    # 日志文件
    log_file_config = configs.get("log_file", {})
    log_file = st.text_input(
        "日志文件路径",
        value=log_file_config.get("effective_value", ""),
        placeholder="logs/app.log",
        help="日志存储路径",
    )

    st.divider()
    st.subheader("SMTP 邮件配置")

    # SMTP 配置
    smtp_host_config = configs.get("smtp_host", {})
    smtp_host = st.text_input(
        "SMTP 服务器",
        value=smtp_host_config.get("effective_value", ""),
        placeholder="smtp.example.com",
    )

    smtp_port_config = configs.get("smtp_port", {})
    smtp_port = st.number_input(
        "SMTP 端口",
        value=int(smtp_port_config.get("effective_value", 586)) if smtp_port_config.get("effective_value") else 586,
        min_value=1,
        max_value=65535,
    )

    smtp_username_config = configs.get("smtp_username", {})
    smtp_username = st.text_input(
        "SMTP 用户名",
        value=smtp_username_config.get("effective_value", ""),
    )

    smtp_password_config = configs.get("smtp_password", {})
    smtp_password_status = smtp_password_config.get("effective_value", "")
    if smtp_password_status:
        st.success("SMTP 密码: 已配置")
    else:
        st.warning("SMTP 密码: 未配置")

    smtp_password = st.text_input(
        "SMTP 密码（填写则更新）",
        value="",
        type="password",
        placeholder="输入新密码",
    )

    # 保存按钮
    if st.button("保存高级设置", type="primary"):
        try:
            updates = {
                "webhook_url": webhook_url,
                "log_file": log_file,
                "smtp_host": smtp_host,
                "smtp_port": str(smtp_port),
                "smtp_username": smtp_username,
            }
            if smtp_password:
                updates["smtp_password"] = smtp_password

            batch_update_config(updates)
            st.success("配置已保存!")
            st.rerun()
        except Exception as e:
            st.error(f"保存失败: {e}")


if __name__ == "__main__":
    main()