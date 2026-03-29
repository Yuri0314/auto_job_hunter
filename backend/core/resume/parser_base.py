"""简历解析器基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger


class BaseParser(ABC):
    """简历解析器基类"""

    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = []

    @classmethod
    def can_parse(cls, file_path: str) -> bool:
        """检查是否可以解析该文件"""
        ext = Path(file_path).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        从文件提取文本

        Args:
            file_path: 文件路径

        Returns:
            提取的文本内容
        """
        pass

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析简历文件

        Args:
            file_path: 文件路径

        Returns:
            {
                "success": bool,
                "text": str,
                "file_type": str,
                "error": str (if failed)
            }
        """
        try:
            if not Path(file_path).exists():
                return {
                    "success": False,
                    "error": f"文件不存在: {file_path}",
                }

            text = self.extract_text(file_path)

            if not text or len(text) < 50:
                return {
                    "success": False,
                    "error": "无法从文件中提取有效文本",
                }

            return {
                "success": True,
                "text": text,
                "file_type": self._get_file_type(file_path),
            }

        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            ".pdf": "pdf",
            ".docx": "docx",
            ".doc": "docx",
            ".md": "md",
            ".markdown": "md",
            ".txt": "txt",
        }
        return type_map.get(ext, "unknown")


class TextParser(BaseParser):
    """纯文本解析器（支持直接粘贴的文本）"""

    SUPPORTED_EXTENSIONS = [".txt"]

    def extract_text(self, text: str) -> str:
        """直接返回文本"""
        return text

    def parse_text(self, text: str) -> Dict[str, Any]:
        """解析粘贴的文本"""
        if not text or len(text) < 50:
            return {
                "success": False,
                "error": "文本内容太少",
            }

        return {
            "success": True,
            "text": text,
            "file_type": "paste",
        }