# 简历解析模块重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构简历解析模块，支持多格式、双引擎解析、结果可编辑、与新数据模型集成

**Architecture:** 定义解析器基类，实现多格式解析器(PDF/Word/MD/TXT)，整合规则引擎和AI引擎，重构 ResumeService

**Tech Stack:** SQLAlchemy, pdfplumber, python-docx, Pydantic, FastAPI

**依赖:** 计划1 - 数据模型扩展

---

## Files Structure

```
backend/core/resume/
├── __init__.py             # 修改: 导出新类
├── parser_base.py          # 新增: 解析器基类
├── pdf_parser.py           # 修改: 继承基类
├── docx_parser.py          # 新增: Word解析器
├── md_parser.py            # 新增: Markdown解析器
├── txt_parser.py           # 新增: 纯文本解析器
├── rule_extractor.py       # 保留: 规则引擎
├── ai_extractor.py         # 新增: AI引擎
├── strategy_generator.py   # 新增: 搜索策略生成器
└── resume_service.py       # 重构: 整合新架构

tests/unit/
└── test_resume_parser.py   # 新增: 解析器测试
```

---

## Task 1: 解析器基类定义

**Files:**
- Create: `backend/core/resume/parser_base.py`

- [ ] **Step 1: 创建解析器基类**

创建文件 `backend/core/resume/parser_base.py`：

```python
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
```

- [ ] **Step 2: 验证基类定义**

```bash
cd /d E:\Code\auto_job_hunter && python -c "from backend.core.resume.parser_base import BaseParser, TextParser; print('Parser base classes imported successfully')"
```

Expected: 输出 "Parser base classes imported successfully"

- [ ] **Step 3: Commit**

```bash
git add backend/core/resume/parser_base.py
git commit -m "feat: 添加简历解析器基类"
```

---

## Task 2: 多格式解析器实现

**Files:**
- Modify: `backend/core/resume/pdf_parser.py`
- Create: `backend/core/resume/docx_parser.py`
- Create: `backend/core/resume/md_parser.py`
- Modify: `backend/core/resume/txt_parser.py` (或从 parser_base.py 分离)

- [ ] **Step 1: 重构 PDFParser 继承基类**

修改 `backend/core/resume/pdf_parser.py`：

```python
"""PDF简历解析器"""

import re
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from .parser_base import BaseParser


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
                raise ImportError(
                    "pdfplumber未安装，请运行: pip install pdfplumber"
                )
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
        """清理提取的文本"""
        if not text:
            return ""

        # 替换特殊空白字符
        text = re.sub(r"[\u00a0\u3000]+", " ", text)

        # 移除行内多余空格
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            line = re.sub(r" +", " ", line)
            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def extract_with_layout(self, file_path: str) -> dict:
        """提取带布局信息的文本"""
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
```

- [ ] **Step 2: 创建 Word 解析器**

创建 `backend/core/resume/docx_parser.py`：

```python
"""Word文档简历解析器"""

from typing import Optional
from pathlib import Path
from loguru import logger

from .parser_base import BaseParser


class DocxParser(BaseParser):
    """Word文档简历解析器"""

    SUPPORTED_EXTENSIONS = [".docx", ".doc"]

    def __init__(self):
        self._docx = None

    def _ensure_docx(self):
        """懒加载python-docx"""
        if self._docx is None:
            try:
                from docx import Document
                self._docx = Document
            except ImportError:
                raise ImportError(
                    "python-docx未安装，请运行: pip install python-docx"
                )
        return self._docx

    def extract_text(self, file_path: str) -> str:
        """
        从Word文档提取文本

        Args:
            file_path: Word文档路径

        Returns:
            提取的文本内容
        """
        Document = self._ensure_docx()

        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"开始解析Word文档: {file_path}")

        try:
            doc = Document(file_path)
            text_parts = []

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    text_parts.append(text)

            # 提取表格中的文本
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_text.append(cell_text)
                    if row_text:
                        text_parts.append(" | ".join(row_text))

            full_text = "\n".join(text_parts)
            logger.info(f"Word解析完成，共提取 {len(full_text)} 个字符")

            return full_text

        except Exception as e:
            logger.error(f"Word解析失败: {e}")
            raise
```

- [ ] **Step 3: 创建 Markdown 解析器**

创建 `backend/core/resume/md_parser.py`：

