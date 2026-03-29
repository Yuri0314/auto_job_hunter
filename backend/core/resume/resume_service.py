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

    # 保留旧API兼容性方法
    async def parse_resume_file(
        self,
        file_path: str,
        user_id: int = 1,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """解析简历文件（旧API兼容）"""
        return await self.parse_resume(
            file_path=file_path,
            file_type="pdf",
            user_id=user_id,
            use_ai=use_ai,
        )

    def get_resume_status(self, user_id: int = 1) -> Dict[str, Any]:
        """获取简历状态（旧API兼容）"""
        resumes = self.get_resume_list(user_id)
        if not resumes:
            return {
                "has_resume": False,
                "resume_text": None,
                "resume_file": None,
            }

        primary = next((r for r in resumes if r["is_primary"]), resumes[0])
        detail = self.get_resume_detail(primary["id"])

        return {
            "has_resume": True,
            "resume_text": detail["profile"]["name"] if detail and detail["profile"] else None,
            "resume_file": detail["file_path"] if detail else None,
            "parsed": bool(detail and detail["profile"]),
        }

    async def generate_search_keywords(
        self,
        user_id: int = 1,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """生成搜索关键词（旧API兼容）"""
        resumes = self.get_resume_list(user_id)
        if not resumes:
            return {
                "keywords": [],
                "filter_config": {},
                "error": "请先上传并解析简历",
            }

        primary = next((r for r in resumes if r["is_primary"]), resumes[0])
        detail = self.get_resume_detail(primary["id"])

        if not detail or not detail["search_strategy"]:
            return {
                "keywords": [],
                "filter_config": {},
            }

        strategy = detail["search_strategy"]
        keywords = (
            strategy.get("primary_keywords", []) +
            strategy.get("variant_keywords", []) +
            strategy.get("skill_combinations", [])
        )

        return {
            "keywords": keywords[:10],
            "filter_config": {
                "cities": strategy.get("cities", []),
                "salary_range": (
                    detail["profile"]["salary_min"],
                    detail["profile"]["salary_max"],
                ) if detail["profile"] else None,
            },
        }


# 单例
_resume_service: Optional[ResumeService] = None


def get_resume_service() -> ResumeService:
    """获取简历服务单例"""
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService()
    return _resume_service