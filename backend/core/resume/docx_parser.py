"""Word文档简历解析器"""

import re
from typing import Dict, Any
from loguru import logger

from backend.core.resume.parser_base import BaseParser


class DocxParser(BaseParser):
    """Word文档简历文本提取器"""

    SUPPORTED_EXTENSIONS = [".docx", ".doc"]

    def __init__(self):
        self._docx = None

    def _ensure_docx(self):
        """懒加载python-docx"""
        if self._docx is None:
            try:
                import docx

                self._docx = docx
            except ImportError:
                raise ImportError("python-docx未安装，请运行: pip install python-docx")
        return self._docx

    def extract_text(self, file_path: str) -> str:
        """
        从Word文档提取文本

        Args:
            file_path: Word文档路径

        Returns:
            提取的文本内容
        """
        docx = self._ensure_docx()

        logger.info(f"开始解析Word文档: {file_path}")

        text_parts = []

        try:
            doc = docx.Document(file_path)

            # 提取段落文本
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    text_parts.append(text)

            # 提取表格文本
            for table in doc.tables:
                table_text = self._extract_table_text(table)
                if table_text:
                    text_parts.append(table_text)

        except Exception as e:
            logger.error(f"Word文档解析失败: {e}")
            raise

        full_text = "\n\n".join(text_parts)
        logger.info(f"Word文档解析完成，共提取 {len(full_text)} 个字符")

        return full_text

    def _extract_table_text(self, table) -> str:
        """
        从表格中提取文本

        Args:
            table: docx表格对象

        Returns:
            表格文本
        """
        rows_text = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            cells = [c for c in cells if c]  # 过滤空单元格
            if cells:
                rows_text.append(" | ".join(cells))

        return "\n".join(rows_text)