```python
"""Markdown简历解析器"""

import re
from typing import Optional
from pathlib import Path
from loguru import logger

from .parser_base import BaseParser


class MarkdownParser(BaseParser):
    """Markdown简历解析器"""

    SUPPORTED_EXTENSIONS = [".md", ".markdown"]

    def extract_text(self, file_path: str) -> str:
        """
        从Markdown文件提取文本

        Args:
            file_path: Markdown文件路径

        Returns:
            提取的文本内容（清理Markdown语法）
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"开始解析Markdown: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 清理Markdown语法
            text = self._clean_markdown(content)

            logger.info(f"Markdown解析完成，共提取 {len(text)} 个字符")

            return text

        except Exception as e:
            logger.error(f"Markdown解析失败: {e}")
            raise

    def _clean_markdown(self, text: str) -> str:
        """清理Markdown语法，提取纯文本"""
        # 移除代码块
        text = re.sub(r"```[\s\S]*?```", "", text)

        # 移除行内代码
        text = re.sub(r"`[^`]+`", "", text)

        # 移除链接，保留文字
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # 移除图片
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)

        # 移除标题标记
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # 移除粗体/斜体
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
        text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)

        # 移除列表标记
        text = re.sub(r"^[\*\-\+]\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\d+\.\s*", "", text, flags=re.MULTILINE)

        # 移除水平线
        text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)

        # 清理多余空白
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return text
```

- [ ] **Step 4: 创建 TXT 解析器**

创建 `backend/core/resume/txt_parser.py`：

```python
"""纯文本简历解析器"""

from pathlib import Path
from loguru import logger

from .parser_base import BaseParser


class TxtParser(BaseParser):
    """纯文本简历解析器"""

    SUPPORTED_EXTENSIONS = [".txt"]

    def extract_text(self, file_path: str) -> str:
        """
        从文本文件提取内容

        Args:
            file_path: 文本文件路径

        Returns:
            文本内容
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"开始解析文本文件: {file_path}")

        try:
            # 尝试多种编码
            encodings = ["utf-8", "gbk", "gb2312", "utf-16"]

            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()

                    logger.info(f"文本解析完成，使用编码 {encoding}，共 {len(content)} 个字符")
                    return content

                except UnicodeDecodeError:
                    continue

            raise ValueError("无法识别文件编码")

        except Exception as e:
            logger.error(f"文本解析失败: {e}")
            raise
```

- [ ] **Step 5: 更新 __init__.py 导出**

修改 `backend/core/resume/__init__.py`：

```python
"""简历解析模块"""

from .parser_base import BaseParser, TextParser
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .md_parser import MarkdownParser
from .txt_parser import TxtParser
from .rule_extractor import RuleExtractor
from .resume_service import ResumeService, get_resume_service

# 解析器注册表
PARSERS = {
    "pdf": PDFParser,
    "docx": DocxParser,
    "md": MarkdownParser,
    "txt": TxtParser,
    "paste": TextParser,
}


def get_parser(file_type: str) -> BaseParser:
    """根据文件类型获取解析器"""
    parser_class = PARSERS.get(file_type)
    if not parser_class:
        raise ValueError(f"不支持的文件类型: {file_type}")
    return parser_class()


def get_parser_for_file(file_path: str) -> BaseParser:
    """根据文件路径自动选择解析器"""
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
    "ResumeService",
    "get_resume_service",
    "get_parser",
    "get_parser_for_file",
    "PARSERS",
]
```

- [ ] **Step 6: 验证多格式解析器**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.resume import get_parser, PARSERS
print('Available parsers:', list(PARSERS.keys()))

pdf_parser = get_parser('pdf')
print('PDF parser:', type(pdf_parser).__name__)

docx_parser = get_parser('docx')
print('DOCX parser:', type(docx_parser).__name__)
"
```

Expected: 输出解析器列表和各解析器名称

- [ ] **Step 7: Commit**

```bash
git add backend/core/resume/
git commit -m "feat: 实现多格式简历解析器 (PDF/Word/Markdown/TXT/粘贴文本)"
```

---

## Task 3: AI提取引擎

**Files:**
- Create: `backend/core/resume/ai_extractor.py`

- [ ] **Step 1: 创建AI提取引擎**

创建 `backend/core/resume/ai_extractor.py`：

```python
"""AI简历信息提取引擎"""

from typing import Dict, Any, Optional, List
from loguru import logger
import json


class AIExtractor:
    """基于AI的简历信息提取器"""

    def __init__(self):
        self._ai_service = None

    @property
    def ai_service(self):
        """懒加载AI服务"""
        if self._ai_service is None:
            try:
                from backend.agents.ai import get_ai_service
                self._ai_service = get_ai_service()
            except Exception as e:
                logger.warning(f"AI服务加载失败: {e}")
        return self._ai_service

    async def extract(self, text: str) -> Dict[str, Any]:
        """
        使用AI提取简历信息

        Args:
            text: 简历文本

        Returns:
            提取的信息字典
        """
        if not self.ai_service:
            logger.warning("AI服务不可用")
            return {}

        try:
            prompt = self._build_extraction_prompt(text)
            response = await self.ai_service.chat(prompt)

            result = self._parse_response(response)

            logger.info(f"AI提取完成，提取了 {len([v for v in result.values() if v])} 个字段")

            return result

        except Exception as e:
            logger.error(f"AI提取失败: {e}")
            return {}

    def _build_extraction_prompt(self, text: str) -> str:
        """构建提取提示词"""
        return f"""请从以下简历文本中提取关键信息，以JSON格式返回。

