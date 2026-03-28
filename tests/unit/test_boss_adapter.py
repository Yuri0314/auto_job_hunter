"""BOSS适配器消息解析测试"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock


class TestParseMessageTime:
    """测试消息时间解析"""

    def test_time_today(self):
        """测试今天的时间格式 HH:MM"""
        from backend.adapters.boss_adapter import BossAdapter

        adapter = BossAdapter.__new__(BossAdapter)
        now = datetime.now()

        result = adapter._parse_message_time("10:30")
        assert result.hour == 10
        assert result.minute == 30

    def test_time_yesterday(self):
        """测试昨天的时间格式"""
        from backend.adapters.boss_adapter import BossAdapter

        adapter = BossAdapter.__new__(BossAdapter)

        result = adapter._parse_message_time("昨天 10:30")
        assert result.hour == 10
        assert result.minute == 30

    def test_time_date_time(self):
        """测试 MM-DD HH:MM 格式"""
        from backend.adapters.boss_adapter import BossAdapter

        adapter = BossAdapter.__new__(BossAdapter)

        result = adapter._parse_message_time("03-15 10:30")
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_time_date_only(self):
        """测试 MM-DD 格式"""
        from backend.adapters.boss_adapter import BossAdapter

        adapter = BossAdapter.__new__(BossAdapter)

        result = adapter._parse_message_time("03-15")
        assert result.month == 3
        assert result.day == 15

    def test_time_empty(self):
        """测试空时间"""
        from backend.adapters.boss_adapter import BossAdapter

        adapter = BossAdapter.__new__(BossAdapter)

        result = adapter._parse_message_time("")
        assert isinstance(result, datetime)

    def test_time_invalid(self):
        """测试无效时间格式"""
        from backend.adapters.boss_adapter import BossAdapter

        adapter = BossAdapter.__new__(BossAdapter)

        result = adapter._parse_message_time("invalid")
        assert isinstance(result, datetime)


@pytest.mark.asyncio
class TestParseChatItem:
    """测试消息项解析"""

    async def test_parse_chat_item_basic(self):
        """测试基本消息项解析"""
        from backend.adapters.boss_adapter import BossAdapter

        # 创建 mock 元素
        mock_item = AsyncMock()

        # 模拟 get_attribute
        mock_item.get_attribute = AsyncMock(side_effect=lambda x: {
            "data-geek": "12345",
            "data-id": None,
        }.get(x))

        # 模拟 query_selector
        async def mock_query_selector(selector):
            mock_el = AsyncMock()
            mock_el.inner_text = AsyncMock(return_value={
                ".name": "张HR",
                ".company-text": "测试公司",
                ".company-name": "测试公司",
                ".msg-text": "您好，我们正在招聘",
                ".msg": "您好，我们正在招聘",
                ".time": "10:30",
                ".job-name": "Python工程师",
            }.get(selector, ""))
            return mock_el

        mock_item.query_selector = mock_query_selector

        # 模拟未读检查
        async def mock_query_selector_unread(selector):
            if selector == ".unread":
                return None  # 没有未读标记 = 已读
            return await mock_query_selector(selector)

        mock_item.query_selector = mock_query_selector_unread

        # 测试
        adapter = BossAdapter.__new__(BossAdapter)
        result = await adapter._parse_chat_item(mock_item)

        assert result is not None
        assert result.id == "12345"
        assert result.hr_name == "张HR"
        assert result.company == "测试公司"
        assert result.content == "您好，我们正在招聘"
        assert result.is_read == True
        assert result.platform == "boss"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])