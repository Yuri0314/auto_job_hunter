"""AI服务模块 - 智能模式支持"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from loguru import logger

from backend.core.config import get_settings


@dataclass
class MatchResult:
    """匹配结果"""
    total_score: int
    skill_score: int
    experience_score: int
    salary_score: int
    career_score: int
    match_points: List[str]
    gap_points: List[str]
    recommendation: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchResult":
        return cls(
            total_score=data.get("total_score", 0),
            skill_score=data.get("skill_score", 0),
            experience_score=data.get("experience_score", 0),
            salary_score=data.get("salary_score", 0),
            career_score=data.get("career_score", 0),
            match_points=data.get("match_points", []),
            gap_points=data.get("gap_points", []),
            recommendation=data.get("recommendation", ""),
        )


class AIProvider(ABC):
    """AI服务提供商基类"""

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """发送聊天请求"""
        pass

    @abstractmethod
    async def chat_with_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """发送聊天请求并返回JSON"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI服务提供商"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or get_settings().openai_api_key
        self.model = model or get_settings().openai_model
        self.base_url = base_url

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """发送聊天请求"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise

    async def chat_with_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """发送聊天请求并返回JSON"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"OpenAI JSON chat error: {e}")
            raise


class OllamaProvider(AIProvider):
    """Ollama本地模型服务提供商"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.base_url = base_url or settings.ollama_base_url or "http://localhost:11434"
        self.model = model or settings.ollama_model or "llama3"

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """发送聊天请求"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def chat_with_json(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """发送聊天请求并返回JSON"""
        # Ollama不支持原生JSON模式，需要在提示词中要求
        messages[-1]["content"] += "\n\n请以JSON格式返回结果。"
        response = await self.chat(messages)

        # 尝试解析JSON
        try:
            # 尝试找到JSON块
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from Ollama response: {response[:200]}")
            return {}


class AIService:
    """AI服务统一接口"""

    def __init__(self, provider: Optional[AIProvider] = None):
        self._provider = provider or self._create_default_provider()
        self._cost_tracker = CostTracker()

    def _create_default_provider(self) -> AIProvider:
        """创建默认AI服务提供商"""
        settings = get_settings()

        # 优先使用OpenAI
        if settings.openai_api_key:
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
            )

        # 其次使用Ollama
        if settings.ollama_base_url:
            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )

        raise ValueError("No AI provider configured. Please set OPENAI_API_KEY or OLLAMA_BASE_URL")

    def set_provider(self, provider: AIProvider) -> None:
        """设置AI服务提供商"""
        self._provider = provider

    async def analyze_job_match(
        self,
        resume: str,
        job_description: str,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> MatchResult:
        """分析职位匹配度"""
        prompt = self._build_matching_prompt(resume, job_description, user_info)

        messages = [
            {"role": "system", "content": "你是一个专业的招聘顾问，擅长分析简历与职位的匹配度。"},
            {"role": "user", "content": prompt},
        ]

        self._cost_tracker.record_request()
        result = await self._provider.chat_with_json(messages)

        return MatchResult.from_dict(result)

    async def generate_greeting(
        self,
        match_result: MatchResult,
        user_name: str,
        experience_years: int,
        style: str = "professional",
        max_length: int = 200,
    ) -> str:
        """生成个性化打招呼语"""
        prompt = f"""根据以下匹配信息，生成一个个性化的打招呼语：

【匹配信息】
- 匹配度总分: {match_result.total_score}分
- 匹配点: {', '.join(match_result.match_points[:3])}
- 推荐理由: {match_result.recommendation}

【用户信息】
- 姓名: {user_name}
- 工作经验: {experience_years}年

要求:
1. 突出匹配点，特别是技能和经验方面的优势
2. 表达求职意愿
3. 控制在{max_length}字以内
4. 语气要{self._get_style_description(style)}

直接输出打招呼语，不要其他内容："""

        messages = [
            {"role": "system", "content": "你是一个求职顾问，擅长撰写专业且有吸引力的求职打招呼语。"},
            {"role": "user", "content": prompt},
        ]

        self._cost_tracker.record_request()
        return await self._provider.chat(messages)

    def _build_matching_prompt(
        self,
        resume: str,
        job_description: str,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建匹配分析提示词"""
        user_context = ""
        if user_info:
            user_context = f"\n【用户补充信息】\n{json.dumps(user_info, ensure_ascii=False, indent=2)}"

        return f"""请分析以下简历和职位描述的匹配度：

【简历信息】
{resume}
{user_context}

【职位描述】
{job_description}

请从以下维度评估匹配度（每项0-100分）：
1. 技能匹配度：候选人技能与职位要求的匹配程度
2. 经验匹配度：候选人工作经验与职位要求的匹配程度
3. 薪资期望匹配度：候选人期望薪资与职位薪资范围的匹配程度
4. 职业发展匹配度：职位对候选人职业发展的价值

输出JSON格式：
{{
    "total_score": 总分（加权平均）,
    "skill_score": 技能分,
    "experience_score": 经验分,
    "salary_score": 薪资分,
    "career_score": 发展分,
    "match_points": ["匹配点1", "匹配点2", "匹配点3"],
    "gap_points": ["差距1", "差距2"],
    "recommendation": "投递建议（一句话）"
}}"""

    def _get_style_description(self, style: str) -> str:
        """获取风格描述"""
        styles = {
            "professional": "专业、正式，适合大公司或传统行业",
            "friendly": "友好、亲切，适合创业公司或互联网公司",
            "formal": "非常正式，适合国企或金融机构",
        }
        return styles.get(style, styles["professional"])

    def get_cost_summary(self) -> Dict[str, Any]:
        """获取成本统计"""
        return self._cost_tracker.get_summary()


class CostTracker:
    """AI调用成本追踪"""

    def __init__(self):
        self._request_count = 0
        self._total_tokens = 0
        # GPT-4定价参考（2024年）
        self._cost_per_1k_tokens = {
            "gpt-4": 0.03,  # 约0.2元/1k tokens
            "gpt-3.5-turbo": 0.001,
            "default": 0.01,
        }

    def record_request(self, tokens: int = 1000) -> None:
        """记录一次请求"""
        self._request_count += 1
        self._total_tokens += tokens

    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        estimated_cost = (self._total_tokens / 1000) * self._cost_per_1k_tokens["default"]

        return {
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "estimated_cost_rmb": round(estimated_cost * 7, 2),  # 粗略换算成人民币
        }


# 全局AI服务实例
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """获取AI服务单例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service