简历文本:
{text[:3000]}

请提取以下字段（如果存在）:
- name: 姓名
- phone: 手机号
- email: 邮箱
- gender: 性别
- age: 年龄（数字）
- experience_years: 工作年限（数字）
- education: 学历
- school: 毕业院校
- major: 专业
- current_position: 当前职位
- current_company: 当前公司
- target_positions: 目标职位列表（数组）
- preferred_cities: 意向城市列表（数组）
- salary_min: 期望薪资下限（数字，单位K）
- salary_max: 期望薪资上限（数字，单位K）
- skills: 技能列表（数组，最多10个核心技能）
- work_experiences: 工作经历列表（数组，每项包含company/position/duration）

只返回JSON，不要其他解释。如果某个字段无法提取，返回null。"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except json.JSONDecodeError:
            logger.warning("AI响应不是有效的JSON")
            return {}

    async def generate_search_suggestions(
        self,
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据用户画像生成搜索建议

        Args:
            profile: 用户画像

        Returns:
            {
                "primary_keywords": ["Python后端", ...],
                "variant_keywords": ["Django开发", ...],
                "skill_combinations": ["Python Django", ...],
                "suggestions": "综合建议"
            }
        """
        if not self.ai_service:
            return {}

        try:
            prompt = f"""根据以下用户画像，生成职位搜索关键词建议。

用户画像:
- 目标职位: {profile.get('target_positions', [])}
- 核心技能: {profile.get('skills', [])[:5]}
- 工作年限: {profile.get('experience_years')}
- 期望薪资: {profile.get('salary_min')}-{profile.get('salary_max')}K

请生成:
1. primary_keywords: 3-5个核心搜索关键词
2. variant_keywords: 3-5个变体关键词（同义词、相关词）
3. skill_combinations: 3-5个技能组合关键词
4. suggestions: 一段简短的搜索策略建议

以JSON格式返回。"""

            response = await self.ai_service.chat(prompt)
            result = self._parse_response(response)

            return result

        except Exception as e:
            logger.error(f"生成搜索建议失败: {e}")
            return {}


# 单例
_ai_extractor: Optional[AIExtractor] = None


def get_ai_extractor() -> AIExtractor:
    """获取AI提取器单例"""
    global _ai_extractor
    if _ai_extractor is None:
        _ai_extractor = AIExtractor()
    return _ai_extractor
```

- [ ] **Step 2: 验证AI提取器**

```bash
cd /d E:\Code\auto_job_hunter && python -c "from backend.core.resume.ai_extractor import AIExtractor; print('AIExtractor imported successfully')"
```

Expected: 输出 "AIExtractor imported successfully"

- [ ] **Step 3: Commit**

```bash
git add backend/core/resume/ai_extractor.py
git commit -m "feat: 添加AI简历信息提取引擎"
```

---

## Task 4: 搜索策略生成器

**Files:**
- Create: `backend/core/resume/strategy_generator.py`

- [ ] **Step 1: 创建搜索策略生成器**

创建 `backend/core/resume/strategy_generator.py`：

```python
"""搜索策略生成器"""

from typing import Dict, Any, List, Optional
from loguru import logger


class StrategyGenerator:
    """根据简历生成搜索策略"""

    # 职位关键词映射
    POSITION_VARIANTS = {
        "后端": ["后端开发", "后端工程师", "服务端开发", "Server开发", "Backend Engineer"],
        "前端": ["前端开发", "前端工程师", "Web开发", "Frontend Engineer"],
        "全栈": ["全栈开发", "全栈工程师", "Full Stack", "前后端开发"],
        "Java开发": ["Java工程师", "Java后端", "Java开发工程师"],
        "Python开发": ["Python工程师", "Python后端", "Python开发工程师"],
        "数据分析师": ["数据分析", "Data Analyst", "数据运营"],
        "算法工程师": ["算法开发", "算法", "AI工程师", "Machine Learning Engineer"],
        "测试工程师": ["测试开发", "QA工程师", "软件测试"],
        "运维工程师": ["DevOps", "SRE", "系统运维", "运维开发"],
        "产品经理": ["产品", "PM", "Product Manager"],
    }

    # 技能关键词映射
    SKILL_KEYWORDS = {
        "Python": ["Python", "Python开发", "Python工程师"],
        "Java": ["Java", "Java开发", "Java工程师"],
        "Go": ["Go", "Golang", "Go开发"],
        "JavaScript": ["JavaScript", "JS", "前端"],
        "TypeScript": ["TypeScript", "TS", "前端"],
        "Vue": ["Vue", "Vue.js", "Vue开发", "前端"],
        "React": ["React", "React.js", "React开发", "前端"],
        "Django": ["Django", "Python Django"],
        "FastAPI": ["FastAPI", "Python FastAPI"],
        "Spring": ["Spring", "SpringBoot", "Java Spring"],
        "MySQL": ["MySQL", "数据库"],
        "Redis": ["Redis", "缓存"],
        "Docker": ["Docker", "容器", "云原生"],
        "Kubernetes": ["Kubernetes", "K8s", "容器编排"],
    }

    def generate(
        self,
        profile: Dict[str, Any],
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        生成搜索策略

        Args:
            profile: 用户画像
            use_ai: 是否使用AI生成

        Returns:
            {
                "primary_keywords": [...],
                "variant_keywords": [...],
                "skill_combinations": [...],
                "cities": [...],
                "salary_range": (min, max),
            }
        """
        logger.info("开始生成搜索策略")

        result = {
            "primary_keywords": self._generate_primary_keywords(profile),
            "variant_keywords": self._generate_variant_keywords(profile),
            "skill_combinations": self._generate_skill_combinations(profile),
            "cities": profile.get("preferred_cities", []) or [profile.get("city")] if profile.get("city") else [],
            "salary_min": profile.get("salary_min"),
            "salary_max": profile.get("salary_max"),
        }

        # 过滤空值
        result["cities"] = [c for c in result["cities"] if c]

        logger.info(f"搜索策略生成完成: 主关键词 {len(result['primary_keywords'])} 个")

        return result

    def _generate_primary_keywords(self, profile: Dict[str, Any]) -> List[str]:
        """生成核心搜索关键词"""
        keywords = []

        # 从目标职位提取
        target_positions = profile.get("target_positions", [])
        for position in target_positions[:3]:
            keywords.append(position)
            # 添加职位变体
            for key, variants in self.POSITION_VARIANTS.items():
                if key in position:
                    keywords.extend(variants[:2])
                    break

        # 从当前职位推断
        if not keywords and profile.get("current_position"):
            keywords.append(profile["current_position"])

        # 去重
        seen = set()
        unique = []
        for k in keywords:
            if k and k not in seen:
                seen.add(k)
                unique.append(k)

        return unique[:5]

    def _generate_variant_keywords(self, profile: Dict[str, Any]) -> List[str]:
        """生成变体关键词"""
        variants = []

        target_positions = profile.get("target_positions", [])
        for position in target_positions:
            for key, position_variants in self.POSITION_VARIANTS.items():
                if key in position:
                    variants.extend(position_variants)
                    break

        # 去重，排除已存在的主关键词
        primary = set(self._generate_primary_keywords(profile))
        seen = set()
        unique = []
        for v in variants:
            if v and v not in seen and v not in primary:
                seen.add(v)
                unique.append(v)

        return unique[:5]

    def _generate_skill_combinations(self, profile: Dict[str, Any]) -> List[str]:
        """生成技能组合关键词"""
        skills = profile.get("skills", [])
        if not skills:
            return []

        combinations = []

        # 核心技能单独作为关键词
        for skill in skills[:3]:
            if skill in self.SKILL_KEYWORDS:
                combinations.extend(self.SKILL_KEYWORDS[skill][:2])

        # 技能 + 职位 组合
        target_positions = profile.get("target_positions", [])
        if target_positions and skills:
            position = target_positions[0]
            core_skill = skills[0]
            combinations.append(f"{core_skill}{position}")

        # 技能组合
        if len(skills) >= 2:
            combinations.append(f"{skills[0]} {skills[1]}")

        # 去重
        seen = set()
        unique = []
        for c in combinations:
            if c and c not in seen:
                seen.add(c)
                unique.append(c)

        return unique[:5]

    async def generate_with_ai(
        self,
        profile: Dict[str, Any],
        ai_extractor,
    ) -> Dict[str, Any]:
        """使用AI生成搜索策略"""
        # 先用规则生成基础策略
        base_strategy = self.generate(profile, use_ai=False)

        # 使用AI增强
        try:
            ai_result = await ai_extractor.generate_search_suggestions(profile)

            if ai_result:
                # 合并AI建议
                if ai_result.get("primary_keywords"):
                    # 去重合并
                    all_primary = list(set(
                        base_strategy["primary_keywords"] +
                        ai_result["primary_keywords"]
                    ))
                    base_strategy["primary_keywords"] = all_primary[:5]

                if ai_result.get("variant_keywords"):
                    all_variants = list(set(
                        base_strategy["variant_keywords"] +
                        ai_result["variant_keywords"]
                    ))
                    base_strategy["variant_keywords"] = all_variants[:5]

                if ai_result.get("skill_combinations"):
                    all_combos = list(set(
                        base_strategy["skill_combinations"] +
                        ai_result["skill_combinations"]
                    ))
                    base_strategy["skill_combinations"] = all_combos[:5]

        except Exception as e:
            logger.warning(f"AI增强搜索策略失败: {e}")

        return base_strategy


# 单例
_strategy_generator: Optional[StrategyGenerator] = None


def get_strategy_generator() -> StrategyGenerator:
    """获取策略生成器单例"""
    global _strategy_generator
    if _strategy_generator is None:
        _strategy_generator = StrategyGenerator()
    return _strategy_generator
```

- [ ] **Step 2: 验证策略生成器**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.resume.strategy_generator import StrategyGenerator

gen = StrategyGenerator()
profile = {
    'target_positions': ['Python后端'],
    'skills': ['Python', 'Django', 'MySQL'],
    'experience_years': 3,
    'preferred_cities': ['北京'],
}
result = gen.generate(profile)
print('Primary:', result['primary_keywords'])
print('Variants:', result['variant_keywords'])
print('Combinations:', result['skill_combinations'])
"
```

Expected: 输出生成的关键词列表

- [ ] **Step 3: Commit**

```bash
git add backend/core/resume/strategy_generator.py
git commit -m "feat: 添加搜索策略生成器"
```

---

## Task 5: 重构 ResumeService

**Files:**
- Modify: `backend/core/resume/resume_service.py`

- [ ] **Step 1: 重构 ResumeService 整合新架构**

修改 `backend/core/resume/resume_service.py`：

```python
"""简历解析服务 - 协调层"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from backend.core.database import (
    SessionLocal,
    Resume,
    ResumeProfile,
    SearchStrategy,
    UserProfile,
)
from .parser_base import TextParser
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .md_parser import MarkdownParser
from .txt_parser import TxtParser
from .rule_extractor import RuleExtractor
from .ai_extractor import AIExtractor, get_ai_extractor
from .strategy_generator import StrategyGenerator, get_strategy_generator


class ResumeService:
    """简历解析服务"""

    # 文件类型映射
    FILE_TYPE_PARSERS = {
        "pdf": PDFParser,
        "docx": DocxParser,
        "md": MarkdownParser,
        "txt": TxtParser,
        "paste": TextParser,
    }

    def __init__(self):
        self._rule_extractor = RuleExtractor()
        self._ai_extractor: Optional[AIExtractor] = None
        self._strategy_generator: Optional[StrategyGenerator] = None

    @property
    def ai_extractor(self) -> AIExtractor:
        """懒加载AI提取器"""
        if self._ai_extractor is None:
            self._ai_extractor = get_ai_extractor()
        return self._ai_extractor

    @property
    def strategy_generator(self) -> StrategyGenerator:
        """懒加载策略生成器"""
        if self._strategy_generator is None:
            self._strategy_generator = get_strategy_generator()
        return self._strategy_generator

    def get_parser(self, file_type: str):
        """获取解析器"""
        parser_class = self.FILE_TYPE_PARSERS.get(file_type)
        if not parser_class:
            raise ValueError(f"不支持的文件类型: {file_type}")
        return parser_class()

    async def parse_resume(
        self,
        file_path: str,
        file_type: str = "pdf",
        user_id: int = 1,
        use_ai: bool = False,
        resume_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        解析简历文件

        Args:
            file_path: 文件路径（或粘贴的文本，当file_type="paste"时）
            file_type: 文件类型 (pdf/docx/md/txt/paste)
            user_id: 用户ID
            use_ai: 是否使用AI模式
            resume_name: 简历名称（可选）

        Returns:
            {
                "success": bool,
                "resume_id": int,
                "profile_id": int,
                "extracted_data": dict,
                "search_strategy": dict,
                "error": str (if failed)
            }
        """
        try:
            logger.info(f"开始解析简历: file_type={file_type}, use_ai={use_ai}")

            # 1. 提取文本
            parser = self.get_parser(file_type)

            if file_type == "paste":
                parse_result = parser.parse_text(file_path)
            else:
                parse_result = parser.parse(file_path)

            if not parse_result.get("success"):
                return parse_result

            text = parse_result["text"]

            # 2. 信息提取
            if use_ai:
                extracted_data = await self._extract_with_ai(text)
            else:
                extracted_data = self._rule_extractor.extract(text)

            # 3. 保存到数据库
            resume, profile = self._save_to_database(
                user_id=user_id,
                file_path=file_path if file_type != "paste" else None,
                file_type=file_type,
                parse_engine="ai" if use_ai else "rule",
                extracted_data=extracted_data,
                raw_text=text,
                resume_name=resume_name,
            )

            # 4. 生成搜索策略
            strategy = self._generate_and_save_strategy(
                resume_id=resume.id,
                profile_data=extracted_data,
                use_ai=use_ai,
            )

            logger.info(f"简历解析成功: resume_id={resume.id}")

            return {
                "success": True,
                "resume_id": resume.id,
                "profile_id": profile.id,
                "extracted_data": extracted_data,
                "search_strategy": strategy,
                "file_type": file_type,
            }

        except Exception as e:
            logger.error(f"简历解析失败: {e}")
            return {"success": False, "error": str(e)}

    async def _extract_with_ai(self, text: str) -> Dict[str, Any]:
        """使用AI提取简历信息"""
        if not self.ai_extractor.ai_service:
            logger.warning("AI服务不可用，回退到规则模式")
            return self._rule_extractor.extract(text)

        try:
            ai_result = await self.ai_extractor.extract(text)

            # 合并规则提取结果（作为补充）
            rule_result = self._rule_extractor.extract(text)

            # AI结果优先，规则结果补充
            merged = rule_result.copy()
            for key, value in ai_result.items():
                if value is not None:
                    merged[key] = value

            return merged

        except Exception as e:
            logger.error(f"AI提取失败: {e}，回退到规则模式")
            return self._rule_extractor.extract(text)

    def _save_to_database(
        self,
        user_id: int,
        file_path: Optional[str],
        file_type: str,
        parse_engine: str,
        extracted_data: Dict[str, Any],
        raw_text: str,
        resume_name: Optional[str] = None,
    ) -> tuple:
        """保存简历到数据库"""
        db = SessionLocal()
        try:
            # 创建简历记录
            name = resume_name or extracted_data.get("name", "未命名简历")
            if file_path and not resume_name:
                from pathlib import Path
                name = Path(file_path).stem

            resume = Resume(
                user_id=user_id,
                name=name,
                file_path=file_path,
                file_type=file_type,
                parse_engine=parse_engine,
                is_primary=False,
            )
            db.add(resume)
            db.flush()  # 获取ID

            # 创建简历画像
            profile = ResumeProfile(
                resume_id=resume.id,
                name=extracted_data.get("name"),
                phone=extracted_data.get("phone"),
                email=extracted_data.get("email"),
                gender=extracted_data.get("gender"),
                age=extracted_data.get("age"),
                experience_years=extracted_data.get("experience_years"),
                current_position=extracted_data.get("current_position"),
                current_company=extracted_data.get("current_company"),
                target_positions=extracted_data.get("target_positions"),
                preferred_cities=extracted_data.get("target_cities") or extracted_data.get("preferred_cities"),
                salary_min=extracted_data.get("expected_salary_min") or extracted_data.get("salary_min"),
                salary_max=extracted_data.get("expected_salary_max") or extracted_data.get("salary_max"),
                education=extracted_data.get("education"),
                school=extracted_data.get("school"),
                major=extracted_data.get("major"),
                skills=extracted_data.get("skills"),
                work_experiences=extracted_data.get("work_experiences"),
                raw_text=raw_text[:10000] if raw_text else None,  # 限制长度
            )
            db.add(profile)
            db.commit()

            return resume, profile

        except Exception as e:
            logger.error(f"保存简历失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def _generate_and_save_strategy(
        self,
        resume_id: int,
        profile_data: Dict[str, Any],
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """生成并保存搜索策略"""
        strategy_data = self.strategy_generator.generate(profile_data, use_ai=use_ai)

        db = SessionLocal()
        try:
            strategy = SearchStrategy(
                resume_id=resume_id,
                primary_keywords=strategy_data.get("primary_keywords", []),
                variant_keywords=strategy_data.get("variant_keywords", []),
                skill_combinations=strategy_data.get("skill_combinations", []),
                cities=strategy_data.get("cities", []),
                salary_min=strategy_data.get("salary_min"),
                salary_max=strategy_data.get("salary_max"),
            )
            db.add(strategy)
            db.commit()

            strategy_data["strategy_id"] = strategy.id

        except Exception as e:
            logger.warning(f"保存搜索策略失败: {e}")
        finally:
            db.close()

        return strategy_data

    def get_resume_list(self, user_id: int = 1) -> List[Dict[str, Any]]:
        """获取用户的简历列表"""
        db = SessionLocal()
        try:
            resumes = db.query(Resume).filter(
                Resume.user_id == user_id
            ).order_by(Resume.updated_at.desc()).all()

            result = []
            for resume in resumes:
                profile = db.query(ResumeProfile).filter(
                    ResumeProfile.resume_id == resume.id
                ).first()

                result.append({
                    "id": resume.id,
                    "name": resume.name,
                    "file_type": resume.file_type,
                    "parse_engine": resume.parse_engine,
                    "is_primary": resume.is_primary,
                    "created_at": resume.created_at.isoformat() if resume.created_at else None,
                    "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
                    "profile": {
                        "name": profile.name if profile else None,
                        "experience_years": profile.experience_years if profile else None,
                        "current_position": profile.current_position if profile else None,
                        "skills": profile.skills if profile else [],
                    } if profile else None,
                })

            return result

        finally:
            db.close()

    def get_resume_detail(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """获取简历详情"""
        db = SessionLocal()
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                return None

            profile = db.query(ResumeProfile).filter(
                ResumeProfile.resume_id == resume_id
            ).first()

            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.resume_id == resume_id
            ).first()

            return {
                "id": resume.id,
                "name": resume.name,
                "file_type": resume.file_type,
                "file_path": resume.file_path,
                "parse_engine": resume.parse_engine,
                "is_primary": resume.is_primary,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
                "profile": {
                    "name": profile.name,
                    "phone": profile.phone,
                    "email": profile.email,
                    "experience_years": profile.experience_years,
                    "current_position": profile.current_position,
                    "target_positions": profile.target_positions,
                    "preferred_cities": profile.preferred_cities,
                    "salary_min": profile.salary_min,
                    "salary_max": profile.salary_max,
                    "education": profile.education,
                    "school": profile.school,
                    "skills": profile.skills,
                } if profile else None,
                "search_strategy": {
                    "primary_keywords": strategy.primary_keywords,
                    "variant_keywords": strategy.variant_keywords,
                    "skill_combinations": strategy.skill_combinations,
                    "cities": strategy.cities,
                } if strategy else None,
            }

        finally:
            db.close()

    def update_resume_profile(
        self,
        resume_id: int,
        profile_data: Dict[str, Any],
    ) -> bool:
        """更新简历画像"""
        db = SessionLocal()
        try:
            profile = db.query(ResumeProfile).filter(
                ResumeProfile.resume_id == resume_id
            ).first()

            if not profile:
                profile = ResumeProfile(resume_id=resume_id)
                db.add(profile)

            # 更新字段
            updatable_fields = [
                "name", "phone", "email", "experience_years",
                "current_position", "target_positions", "preferred_cities",
                "salary_min", "salary_max", "education", "school",
                "major", "skills", "work_experiences",
            ]

            for field in updatable_fields:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])

            db.commit()
            return True

        except Exception as e:
            logger.error(f"更新简历画像失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()


# 单例
_resume_service: Optional[ResumeService] = None


def get_resume_service() -> ResumeService:
    """获取简历服务单例"""
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService()
    return _resume_service
```

- [ ] **Step 2: 验证 ResumeService 重构**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.resume import ResumeService, get_resume_service
service = get_resume_service()
print('ResumeService initialized')
print('Available file types:', list(service.FILE_TYPE_PARSERS.keys()))
"
```

Expected: 输出初始化信息和文件类型列表

- [ ] **Step 3: Commit**

```bash
git add backend/core/resume/resume_service.py
git commit -m "refactor: 重构ResumeService，支持多格式解析、双引擎提取、搜索策略生成"
```

---

## Task 6: 更新 API 端点

**Files:**
- Modify: `backend/api/resume.py`

- [ ] **Step 1: 更新上传API支持多格式**

修改 `backend/api/resume.py` 中的 `upload_and_parse_resume` 函数：

```python
@router.post("/upload", response_model=ParseResultResponse)
async def upload_and_parse_resume(
    file: UploadFile = File(...),
    use_ai: bool = Query(False, description="是否使用AI模式提取信息"),
    user_id: int = 1,
):
    """
    上传并解析简历

    支持 PDF、Word(.docx)、Markdown(.md)、纯文本(.txt) 格式
    """
    import tempfile
    import os

    # 检查文件类型
    filename = file.filename.lower()
    supported_extensions = [".pdf", ".docx", ".doc", ".md", ".markdown", ".txt"]

    ext = os.path.splitext(filename)[1]
    if ext not in supported_extensions:
        raise HTTPException(
            400,
            f"不支持的文件格式: {ext}。支持的格式: {', '.join(supported_extensions)}"
        )

    # 确定文件类型
    file_type_map = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".md": "md",
        ".markdown": "md",
        ".txt": "txt",
    }
    file_type = file_type_map.get(ext, "txt")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 解析简历
        service = get_resume_service()
        result = await service.parse_resume(
            file_path=tmp_path,
            file_type=file_type,
            user_id=user_id,
            use_ai=use_ai,
        )

        return result

    except Exception as e:
        logger.error(f"Upload resume error: {e}")
        raise HTTPException(500, f"简历解析失败: {str(e)}")
