"""Data import API for historical test data."""
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List

from app.models import sql_models
from app.models.sql_models import get_db
from app.core.response import Success, Fail
from app.services.import_service import DataImportService

router = APIRouter()


@router.post("/import/excel")
async def import_from_excel(
    *,
    db: Session = Depends(get_db),
    data_type: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Import historical data from Excel file.
    data_type: requirements, testcases, or defects
    """
    if data_type not in ["requirements", "testcases", "defects"]:
        return Fail(message="Invalid data_type", code=40001)

    # Save uploaded file
    upload_dir = Path("uploads/imports")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Import data
    import_service = DataImportService(db)
    result = import_service.import_from_excel(str(file_path), data_type)

    return Success(data=result)


@router.post("/import/batch-extract")
def batch_extract_knowledge(
    *,
    db: Session = Depends(get_db),
    requirement_ids: List[int]
):
    """
    Batch extract test knowledge from requirements.
    """
    from app.core.dependencies import get_extraction_service

    extraction_service = get_extraction_service()
    extracted = 0
    failed = 0

    for req_id in requirement_ids:
        try:
            req = db.query(sql_models.RequirementRaw).filter(
                sql_models.RequirementRaw.id == req_id
            ).first()
            if req:
                extraction_service.extract_and_store(
                    str(req.id), f"KB-{req.id}", req.full_content
                )
                extracted += 1
        except Exception as e:
            print(f"Extract failed for {req_id}: {e}")
            failed += 1

    return Success(data={"extracted": extracted, "failed": failed})
