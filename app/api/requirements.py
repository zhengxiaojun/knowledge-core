from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import uuid

from app.models import sql_models
from app.schemas import requirement_schema, knowledge_base_schema
from app.models.sql_models import get_db, StatusEnum, SessionLocal
from app.core.response import Success, Fail
from app.services.extraction_service import ExtractionService
from app.services.intent_service import IntentService

router = APIRouter()

def run_extraction_in_background(
    requirement_id: int,
    knowledge_base_id: str,
    text: str,
):
    """
    A function to run the extraction process in the background.
    """
    db = SessionLocal()
    extraction_service = ExtractionService()
    try:
        extraction_service.extract_and_store(
            requirement_id=str(requirement_id),
            knowledge_base_id=knowledge_base_id,
            text=text
        )
        db_kb = db.query(sql_models.KnowledgeBase).filter(sql_models.KnowledgeBase.id == knowledge_base_id).first()
        if db_kb:
            db_kb.status = StatusEnum.COMPLETED
            db.commit()
    except Exception as e:
        db_kb = db.query(sql_models.KnowledgeBase).filter(sql_models.KnowledgeBase.id == knowledge_base_id).first()
        if db_kb:
            db_kb.status = StatusEnum.FAILED
            db.commit()
        print(f"Extraction failed for KB {knowledge_base_id}: {e}")
    finally:
        db.close()


@router.post("/")
def create_requirement(
    *,
    db: Session = Depends(get_db),
    req_in: requirement_schema.RequirementCreate
):
    db_req = sql_models.Requirement(
        name=req_in.name,
        description=req_in.description,
        priority=req_in.priority
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    
    response_data = requirement_schema.RequirementOut.model_validate(db_req)
    return Success(data=response_data.dict())

@router.get("/")
def read_requirements(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    requirements = db.query(sql_models.Requirement).offset(skip).limit(limit).all()
    response_data = [requirement_schema.RequirementOut.model_validate(req).dict() for req in requirements]
    return Success(data=response_data)

@router.get("/{requirement_id}")
def read_requirement(
    *,
    db: Session = Depends(get_db),
    requirement_id: int,
):
    requirement = db.query(sql_models.Requirement).filter(sql_models.Requirement.id == requirement_id).first()
    if not requirement:
        return Fail(message="Requirement not found", code=40401, status_code=404)
    
    response_data = requirement_schema.RequirementOut.model_validate(requirement)
    return Success(data=response_data.dict())

class ExtractionRequest(requirement_schema.RequirementBase):
    pass

@router.post("/{requirement_id}/extraction")
def run_extraction(
    *,
    db: Session = Depends(get_db),
    requirement_id: int,
    background_tasks: BackgroundTasks,
    req_in: ExtractionRequest
):
    requirement = db.query(sql_models.Requirement).filter(sql_models.Requirement.id == requirement_id).first()
    if not requirement:
        return Fail(message="Requirement not found", code=40401, status_code=404)

    knowledge_base_id = f"KB-{uuid.uuid4().hex[:8].upper()}"
    
    db_kb = sql_models.KnowledgeBase(
        id=knowledge_base_id,
        requirement_id=requirement_id,
        status=StatusEnum.PROCESSING
    )
    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)

    background_tasks.add_task(
        run_extraction_in_background,
        requirement_id,
        knowledge_base_id,
        req_in.description,
    )
    
    response_data = knowledge_base_schema.KnowledgeBaseOut.model_validate(db_kb)
    return Success(data=response_data.dict())


@router.post("/{requirement_id}/intent")
def analyze_intent(
    *,
    db: Session = Depends(get_db),
    requirement_id: int,
    intent_service: IntentService = Depends(IntentService)
):
    requirement = db.query(sql_models.Requirement).filter(sql_models.Requirement.id == requirement_id).first()
    if not requirement:
        return Fail(message="Requirement not found", code=40401, status_code=404)
    
    try:
        intents = intent_service.analyze(requirement.description)
        return Success(data=intents)
    except Exception as e:
        return Fail(message=f"Intent analysis failed: {str(e)}")