```

- [ ] **Step 2: 添加粘贴文本解析API**

在 `backend/api/resume.py` 中添加：

```python
class ParseTextRequest(BaseModel):
    """粘贴文本解析请求"""
    text: str
    use_ai: bool = False


@router.post("/parse-text")
async def parse_pasted_text(
    request: ParseTextRequest,
    user_id: int = 1,
):
    """
    解析粘贴的简历文本

    用户可以直接粘贴简历内容进行解析
    """
    if len(request.text) < 50:
        raise HTTPException(400, "文本内容太少，请提供完整的简历信息")

    try:
        service = get_resume_service()
        result = await service.parse_resume(
            file_path=request.text,
            file_type="paste",
            user_id=user_id,
            use_ai=request.use_ai,
        )

        return result

    except Exception as e:
        logger.error(f"Parse text error: {e}")
        raise HTTPException(500, f"解析失败: {str(e)}")
```

- [ ] **Step 3: 添加获取简历详情API**

```python
@router.get("/{resume_id}")
async def get_resume_detail(
    resume_id: int,
):
    """获取简历详情"""
    service = get_resume_service()
    detail = service.get_resume_detail(resume_id)

    if not detail:
        raise HTTPException(404, "简历不存在")

    return detail
```

- [ ] **Step 4: 添加更新简历画像API**

```python
class UpdateProfileRequest(BaseModel):
    """更新画像请求"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    experience_years: Optional[int] = None
    current_position: Optional[str] = None
    target_positions: Optional[List[str]] = None
    preferred_cities: Optional[List[str]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    education: Optional[str] = None
    school: Optional[str] = None
    skills: Optional[List[str]] = None


@router.put("/{resume_id}/profile")
async def update_resume_profile(
    resume_id: int,
    request: UpdateProfileRequest,
):
    """更新简历画像（用户编辑修正）"""
    service = get_resume_service()

    success = service.update_resume_profile(
        resume_id=resume_id,
        profile_data=request.dict(exclude_unset=True),
    )

    if not success:
        raise HTTPException(500, "更新失败")

    return {"success": True, "message": "简历画像已更新"}
```

- [ ] **Step 5: 测试API**

```bash
cd /d E:\Code\auto_job_hunter && python run.py web &
```

测试多格式上传和粘贴文本解析。

- [ ] **Step 6: Commit**

```bash
git add backend/api/resume.py
git commit -m "feat: 更新简历API支持多格式上传、粘贴文本解析、画像编辑"
```

---

## Task 7: 单元测试

**Files:**
- Create: `tests/unit/test_resume_parser.py`

- [ ] **Step 1: 创建解析器测试**

创建 `tests/unit/test_resume_parser.py`：

```python
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
```

- [ ] **Step 2: 运行测试**

```bash
cd /d E:\Code\auto_job_hunter && pytest tests/unit/test_resume_parser.py -v
```

Expected: 所有测试通过

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_resume_parser.py
git commit -m "test: 添加简历解析器单元测试"
```

---

## Verification

- [ ] **运行所有测试**

```bash
cd /d E:\Code\auto_job_hunter && pytest tests/unit/ -v
```

Expected: 所有测试通过

- [ ] **测试多格式解析**

```bash
cd /d E:\Code\auto_job_hunter && python -c "
from backend.core.resume import get_resume_service

service = get_resume_service()
print('Service initialized')

# 测试支持的格式
print('Supported formats:', list(service.FILE_TYPE_PARSERS.keys()))
"
```

---

## Summary

完成本计划后：

1. **多格式支持**: PDF, Word(.docx), Markdown(.md), 纯文本(.txt), 粘贴文本
2. **双引擎解析**: 规则引擎(默认) + AI引擎(可选)
3. **解析结果可编辑**: 通过 API 更新简历画像
4. **搜索策略生成**: 自动生成关键词组合
5. **与新数据模型集成**: Resume, ResumeProfile, SearchStrategy

这些改动为后续的多简历管理和仪表盘提供了核心功能支持。