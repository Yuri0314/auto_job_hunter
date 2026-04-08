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

        result = adapter._parse_message_time("04-15")
        assert result.month == 4
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
        from selenium.common.exceptions import NoSuchElementException

        # 创建 mock 元素（模拟 Selenium WebElement）
        mock_item = MagicMock()

        # 模拟 get_attribute（同步）
        mock_item.get_attribute = MagicMock(side_effect=lambda x: {
            "data-geek": "12345",
            "data-id": None,
        }.get(x))

        # 模拟 find_element（同步）
        def mock_find_element(by, xpath):
            mock_el = MagicMock()
            text_map = {
                ".//span[contains(@class, 'name')]": "张HR",
                ".//span[contains(@class, 'company-text') or contains(@class, 'company-name')]": "测试公司",
                ".//span[contains(@class, 'msg-text') or contains(@class, 'msg')]": "您好，我们正在招聘",
                ".//span[contains(@class, 'time')]": "10:30",
                ".//span[contains(@class, 'job-name')]": "Python工程师",
            }
            if xpath in text_map:
                mock_el.text = text_map[xpath]
                return mock_el
            # 未读标记不存在，抛出异常
            raise NoSuchElementException("Not found")

        mock_item.find_element = mock_find_element

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