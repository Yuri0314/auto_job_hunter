"""简历解析器单元测试"""

import pytest
import tempfile
import os

from backend.core.resume import (
    PDFParser,
    DocxParser,
    MarkdownParser,
    TxtParser,
    TextParser,
    RuleExtractor,
    StrategyGenerator,
    ResumeService,
)


class TestPDFParser:
    """PDF解析器测试"""

    def test_can_parse_pdf(self):
        """测试PDF文件识别"""
        parser = PDFParser()
        assert parser.can_parse("test.pdf") == True
        assert parser.can_parse("test.txt") == False


class TestTxtParser:
    """TXT解析器测试"""

    def test_extract_text(self):
        """测试文本提取"""
        parser = TxtParser()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("姓名：张三\n电话：13800138000\nPython工程师，5年经验")
            tmp_path = f.name

        try:
            text = parser.extract_text(tmp_path)
            assert "张三" in text
            assert "Python" in text
        finally:
            os.unlink(tmp_path)


class TestMarkdownParser:
    """Markdown解析器测试"""

    def test_clean_markdown(self):
        """测试Markdown清理"""
        parser = MarkdownParser()

        md_text = """
# 张三的简历

## 个人信息
- 电话: 13800138000
- 邮箱: zhangsan@example.com

## 技能
- **Python**
- **Django**
- `MySQL`
"""

        cleaned = parser._clean_markdown(md_text)

        assert "# " not in cleaned
        assert "**" not in cleaned
        assert "`" not in cleaned
        assert "张三" in cleaned
        assert "Python" in cleaned


class TestRuleExtractor:
    """规则提取器测试"""

    def test_extract_phone(self):
        """测试手机号提取"""
        extractor = RuleExtractor()

        text = "姓名：张三\n手机：13800138000\n邮箱：test@example.com"
        result = extractor.extract(text)

        assert result["phone"] == "13800138000"

    def test_extract_email(self):
        """测试邮箱提取"""
        extractor = RuleExtractor()

        text = "联系方式：test@example.com"
        result = extractor.extract(text)

        assert result["email"] == "test@example.com"

    def test_extract_skills(self):
        """测试技能提取"""
        extractor = RuleExtractor()

        text = "熟练掌握 Python、Django、MySQL，熟悉 Redis、Docker"
        result = extractor.extract(text)

        assert "Python" in result["skills"]
        assert "Django" in result["skills"]


class TestStrategyGenerator:
    """搜索策略生成器测试"""

    def test_generate_primary_keywords(self):
        """测试主关键词生成"""
        generator = StrategyGenerator()

        profile = {
            "target_positions": ["Python后端"],
            "skills": ["Python", "Django", "MySQL"],
            "experience_years": 3,
        }

        result = generator.generate(profile)

        assert len(result["primary_keywords"]) > 0
        assert "Python后端" in result["primary_keywords"]

    def test_generate_skill_combinations(self):
        """测试技能组合生成"""
        generator = StrategyGenerator()

        profile = {
            "target_positions": ["后端工程师"],
            "skills": ["Python", "Django", "FastAPI"],
        }

        result = generator.generate(profile)

        assert len(result["skill_combinations"]) > 0


class TestTextParser:
    """粘贴文本解析器测试"""

    def test_parse_text(self):
        """测试粘贴文本解析"""
        parser = TextParser()

        text = """
姓名：张三
电话：13800138000
邮箱：zhangsan@example.com

求职意向：Python后端工程师

技能：
- Python
- Django
- MySQL
"""

        result = parser.parse_text(text)

        assert result["success"] == True
        assert result["file_type"] == "paste"

    def test_parse_short_text(self):
        """测试过短文本"""
        parser = TextParser()

        result = parser.parse_text("太短")

        assert result["success"] == False
        assert "太少" in result["error"]


class TestResumeService:
    """ResumeService测试"""

    def test_get_parser(self):
        """测试获取解析器"""
        service = ResumeService()

        pdf_parser = service.get_parser("pdf")
        assert isinstance(pdf_parser, PDFParser)

        txt_parser = service.get_parser("txt")
        assert isinstance(txt_parser, TxtParser)

    def test_file_type_parsers(self):
        """测试支持的文件类型"""
        service = ResumeService()

        assert "pdf" in service.FILE_TYPE_PARSERS
        assert "docx" in service.FILE_TYPE_PARSERS
        assert "md" in service.FILE_TYPE_PARSERS
        assert "txt" in service.FILE_TYPE_PARSERS
        assert "paste" in service.FILE_TYPE_PARSERS