"""
Auto Job Hunter - Streamlit Web GUI

启动方式: streamlit run frontend/app.py
"""

import streamlit as st
import httpx
from datetime import datetime
import asyncio

# API Base URL
API_BASE = "http://localhost:8000/api"


def init_session_state():
    """初始化会话状态"""
    if "jobs" not in st.session_state:
        st.session_state.jobs = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "applications" not in st.session_state:
        st.session_state.applications = []


async def fetch_jobs(status=None, keyword=None, page=1):
    """获取职位列表"""
    params = {"page": page, "page_size": 20}
    if status:
        params["status"] = status
    if keyword:
        params["keyword"] = keyword

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/jobs", params=params)
        return response.json()


async def fetch_applications(page=1):
    """获取投递记录"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/applications", params={"page": page})
        return response.json()


async def fetch_messages(page=1):
    """获取消息列表"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/messages", params={"page": page})
        return response.json()


async def fetch_profile():
    """获取用户画像"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/user/profile")
        return response.json()


async def update_profile(data):
    """更新用户画像"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{API_BASE}/user/profile", json=data)
        return response.json()


async def search_and_apply(keywords, platforms, city, salary_min, salary_max, max_count, auto_apply, greeting):
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
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{API_BASE}/applications/search-and-apply", json=data)
        return response.json()


async def fetch_system_status():
    """获取系统状态"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/system/status")
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
        ["仪表盘", "职位搜索", "投递记录", "消息中心", "用户配置", "系统设置"],
    )

    # 根据页面显示内容
    if page == "仪表盘":
        show_dashboard()
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
        result = asyncio.run(fetch_jobs(page=1))
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
                    result = asyncio.run(search_and_apply(
                        keywords=keywords,
                        platforms=platforms,
                        city=city,
                        salary_min=salary_min,
                        salary_max=salary_max,
                        max_count=max_count,
                        auto_apply=auto_apply,
                        greeting=greeting,
                    ))

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
        result = asyncio.run(fetch_applications(page=1))
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
        result = asyncio.run(fetch_messages(page=1))
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
        profile = asyncio.run(fetch_profile())
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
            asyncio.run(update_profile(update_data))
            st.success("配置已保存!")
        except Exception as e:
            st.error(f"保存失败: {e}")


def show_system_settings():
    """显示系统设置页面"""
    st.title("🔧 系统设置")

    # 系统状态
    st.subheader("系统状态")
    try:
        status = asyncio.run(fetch_system_status())
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"版本: {status.get('version', 'unknown')}")
            st.info(f"状态: {status.get('status', 'unknown')}")

        with col2:
            st.info(f"数据库: {status.get('database', 'unknown')}")
            st.info(f"AI配置: {'已配置' if status.get('ai_configured') else '未配置'}")

        if status.get('platforms_configured'):
            st.write(f"已配置平台: {', '.join(status['platforms_configured'])}")

    except Exception as e:
        st.error(f"获取系统状态失败: {e}")

    # 平台登录
    st.subheader("平台登录")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**BOSS直聘**")
        if st.button("登录BOSS直聘"):
            st.info("请在浏览器中完成登录...")

    with col2:
        st.write("**猎聘**")
        if st.button("登录猎聘"):
            st.info("请在浏览器中完成登录...")

    # 过滤规则
    st.subheader("过滤规则")

    with st.form("filter_rule"):
        rule_name = st.text_input("规则名称")
        col1, col2 = st.columns(2)

        with col1:
            keywords = st.text_area("关键词 (每行一个)")
            exclude = st.text_area("排除关键词 (每行一个)")
            cities = st.text_area("城市 (每行一个)")

        with col2:
            sal_min = st.number_input("薪资下限(K)", 0, 200, 0)
            sal_max = st.number_input("薪资上限(K)", 0, 200, 0)
            priority = st.number_input("优先级", 0, 100, 0)

        if st.form_submit_button("添加规则"):
            st.success("规则已添加!")


if __name__ == "__main__":
    main()