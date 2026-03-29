"""PDF简历解析器"""

import re
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from backend.core.resume.parser_base import BaseParser


class PDFParser(BaseParser):
    """PDF简历文本提取器"""

    SUPPORTED_EXTENSIONS = [".pdf"]

    def __init__(self):
        self._pdfplumber = None

    def _ensure_pdfplumber(self):
        """懒加载pdfplumber"""
        if self._pdfplumber is None:
            try:
                import pdfplumber

                self._pdfplumber = pdfplumber
            except ImportError:
                raise ImportError("pdfplumber未安装，请运行: pip install pdfplumber")
        return self._pdfplumber

    def extract_text(self, file_path: str) -> str:
        """
        从PDF文件提取文本

        Args:
            file_path: PDF文件路径

        Returns:
            提取的文本内容
        """
        pdfplumber = self._ensure_pdfplumber()

        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"开始解析PDF: {file_path}")

        text_parts = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # 清理文本
                            page_text = self._clean_text(page_text)
                            text_parts.append(page_text)
                            logger.debug(f"第{i+1}页提取了 {len(page_text)} 个字符")
                    except Exception as e:
                        logger.warning(f"第{i+1}页提取失败: {e}")
                        continue

        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            raise

        full_text = "\n\n".join(text_parts)
        logger.info(f"PDF解析完成，共提取 {len(full_text)} 个字符")

        return full_text

    def _clean_text(self, text: str) -> str:
        """
        清理提取的文本

        - 移除多余的空白
        - 保留有意义的换行
        - 处理特殊字符
        """
        if not text:
            return ""

        # 替换特殊空白字符
        text = re.sub(r"[\u00a0\u3000]+", " ", text)

        # 移除行内多余空格（保留必要的空格）
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # 移除行首行尾空格
            line = line.strip()
            # 压缩多个空格为一个
            line = re.sub(r" +", " ", line)
            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def extract_with_layout(self, file_path: str) -> dict:
        """
        提取带布局信息的文本

        Returns:
            {
                "text": "完整文本",
                "pages": [
                    {"page_num": 1, "text": "页面文本", "width": 600, "height": 800}
                ]
            }
        """
        pdfplumber = self._ensure_pdfplumber()

        result = {
            "text": "",
            "pages": [],
        }

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                page_text = self._clean_text(page_text)

                result["pages"].append({
                    "page_num": i + 1,
                    "text": page_text,
                    "width": page.width,
                    "height": page.height,
                })

        result["text"] = "\n\n".join(p["text"] for p in result["pages"])
        return result