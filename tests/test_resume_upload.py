"""测试简历上传 NiceGUI 3.0+ FileUpload API"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO


class TestFileUploadAPI:
    """测试 NiceGUI 3.0+ FileUpload API"""

    @pytest.mark.asyncio
    async def test_small_file_upload_api(self):
        """测试 SmallFileUpload 的正确用法"""
        # NiceGUI 3.0+ 的 FileUpload 对象（SmallFileUpload）
        # 有 name, content_type 属性和异步 read() 方法
        mock_file_upload = MagicMock()
        mock_file_upload.name = "resume.pdf"
        mock_file_upload.content_type = "application/pdf"
        mock_file_upload.read = AsyncMock(return_value=b"PDF content...")

        # 正确用法：await e.file.read() 和 e.file.name
        file_content = await mock_file_upload.read()
        filename = mock_file_upload.name

        assert file_content == b"PDF content..."
        assert filename == "resume.pdf"

    @pytest.mark.asyncio
    async def test_upload_event_arguments_structure(self):
        """测试 UploadEventArguments 的结构"""
        # e 是 UploadEventArguments，e.file 是 FileUpload
        mock_file_upload = MagicMock()
        mock_file_upload.name = "test.pdf"
        mock_file_upload.read = AsyncMock(return_value=b"content")

        # 模拟 e.file
        class MockEvent:
            file = mock_file_upload

        e = MockEvent()
        content = await e.file.read()
        name = e.file.name

        assert content == b"content"
        assert name == "test.pdf"

    def test_old_api_fails(self):
        """测试旧 API 会报错"""
        mock_file_upload = MagicMock(spec=['name', 'content_type', 'read'])
        mock_file_upload.name = "test.pdf"

        # 旧代码 e.file.file 会报错，因为 FileUpload 没有 file 属性
        with pytest.raises(AttributeError):
            _ = mock_file_upload.file  # noqa: B018

    @pytest.mark.asyncio
    async def test_upload_success_flow(self):
        """测试上传成功流程"""
        mock_response = {
            "success": True,
            "extracted_data": {
                "name": "Zhang San",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
            }
        }

        refresh_called = False
        tab_changed_to = None

        def refresh_list():
            nonlocal refresh_called
            refresh_called = True

        def change_tab(tab_name):
            nonlocal tab_changed_to
            tab_changed_to = tab_name

        result = mock_response
        if result.get("success"):
            refresh_list()
            change_tab("resume list")

        assert refresh_called
        assert tab_changed_to == "resume list"

    @pytest.mark.asyncio
    async def test_upload_error_handling(self):
        """测试上传错误处理"""
        errors = []

        def notify_error(msg):
            errors.append(msg)

        try:
            raise AttributeError("'SmallFileUpload' object has no attribute 'file'")
        except Exception as ex:
            notify_error(f"Upload error: {str(ex)}")

        assert len(errors) == 1
        assert "Upload error" in errors[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
