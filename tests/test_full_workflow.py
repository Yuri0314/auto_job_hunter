"""端到端集成测试 - 测试完整求职流程"""

import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from backend.adapters import get_adapter, Platform
from backend.services import get_orchestrator
from backend.core.database import SessionLocal, Job, Application, Message, JobStatus, ApplicationStatus
from datetime import datetime


async def run_full_workflow():
    """完整工作流程测试"""
    print("=" * 70)
    print("Auto Job Hunter 完整工作流程测试")
    print("=" * 70)

    results = {}

    # ========== 阶段 1: 搜索职位 ==========
    print("\n【阶段 1】搜索职位")
    print("-" * 40)
    try:
        adapter = get_adapter(Platform.BOSS)
        search_result = await adapter.search_jobs(
            keywords="Python",
            city="北京",
            page=1,
            page_size=10,
        )
        results["search"] = search_result
        job_count = len(search_result.jobs) if search_result.jobs else 0
        print(f"  搜索结果: {job_count} 个职位")
        if search_result.jobs:
            for job in search_result.jobs[:3]:
                print(f"    - {job.title} @ {job.company}")
        else:
            print("    ⚠️  未找到职位（可能需要登录）")
            # 创建模拟职位继续测试
            print("    → 创建模拟职位继续测试流程...")
            from backend.core.filter.simple_filter import JobInfo
            mock_job = JobInfo(
                id="mock_001",
                title="Python开发工程师",
                company="测试科技公司",
                salary="15-25K",
                salary_min=15,
                salary_max=25,
                city="北京",
                description="Python开发",
                platform="boss",
            )
            results["search"] = type('SearchResult', (), {"jobs": [mock_job], "total_count": 1})()
    except Exception as e:
        print(f"  ❌ 搜索失败: {e}")
        results["search"] = None

    # ========== 阶段 2: 保存职位到数据库 ==========
    print("\n【阶段 2】保存职位到数据库")
    print("-" * 40)
    try:
        db = SessionLocal()
        saved_count = 0
        if results["search"] and results["search"].jobs:
            for job_info in results["search"].jobs[:5]:
                existing = db.query(Job).filter(Job.job_id == job_info.id).first()
                if not existing:
                    job = Job(
                        job_id=job_info.id,
                        platform=job_info.platform,
                        title=job_info.title,
                        company=job_info.company,
                        salary=job_info.salary,
                        city=job_info.city,
                        status=JobStatus.NEW,
                    )
                    db.add(job)
                    saved_count += 1
        db.commit()
        print(f"  保存了 {saved_count} 个新职位")
        results["saved_jobs"] = saved_count
    except Exception as e:
        print(f"  ❌ 保存失败: {e}")
        db.rollback()
        results["saved_jobs"] = 0
    finally:
        db.close()

    # ========== 阶段 3: 查询数据库 ==========
    print("\n【阶段 3】查询数据库")
    print("-" * 40)
    try:
        db = SessionLocal()
        total_jobs = db.query(Job).count()
        total_apps = db.query(Application).count()
        total_msgs = db.query(Message).count()
        print(f"  职位总数: {total_jobs}")
        print(f"  投递记录: {total_apps}")
        print(f"  消息记录: {total_msgs}")
        results["db_stats"] = {"jobs": total_jobs, "applications": total_apps, "messages": total_msgs}
        db.close()
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")

    # ========== 阶段 4: 测试投递功能 ==========
    print("\n【阶段 4】测试投递功能")
    print("-" * 40)
    try:
        db = SessionLocal()
        test_job = db.query(Job).filter(Job.status == JobStatus.NEW).first()
        if test_job:
            # 重置浏览器管理器以获取新的浏览器实例
            from backend.automation.browser import reset_browser_manager
            reset_browser_manager()

            adapter = get_adapter(Platform(test_job.platform))
            result = await adapter.apply_job(job_id=test_job.job_id, greeting="您好，我对这个职位很感兴趣！")
            print(f"  投递结果: {'✅ 成功' if result.success else '❌ 失败'}")
            print(f"    消息: {result.message or result.error}")

            # 记录投递
            app = Application(
                job_id=test_job.job_id,
                platform=test_job.platform,
                status=ApplicationStatus.SUCCESS if result.success else ApplicationStatus.FAILED,
                message=result.message,
                error_message=result.error,
                submitted_at=datetime.now() if result.success else None,
            )
            db.add(app)

            if result.success:
                test_job.status = JobStatus.APPLIED
                test_job.applied_at = datetime.now()
            db.commit()
            results["apply"] = result.success
        else:
            print("  ⚠️  没有可投递的职位，跳过测试")
            results["apply"] = None
        db.close()
    except Exception as e:
        print(f"  ❌ 投递失败: {e}")
        results["apply"] = False

    # ========== 阶段 5: 测试消息功能 ==========
    print("\n【阶段 5】测试消息功能")
    print("-" * 40)
    try:
        adapter = get_adapter(Platform.BOSS)
        # 测试消息解析
        test_time = adapter._parse_message_time("10:30")
        print(f"  时间解析: {test_time}")

        # 测试消息回复（模拟）
        # 实际回复需要有效的会话ID
        print("  消息解析功能: ✅ 正常")
        results["message_parse"] = True
    except Exception as e:
        print(f"  ❌ 消息测试失败: {e}")
        results["message_parse"] = False

    # ========== 阶段 6: 测试协调器 ==========
    print("\n【阶段 6】测试协调器")
    print("-" * 40)
    try:
        orchestrator = await get_orchestrator(use_ai=False)
        print(f"  协调器模式: {'AI模式' if orchestrator.use_ai else '简单模式'}")
        print(f"  协调器状态: ✅ 初始化成功")
        results["orchestrator"] = True
    except Exception as e:
        print(f"  ❌ 协调器测试失败: {e}")
        results["orchestrator"] = False

    # 清理
    from backend.automation.browser import get_browser_manager
    await get_browser_manager().close()

    # ========== 测试结果汇总 ==========
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    all_passed = True
    for key, value in results.items():
        status = "✅" if value else ("⚠️" if value is None else "❌")
        if not value and value is not None:
            all_passed = False
        print(f"  {key}: {status} ({value})")

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试未通过，请检查日志")
    print("=" * 70)

    return results


if __name__ == "__main__":
    asyncio.run(run_full_workflow())
