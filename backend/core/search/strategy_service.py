"""搜索策略管理服务"""

from typing import Dict, Any, List, Optional
from loguru import logger

from backend.core.database import (
    SessionLocal,
    SearchStrategy,
    Resume,
    ResumeProfile,
)


class StrategyService:
    """搜索策略管理服务"""

    def get_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """获取搜索策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return None

            return self._to_dict(strategy)

        finally:
            db.close()

    def get_strategies_by_resume(self, resume_id: int) -> List[Dict[str, Any]]:
        """获取简历关联的所有搜索策略"""
        db = SessionLocal()
        try:
            strategies = db.query(SearchStrategy).filter(
                SearchStrategy.resume_id == resume_id
            ).order_by(SearchStrategy.priority.desc()).all()

            return [self._to_dict(s) for s in strategies]

        finally:
            db.close()

    def get_active_strategy(self, resume_id: int) -> Optional[Dict[str, Any]]:
        """获取简历的激活策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.resume_id == resume_id,
                SearchStrategy.is_active == True,
            ).first()

            return self._to_dict(strategy) if strategy else None

        finally:
            db.close()

    def create_strategy(
        self,
        resume_id: int,
        primary_keywords: List[str],
        variant_keywords: List[str] = None,
        skill_combinations: List[str] = None,
        cities: List[str] = None,
        salary_min: int = None,
        salary_max: int = None,
        exclude_keywords: List[str] = None,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """创建搜索策略"""
        db = SessionLocal()
        try:
            strategy = SearchStrategy(
                resume_id=resume_id,
                primary_keywords=primary_keywords or [],
                variant_keywords=variant_keywords or [],
                skill_combinations=skill_combinations or [],
                cities=cities or [],
                salary_min=salary_min,
                salary_max=salary_max,
                exclude_keywords=exclude_keywords or [],
                priority=priority,
                is_active=True,
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)

            return self._to_dict(strategy)

        except Exception as e:
            logger.error(f"创建搜索策略失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def update_strategy(
        self,
        strategy_id: int,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """更新搜索策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return None

            # 可更新字段
            updatable = [
                "primary_keywords", "variant_keywords", "skill_combinations",
                "cities", "salary_min", "salary_max", "exclude_keywords",
                "priority", "is_active",
            ]

            for field in updatable:
                if field in kwargs:
                    setattr(strategy, field, kwargs[field])

            db.commit()
            return self._to_dict(strategy)

        except Exception as e:
            logger.error(f"更新搜索策略失败: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def delete_strategy(self, strategy_id: int) -> bool:
        """删除搜索策略"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return False

            db.delete(strategy)
            db.commit()
            return True

        finally:
            db.close()

    def set_active_strategy(self, strategy_id: int) -> bool:
        """设置激活策略（同一简历的其他策略设为非激活）"""
        db = SessionLocal()
        try:
            strategy = db.query(SearchStrategy).filter(
                SearchStrategy.id == strategy_id
            ).first()

            if not strategy:
                return False

            # 取消同简历其他策略的激活状态
            db.query(SearchStrategy).filter(
                SearchStrategy.resume_id == strategy.resume_id,
                SearchStrategy.id != strategy_id,
            ).update({"is_active": False})

            # 激活当前策略
            strategy.is_active = True
            db.commit()

            return True

        except Exception as e:
            logger.error(f"设置激活策略失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_all_keywords(self, strategy_id: int) -> List[str]:
        """获取策略的所有关键词（用于搜索）"""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return []

        keywords = []
        keywords.extend(strategy.get("primary_keywords", []))
        keywords.extend(strategy.get("variant_keywords", []))
        keywords.extend(strategy.get("skill_combinations", []))

        # 去重
        seen = set()
        unique = []
        for k in keywords:
            if k and k not in seen:
                seen.add(k)
                unique.append(k)

        return unique

    def _to_dict(self, strategy: SearchStrategy) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": strategy.id,
            "resume_id": strategy.resume_id,
            "primary_keywords": strategy.primary_keywords or [],
            "variant_keywords": strategy.variant_keywords or [],
            "skill_combinations": strategy.skill_combinations or [],
            "cities": strategy.cities or [],
            "salary_min": strategy.salary_min,
            "salary_max": strategy.salary_max,
            "exclude_keywords": strategy.exclude_keywords or [],
            "priority": strategy.priority,
            "is_active": strategy.is_active,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
        }


# 单例
_strategy_service: Optional[StrategyService] = None


def get_strategy_service() -> StrategyService:
    """获取策略服务单例"""
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService()
    return _strategy_service