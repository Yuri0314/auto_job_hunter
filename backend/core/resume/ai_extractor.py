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