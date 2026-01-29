"""Statistics and analytics API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.sql_models import get_db
from app.core.response import Success
from app.services.statistics_service import StatisticsService

router = APIRouter()


@router.get("/overview")
def get_overview_statistics(
    db: Session = Depends(get_db)
):
    """Get overview statistics of the system."""
    stats_service = StatisticsService(db)
    stats = stats_service.get_overview_stats()
    return Success(data=stats)


@router.get("/generation")
def get_generation_statistics(
    db: Session = Depends(get_db),
    days: int = 7
):
    """Get test case generation statistics for recent days."""
    stats_service = StatisticsService(db)
    stats = stats_service.get_generation_stats(days)
    return Success(data=stats)


@router.get("/coverage/{requirement_id}")
def get_coverage_statistics(
    *,
    db: Session = Depends(get_db),
    requirement_id: int
):
    """Get test coverage statistics for a requirement."""
    stats_service = StatisticsService(db)
    stats = stats_service.get_test_coverage_by_requirement(requirement_id)
    return Success(data=stats)


@router.get("/knowledge")
def get_knowledge_statistics(
    db: Session = Depends(get_db)
):
    """Get knowledge base statistics."""
    stats_service = StatisticsService(db)
    stats = stats_service.get_knowledge_stats()
    return Success(data=stats)
