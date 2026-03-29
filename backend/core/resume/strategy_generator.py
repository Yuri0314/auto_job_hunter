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
                "salary_min": int,
                "salary_max": int,
            }
        """
        logger.info("开始生成搜索策略")

        result = {
            "primary_keywords": self._generate_primary_keywords(profile),
            "variant_keywords": self._generate_variant_keywords(profile),
            "skill_combinations": self._generate_skill_combinations(profile),
            "cities": profile.get("preferred_cities", []) or ([profile.get("city")] if profile.get("city") else []),
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