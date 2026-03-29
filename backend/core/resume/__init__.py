"""简历解析模块"""

from backend.core.resume.parser_base import BaseParser, TextParser
from backend.core.resume.pdf_parser import PDFParser
from backend.core.resume.docx_parser import DocxParser
from backend.core.resume.md_parser import MarkdownParser
from backend.core.resume.txt_parser import TxtParser
from backend.core.resume.rule_extractor import RuleExtractor
from backend.core.resume.ai_extractor import AIExtractor, get_ai_extractor
from backend.core.resume.strategy_generator import StrategyGenerator, get_strategy_generator
from backend.core.resume.resume_service import ResumeService, get_resume_service

# 解析器注册表
PARSERS = {
    "pdf": PDFParser,
    "docx": DocxParser,
    "md": MarkdownParser,
    "txt": TxtParser,
    "paste": TextParser,
}


def get_parser(file_type: str) -> BaseParser:
    """
    根据文件类型获取解析器

    Args:
        file_type: 文件类型 (pdf, docx, md, txt, paste)

    Returns:
        对应的解析器实例

    Raises:
        ValueError: 不支持的文件类型
    """
    parser_class = PARSERS.get(file_type)
    if not parser_class:
        raise ValueError(f"不支持的文件类型: {file_type}")
    return parser_class()


def get_parser_for_file(file_path: str) -> BaseParser:
    """
    根据文件路径自动选择解析器

    Args:
        file_path: 文件路径

    Returns:
        对应的解析器实例

    Raises:
        ValueError: 不支持的文件格式
    """
    from pathlib import Path

    ext = Path(file_path).suffix.lower()
    ext_map = {
        ".pdf": PDFParser,
        ".docx": DocxParser,
        ".doc": DocxParser,
        ".md": MarkdownParser,
        ".markdown": MarkdownParser,
        ".txt": TxtParser,
    }
    parser_class = ext_map.get(ext)
    if not parser_class:
        raise ValueError(f"不支持的文件格式: {ext}")
    return parser_class()


__all__ = [
    "BaseParser",
    "TextParser",
    "PDFParser",
    "DocxParser",
    "MarkdownParser",
    "TxtParser",
    "RuleExtractor",
    "AIExtractor",
    "get_ai_extractor",
    "StrategyGenerator",
    "get_strategy_generator",
    "ResumeService",
    "get_resume_service",
    "get_parser",
    "get_parser_for_file",
    "PARSERS",
]