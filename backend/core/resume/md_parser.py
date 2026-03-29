"""Markdown简历解析器"""

import re
from typing import Dict, Any
from loguru import logger

from backend.core.resume.parser_base import BaseParser


class MarkdownParser(BaseParser):
    """Markdown简历文本提取器"""

    SUPPORTED_EXTENSIONS = [".md", ".markdown"]

    def extract_text(self, file_path: str) -> str:
        """
        从Markdown文件提取纯文本

        Args:
            file_path: Markdown文件路径

        Returns:
            提取的纯文本内容
        """
        logger.info(f"开始解析Markdown: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 清理Markdown语法
            text = self._clean_markdown(content)

            logger.info(f"Markdown解析完成，共提取 {len(text)} 个字符")

            return text

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, "r", encoding="gbk") as f:
                    content = f.read()
                text = self._clean_markdown(content)
                return text
            except Exception as e:
                logger.error(f"Markdown解析失败: {e}")
                raise

        except Exception as e:
            logger.error(f"Markdown解析失败: {e}")
            raise

    def _clean_markdown(self, content: str) -> str:
        """
        清理Markdown语法，提取纯文本

        Args:
            content: Markdown内容

        Returns:
            纯文本
        """
        if not content:
            return ""

        text = content

        # 移除代码块
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # 移除图片
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)

        # 移除链接，保留文本
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # 移除标题标记
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # 移除粗体和斜体标记
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # 移除水平线
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # 移除列表标记
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # 移除HTML标签
        text = re.sub(r"<[^>]+>", "", text)

        # 清理多余空白
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)