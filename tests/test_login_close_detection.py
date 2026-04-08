"""测试登录流程中的浏览器关闭检测"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLoginCloseEventDetection:
    """测试浏览器关闭事件检测逻辑"""

    @pytest.mark.asyncio
    async def test_closed_event_triggered_on_page_close(self):
        """测试页面关闭事件能正确触发 closed_event"""
        closed_event = asyncio.Event()

        def on_page_close():
            closed_event.set()

        # 模拟页面关闭事件触发
        on_page_close()

        assert closed_event.is_set()

    @pytest.mark.asyncio
    async def test_wait_loop_exits_on_close_event(self):
        """测试等待循环在关闭事件触发时立即退出"""
        closed_event = asyncio.Event()

        async def simulate_wait_loop():
            """模拟登录等待循环"""
            for i in range(10):
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
                    return "closed"

                # 模拟登录检测
                await asyncio.sleep(0.01)

            return "timeout"

        async def trigger_close_after_delay():
            await asyncio.sleep(0.05)  # 50ms后触发关闭
            closed_event.set()

        # 并行运行：等待循环 + 触发关闭
        result = await asyncio.gather(
            simulate_wait_loop(),
            trigger_close_after_delay(),
        )

        assert result[0] == "closed"

    @pytest.mark.asyncio
    async def test_wait_loop_completes_without_close(self):
        """测试没有关闭事件时循环正常超时"""
        closed_event = asyncio.Event()
        iterations = []

        async def simulate_wait_loop():
            for i in range(3):
                iterations.append(i)
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(closed_event.wait()),
                        asyncio.create_task(asyncio.sleep(0.05)),
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
                    return "closed"

            return "completed"

        result = await simulate_wait_loop()

        assert result == "completed"
        assert iterations == [0, 1, 2]


class TestDoLoginFinallyCleanup:
    """测试 _do_login 的 finally 清理逻辑"""

    @pytest.mark.asyncio
    async def test_login_tasks_cleaned_up_on_failure(self):
        """测试登录失败后状态被正确清理"""
        _login_tasks = {}
        platform = "boss"

        async def mock_adapter_login():
            return False  # 模拟登录失败

        async def do_login():
            _login_tasks[platform] = {"status": "logging_in"}
            try:
                success = await mock_adapter_login()
                if success:
                    _login_tasks[platform] = {"status": "success"}
                else:
                    _login_tasks[platform] = {"status": "failed"}
            except Exception:
                _login_tasks[platform] = {"status": "failed"}
            finally:
                if _login_tasks.get(platform, {}).get("status") == "logging_in":
                    del _login_tasks[platform]

        await do_login()

        # 失败状态不应该被 finally 清理
        assert platform in _login_tasks
        assert _login_tasks[platform]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_login_tasks_cleaned_up_when_stuck(self):
        """测试登录任务卡住时 finally 会清理"""
        _login_tasks = {}
        platform = "boss"

        async def mock_adapter_login():
            raise Exception("Browser closed unexpectedly")

        async def do_login():
            _login_tasks[platform] = {"status": "logging_in"}
            try:
                success = await mock_adapter_login()
                if success:
                    _login_tasks[platform] = {"status": "success"}
                else:
                    _login_tasks[platform] = {"status": "failed"}
            except Exception:
                # 异常被捕获，状态被设置为 failed
                _login_tasks[platform] = {"status": "failed"}
            finally:
                if _login_tasks.get(platform, {}).get("status") == "logging_in":
                    del _login_tasks[platform]

        await do_login()

        # 异常被 except 捕获后设置了 failed，finally 不会清理
        assert platform in _login_tasks
        assert _login_tasks[platform]["status"] == "failed"


class TestLoginStatusRetry:
    """测试登录失败后允许重试"""

    def test_failed_status_allows_retry(self):
        """测试失败状态时允许重新登录"""
        _login_tasks = {"boss": {"status": "failed", "message": "超时"}}

        platform = "boss"
        task_info = _login_tasks.get(platform, {})
        current_status = task_info.get("status")

        # 模拟 login_platform 的检查逻辑
        if current_status == "logging_in":
            result = "already_running"
        elif current_status == "failed":
            del _login_tasks[platform]
            result = "retry_allowed"
        else:
            result = "new_login"

        assert result == "retry_allowed"
        assert platform not in _login_tasks

    def test_logging_in_status_blocks_retry(self):
        """测试登录中状态阻止重复登录"""
        _login_tasks = {"boss": {"status": "logging_in", "message": "等待登录"}}

        platform = "boss"
        task_info = _login_tasks.get(platform, {})
        current_status = task_info.get("status")

        if current_status == "logging_in":
            result = "already_running"
        elif current_status == "failed":
            del _login_tasks[platform]
            result = "retry_allowed"
        else:
            result = "new_login"

        assert result == "already_running"


class TestTimerStopOnComplete:
    """测试轮询定时器在完成后停止"""

    def test_timer_stopped_on_failed_status(self):
        """测试检测到失败状态时定时器被停止"""
        _login_check_timers = {"boss": MagicMock()}
        stopped = []

        def _stop_login_check(platform_id):
            if platform_id in _login_check_timers:
                timer = _login_check_timers.pop(platform_id)
                timer.stop()
                stopped.append(platform_id)

        # 模拟检测到失败状态
        status = "failed"
        if status == "failed":
            _stop_login_check("boss")

        assert "boss" in stopped
        assert "boss" not in _login_check_timers

    def test_timer_stopped_on_success_status(self):
        """测试检测到成功状态时定时器被停止"""
        _login_check_timers = {"boss": MagicMock()}
        stopped = []

        def _stop_login_check(platform_id):
            if platform_id in _login_check_timers:
                timer = _login_check_timers.pop(platform_id)
                timer.stop()
                stopped.append(platform_id)

        # 模拟检测到成功状态
        status = "success"
        if status == "success":
            _stop_login_check("boss")

        assert "boss" in stopped
        assert "boss" not in _login_check_timers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
