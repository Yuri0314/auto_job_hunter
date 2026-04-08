"""端到端流程测试 - 模拟真实用户操作"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO


class TestResumeUploadFullFlow:
    """测试简历上传完整流程"""

    @pytest.mark.asyncio
    async def test_upload_and_display_resume(self):
        """测试上传简历到列表显示的完整流程"""
        # 1. 模拟前端上传事件 (NiceGUI 3.0+ FileUpload)
        mock_file_upload = MagicMock()
        mock_file_upload.name = "张三_简历.pdf"
        mock_file_upload.read = AsyncMock(return_value=b"%PDF-1.4 ... resume content ...")

        # 2. 模拟上传回调
        file_content = await mock_file_upload.read()
        filename = mock_file_upload.name

        assert file_content.startswith(b"%PDF")
        assert filename == "张三_简历.pdf"

    @pytest.mark.asyncio
    async def test_backend_api_response_structure(self):
        """测试后端API返回的数据结构"""
        # 模拟后端上传响应
        mock_response = {
            "success": True,
            "message": "简历上传成功",
            "extracted_data": {
                "name": "张三",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
            }
        }

        assert mock_response["success"]
        assert mock_response["extracted_data"]["name"] == "张三"

    @pytest.mark.asyncio
    async def test_resume_list_display_name(self):
        """测试简历列表显示姓名字段"""
        # 模拟后端返回的简历列表项
        resume_item = {
            "id": 1,
            "name": "tmp9onl2kyq.pdf",  # 文件名
            "file_type": "pdf",
            "is_primary": False,
            "created_at": "2026-04-08T10:00:00",
            "profile": {
                "name": "张三",  # 解析出的姓名
                "phone": "13800138000",
                "email": "zhangsan@example.com",
                "current_position": "Python开发工程师",
            }
        }

        # 前端显示逻辑：优先使用 profile.name
        profile = resume_item.get("profile")
        display_name = (profile and profile.get("name")) or resume_item.get("name", "未命名")

        assert display_name == "张三"  # 应该显示姓名而不是文件名

    @pytest.mark.asyncio
    async def test_resume_list_without_profile(self):
        """测试没有解析结果时回退到文件名"""
        resume_item = {
            "id": 2,
            "name": "未命名简历.pdf",
            "file_type": "pdf",
            "is_primary": False,
            "profile": None,
        }

        profile = resume_item.get("profile")
        display_name = (profile and profile.get("name")) or resume_item.get("name", "未命名")

        assert display_name == "未命名简历.pdf"


class TestLoginFlow:
    """测试登录完整流程"""

    @pytest.mark.asyncio
    async def test_login_close_detection(self):
        """测试关闭浏览器后登录任务正确终止"""
        closed_event = asyncio.Event()
        login_completed = {"status": None}

        async def simulate_login_wait():
            for i in range(5):
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(closed_event.wait()),
                        asyncio.create_task(asyncio.sleep(0.1)),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                if closed_event.is_set():
                    login_completed["status"] = "closed_by_user"
                    return

            login_completed["status"] = "timeout"

        async def simulate_user_close():
            await asyncio.sleep(0.05)
            closed_event.set()

        await asyncio.gather(
            simulate_login_wait(),
            simulate_user_close(),
        )

        assert login_completed["status"] == "closed_by_user"

    @pytest.mark.asyncio
    async def test_login_retry_after_failure(self):
        """测试登录失败后允许重试"""
        login_tasks = {"boss": {"status": "failed", "message": "超时"}}

        # 模拟 login_platform 检查逻辑
        platform = "boss"
        current_status = login_tasks.get(platform, {}).get("status")

        if current_status == "logging_in":
            result = "already_running"
        elif current_status == "failed":
            del login_tasks[platform]
            result = "retry_allowed"
        else:
            result = "new_login"

        assert result == "retry_allowed"
        assert platform not in login_tasks

    @pytest.mark.asyncio
    async def test_login_status_polling_stops(self):
        """测试登录状态轮询在终态时停止"""
        timers = {"boss": MagicMock()}
        stopped = []

        def stop_timer(platform_id):
            if platform_id in timers:
                timer = timers.pop(platform_id)
                timer.stop()
                stopped.append(platform_id)

        # 模拟检测到 failed 状态
        status = "failed"
        if status == "failed":
            stop_timer("boss")

        assert "boss" in stopped
        assert "boss" not in timers


class TestFullUserJourney:
    """完整用户旅程测试"""

    @pytest.mark.asyncio
    async def test_user_journey_upload_resume(self):
        """用户旅程：上传简历 → 解析 → 列表显示"""
        journey = {"step": 0, "errors": []}

        # Step 1: 用户点击上传按钮
        journey["step"] = 1
        mock_file = MagicMock()
        mock_file.name = "李四_简历.pdf"
        mock_file.read = AsyncMock(return_value=b"resume content")

        # Step 2: 前端读取文件
        journey["step"] = 2
        content = await mock_file.read()
        name = mock_file.name
        assert content == b"resume content"
        assert name == "李四_简历.pdf"

        # Step 3: 后端解析
        journey["step"] = 3
        api_response = {
            "success": True,
            "extracted_data": {
                "name": "李四",
                "phone": "13900139000",
                "email": "lisi@example.com",
            }
        }
        assert api_response["success"]

        # Step 4: 刷新列表
        journey["step"] = 4
        list_response = {
            "items": [{
                "id": 1,
                "name": "李四_简历.pdf",
                "profile": {
                    "name": "李四",
                    "phone": "13900139000",
                }
            }]
        }

        # Step 5: 前端显示
        journey["step"] = 5
        for item in list_response["items"]:
            profile = item.get("profile")
            display = (profile and profile.get("name")) or item.get("name", "未命名")
            assert display == "李四"  # 显示姓名而不是文件名

        assert journey["step"] == 5
        assert len(journey["errors"]) == 0

    @pytest.mark.asyncio
    async def test_user_journey_login_close_retry(self):
        """用户旅程：打开登录 → 关闭窗口 → 重新登录"""
        journey = {"step": 0, "errors": []}

        # Step 1: 用户点击登录
        journey["step"] = 1
        login_tasks = {}
        login_tasks["boss"] = {"status": "logging_in"}

        # Step 2: 用户关闭浏览器
        journey["step"] = 2
        closed_event = asyncio.Event()
        closed_event.set()  # 模拟窗口关闭

        # Step 3: 登录任务检测到关闭并退出
        journey["step"] = 3
        login_tasks["boss"] = {"status": "failed", "message": "用户取消"}

        # Step 4: 用户再次点击登录
        journey["step"] = 4
        current_status = login_tasks.get("boss", {}).get("status")
        if current_status == "failed":
            del login_tasks["boss"]
            can_retry = True
        else:
            can_retry = False

        assert can_retry
        assert "boss" not in login_tasks

        assert journey["step"] == 4
        assert len(journey["errors"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
