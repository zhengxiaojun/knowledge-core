"""Statistics and analytics service."""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime, timedelta

from app.models import sql_models


class StatisticsService:
    """Service for generating statistics and analytics."""

    def __init__(self, db: Session):
        self.db = db

    def get_overview_stats(self) -> Dict[str, Any]:
        """Get overview statistics."""
        total_requirements = self.db.query(sql_models.RequirementRaw).count()
        total_test_points = self.db.query(sql_models.TestPoint).count()
        total_test_cases = self.db.query(sql_models.TestCase).count()
        total_defects = self.db.query(sql_models.Defect).count()

        confirmed_cases = self.db.query(sql_models.TestCase).filter(
            sql_models.TestCase.status == sql_models.TestCaseStatusEnum.CONFIRMED
        ).count()

        ai_generated_cases = self.db.query(sql_models.TestCase).filter(
            sql_models.TestCase.created_by == sql_models.CreatorEnum.AI
        ).count()

        return {
            "total_requirements": total_requirements,
            "total_test_points": total_test_points,
            "total_test_cases": total_test_cases,
            "total_defects": total_defects,
            "confirmed_cases": confirmed_cases,
            "ai_generated_cases": ai_generated_cases,
            "confirmation_rate": round(confirmed_cases / total_test_cases * 100, 2) if total_test_cases > 0 else 0
        }

    def get_generation_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get test case generation statistics for recent days."""
        start_date = datetime.utcnow() - timedelta(days=days)

        tasks = self.db.query(sql_models.GenerationTask).filter(
            sql_models.GenerationTask.created_at >= start_date
        ).all()

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == sql_models.StatusEnum.DONE)
        failed_tasks = sum(1 for t in tasks if t.status == sql_models.StatusEnum.FAILED)
        running_tasks = sum(1 for t in tasks if t.status == sql_models.StatusEnum.RUNNING)

        return {
            "period_days": days,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "success_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
        }

    def get_test_coverage_by_requirement(self, requirement_id: int) -> Dict[str, Any]:
        """Get test coverage statistics for a specific requirement."""
        # Get test points for this requirement
        test_points = self.db.query(sql_models.TestPoint).filter(
            sql_models.TestPoint.source == "requirement"
        ).all()

        # Get test cases
        test_cases = self.db.query(sql_models.TestCase).filter(
            sql_models.TestCase.related_req_id == requirement_id
        ).all()

        covered_points = len([tp for tp in test_points if any(tc.test_point_id == tp.id for tc in test_cases)])

        return {
            "requirement_id": requirement_id,
            "total_test_points": len(test_points),
            "covered_test_points": covered_points,
            "total_test_cases": len(test_cases),
            "coverage_rate": round(covered_points / len(test_points) * 100, 2) if test_points else 0
        }

    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        test_points = self.db.query(
            sql_models.TestPoint.type,
            func.count(sql_models.TestPoint.id)
        ).group_by(sql_models.TestPoint.type).all()

        type_distribution = {tp_type.value: count for tp_type, count in test_points}

        avg_confidence = self.db.query(
            func.avg(sql_models.TestPoint.confidence)
        ).scalar() or 0

        return {
            "type_distribution": type_distribution,
            "average_confidence": round(float(avg_confidence), 2),
            "total_knowledge_units": sum(type_distribution.values())
        }
