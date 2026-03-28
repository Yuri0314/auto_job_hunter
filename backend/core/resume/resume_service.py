"""简历解析服务 - 协调层"""

from typing import Dict, Any, Optional
from loguru import logger

from backend.core.resume.pdf_parser import PDFParser
from backend.core.resume.rule_extractor import RuleExtractor
from backend.core.database import SessionLocal, UserProfile


class ResumeService:
    """简历解析服务"""

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.rule_extractor = RuleExtractor()
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

    async def parse_resume_file(
        self,
        file_path: str,
        user_id: int = 1,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        解析简历文件

        Args:
            file_path: 简历文件路径
            user_id: 用户ID
            use_ai: 是否使用AI模式

        Returns:
            {
                "success": bool,
                "extracted_data": dict,
                "resume_text": str,
                "error": str (if failed)
            }
        """
        try:
            # 1. PDF提取文本
            logger.info(f"开始解析简历: {file_path}")
            resume_text = self.pdf_parser.extract_text(file_path)

            if not resume_text or len(resume_text) < 50:
                return {
                    "success": False,
                    "error": "无法从PDF中提取有效文本，请确认文件是否正确",
                }

            # 2. 信息提取
            if use_ai and self.ai_service:
                extracted_data = await self._extract_with_ai(resume_text)
            else:
                extracted_data = self.rule_extractor.extract(resume_text)

            # 3. 更新用户画像
            self._update_user_profile(
                user_id=user_id,
                data=extracted_data,
                resume_text=resume_text,
                file_path=file_path,
            )

            logger.info(f"简历解析成功，提取了 {len([v for v in extracted_data.values() if v])} 个字段")

            return {
                "success": True,
                "extracted_data": extracted_data,
                "resume_text": resume_text,
                "file_path": file_path,
            }

        except FileNotFoundError as e:
            logger.error(f"文件不存在: {file_path}")
            return {"success": False, "error": f"文件不存在: {file_path}"}

        except Exception as e:
            logger.error(f"简历解析失败: {e}")
            return {"success": False, "error": str(e)}

    async def _extract_with_ai(self, resume_text: str) -> Dict[str, Any]:
        """使用AI提取简历信息"""
        if not self.ai_service:
            logger.warning("AI服务不可用，回退到规则模式")
            return self.rule_extractor.extract(resume_text)

        try:
            result = await self.ai_service.extract_resume_info(resume_text)
            return result
        except Exception as e:
            logger.error(f"AI提取失败: {e}，回退到规则模式")
            return self.rule_extractor.extract(resume_text)

    def _update_user_profile(
        self,
        user_id: int,
        data: Dict[str, Any],
        resume_text: str,
        file_path: str,
    ) -> None:
        """更新用户画像"""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter(
                UserProfile.id == user_id
            ).first()

            if not profile:
                profile = UserProfile(id=user_id)
                db.add(profile)

            # 字段映射
            field_mapping = {
                "name": "name",
                "gender": "gender",
                "age": "age",
                "phone": "phone",
                "email": "email",
                "city": "city",
                "education": "education",
                "school": "school",
                "major": "major",
                "experience_years": "experience_years",
                "target_positions": "target_positions",
                "target_cities": "target_cities",
                "expected_salary_min": "expected_salary_min",
                "expected_salary_max": "expected_salary_max",
                "skills": "skills",
                "certifications": "certifications",
                "work_experiences": "work_experiences",
            }

            for source_field, target_field in field_mapping.items():
                value = data.get(source_field)
                if value is not None:
                    setattr(profile, target_field, value)

            # 简历文本和文件路径
            profile.resume_text = resume_text
            profile.resume_file = file_path

            db.commit()
            logger.info(f"用户画像已更新: user_id={user_id}")

        except Exception as e:
            logger.error(f"更新用户画像失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def get_resume_status(self, user_id: int = 1) -> Dict[str, Any]:
        """获取简历状态"""
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter(
                UserProfile.id == user_id
            ).first()

            if not profile:
                return {
                    "has_resume": False,
                    "resume_text": None,
                    "resume_file": None,
                }

            return {
                "has_resume": bool(profile.resume_text),
                "resume_text": profile.resume_text[:500] + "..." if profile.resume_text and len(profile.resume_text) > 500 else profile.resume_text,
                "resume_file": profile.resume_file,
                "parsed": bool(profile.skills or profile.target_positions),
            }

        finally:
            db.close()

    async def generate_search_keywords(
        self,
        user_id: int = 1,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        基于用户画像生成搜索关键词

        Returns:
            {
                "keywords": ["Python后端", "Java开发", ...],
                "filter_config": {...}
            }
        """
        db = SessionLocal()
        try:
            profile = db.query(UserProfile).filter(
                UserProfile.id == user_id
            ).first()

            if not profile or not profile.resume_text:
                return {
                    "keywords": [],
                    "filter_config": {},
                    "error": "请先上传并解析简历",
                }

            # 构建关键词
            keywords = []

            # 从目标职位提取
            if profile.target_positions:
                keywords.extend(profile.target_positions)

            # 从技能提取（前3个核心技能）
            if profile.skills:
                core_skills = profile.skills[:3]
                for skill in core_skills:
                    # 组合技能+职位
                    if profile.target_positions:
                        keywords.append(f"{skill}{profile.target_positions[0]}")
                    else:
                        keywords.append(skill)

            # 使用AI生成更智能的关键词
            if use_ai and self.ai_service:
                try:
                    profile_dict = self._profile_to_dict(profile)
                    ai_result = await self.ai_service.generate_search_keywords(profile_dict)
                    if ai_result.get("keywords"):
                        keywords = ai_result["keywords"]
                except Exception as e:
                    logger.warning(f"AI生成关键词失败: {e}")

            # 构建过滤条件
            filter_config = {
                "salary_range": None,
                "cities": profile.target_cities or [],
                "keywords": profile.skills[:5] if profile.skills else [],
            }

            if profile.expected_salary_min and profile.expected_salary_max:
                filter_config["salary_range"] = (
                    profile.expected_salary_min,
                    profile.expected_salary_max,
                )

            return {
                "keywords": list(set(keywords))[:10],  # 去重，最多10个
                "filter_config": filter_config,
            }

        finally:
            db.close()

    def _profile_to_dict(self, profile: UserProfile) -> Dict[str, Any]:
        """将UserProfile转换为字典"""
        return {
            "name": profile.name,
            "skills": profile.skills or [],
            "experience_years": profile.experience_years,
            "education": profile.education,
            "target_positions": profile.target_positions or [],
            "target_cities": profile.target_cities or [],
            "expected_salary_min": profile.expected_salary_min,
            "expected_salary_max": profile.expected_salary_max,
        }


# 单例
_resume_service: Optional[ResumeService] = None


def get_resume_service() -> ResumeService:
    """获取简历服务单例"""
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService()
    return _resume_service