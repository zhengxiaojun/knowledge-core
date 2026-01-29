"""Defect management API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.models import sql_models
from app.schemas import defect_schema
from app.models.sql_models import get_db
from app.core.response import Success, Fail

router = APIRouter()


@router.post("/")
def create_defect(
    *,
    db: Session = Depends(get_db),
    defect_in: defect_schema.DefectCreate
):
    """Create a new defect record."""
    # Check if defect_id already exists
    existing = db.query(sql_models.Defect).filter(
        sql_models.Defect.defect_id == defect_in.defect_id
    ).first()

    if existing:
        return Fail(message="Defect ID already exists", code=40001)

    db_defect = sql_models.Defect(
        defect_id=defect_in.defect_id,
        title=defect_in.title,
        phenomenon=defect_in.phenomenon,
        root_cause=defect_in.root_cause,
        related_req_id=defect_in.related_req_id,
        severity=defect_in.severity,
        status=defect_in.status
    )
    db.add(db_defect)
    db.commit()
    db.refresh(db_defect)

    return Success(data={
        "id": db_defect.id,
        "defect_id": db_defect.defect_id,
        "title": db_defect.title
    })


@router.get("/")
def list_defects(
    db: Session = Depends(get_db),
    requirement_id: Optional[int] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """List defects with optional filters."""
    query = db.query(sql_models.Defect)

    if requirement_id:
        query = query.filter(sql_models.Defect.related_req_id == requirement_id)
    if severity:
        query = query.filter(sql_models.Defect.severity == severity)

    defects = query.offset(skip).limit(limit).all()

    result = []
    for defect in defects:
        result.append({
            "id": defect.id,
            "defect_id": defect.defect_id,
            "title": defect.title,
            "phenomenon": defect.phenomenon,
            "severity": defect.severity,
            "status": defect.status,
            "created_at": defect.created_at.isoformat() if defect.created_at else None
        })

    return Success(data=result)


@router.get("/{defect_id}")
def get_defect(
    *,
    db: Session = Depends(get_db),
    defect_id: int
):
    """Get defect details by ID."""
    defect = db.query(sql_models.Defect).filter(
        sql_models.Defect.id == defect_id
    ).first()

    if not defect:
        return Fail(message="Defect not found", code=40401, status_code=404)

    return Success(data={
        "id": defect.id,
        "defect_id": defect.defect_id,
        "title": defect.title,
        "phenomenon": defect.phenomenon,
        "root_cause": defect.root_cause,
        "related_req_id": defect.related_req_id,
        "severity": defect.severity,
        "status": defect.status,
        "created_at": defect.created_at.isoformat() if defect.created_at else None
    })


@router.put("/{defect_id}")
def update_defect(
    *,
    db: Session = Depends(get_db),
    defect_id: int,
    defect_in: defect_schema.DefectUpdate
):
    """Update defect information."""
    defect = db.query(sql_models.Defect).filter(
        sql_models.Defect.id == defect_id
    ).first()

    if not defect:
        return Fail(message="Defect not found", code=40401, status_code=404)

    update_data = defect_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(defect, field):
            setattr(defect, field, value)

    db.commit()
    db.refresh(defect)

    return Success(data={"id": defect.id, "message": "Updated successfully"})


@router.post("/{defect_id}/extract-risk")
def extract_risk_from_defect(
    *,
    db: Session = Depends(get_db),
    defect_id: int
):
    """
    Extract risk/test point from a defect and add to knowledge base.
    """
    defect = db.query(sql_models.Defect).filter(
        sql_models.Defect.id == defect_id
    ).first()

    if not defect:
        return Fail(message="Defect not found", code=40401, status_code=404)

    # Create a risk test point based on defect
    risk_content = f"{defect.title}: {defect.phenomenon}"
    if defect.root_cause:
        risk_content += f" (Root cause: {defect.root_cause})"

    test_point = sql_models.TestPoint(
        content=risk_content,
        type=sql_models.TestKnowledgeTypeEnum.RISK,
        confidence=0.9,
        source="defect"
    )
    db.add(test_point)
    db.commit()
    db.refresh(test_point)

    return Success(data={
        "test_point_id": test_point.id,
        "content": test_point.content,
        "message": "Risk point extracted successfully"
    })
