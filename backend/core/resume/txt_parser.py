"""纯文本简历解析器"""

from typing import Dict, Any
from loguru import logger

from backend.core.resume.parser_base import BaseParser


class TxtParser(BaseParser):
    """纯文本简历解析器"""

    SUPPORTED_EXTENSIONS = [".txt"]

    # 支持的编码列表（按优先级排序）
    ENCODINGS = ["utf-8", "gbk", "gb2312", "utf-16"]

    def extract_text(self, file_path: str) -> str:
        """
        从纯文本文件提取内容

        Args:
            file_path: 文本文件路径

        Returns:
            文本内容
        """
        logger.info(f"开始解析文本文件: {file_path}")

        # 尝试不同编码
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()

                # 清理文本
                text = self._clean_text(content)

                logger.info(
                    f"文本文件解析完成 (编码: {encoding})，共提取 {len(text)} 个字符"
                )

                return text

            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"使用 {encoding} 编码读取失败: {e}")
                continue

        # 所有编码都失败
        raise UnicodeDecodeError(
            "utf-8",
            b"",
            0,
            1,
            f"无法解码文件，尝试了以下编码: {', '.join(self.ENCODINGS)}",
        )

    def _clean_text(self, text: str) -> str:
        """
        清理文本内容

        - 移除BOM标记
        - 规范化换行符
        - 移除多余空白行
        """
        if not text:
            return ""

        # 移除BOM标记
        if text.startswith("\ufeff"):
            text = text[1:]

        # 规范化换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 移除多余空白行（保留段落间的空行）
        lines = text.split("\n")
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            is_empty = not line.strip()

            # 跳过连续的空行
            if is_empty and prev_empty:
                continue

            cleaned_lines.append(line)
            prev_empty = is_empty

        # 移除首尾空白行
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)