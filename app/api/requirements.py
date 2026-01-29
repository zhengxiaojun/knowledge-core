from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid
import os
from pathlib import Path

from app.models import sql_models
from app.schemas import requirement_schema, knowledge_base_schema
from app.models.sql_models import get_db, StatusEnum, SessionLocal
from app.core.response import Success, Fail
from app.services.extraction_service import ExtractionService
from app.services.intent_service import IntentService
from app.services.parser import DocumentParser

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


@router.post("/upload")
async def upload_requirement(
    *,
    db: Session = Depends(get_db),
    project_id: str = Form(...),
    input_type: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload requirement documents (supports text, Word, PDF, Excel, image)
    """
    if input_type not in ["text", "doc", "pdf", "excel", "image"]:
        return Fail(message="Invalid input_type. Must be one of: text, doc, pdf, excel, image", code=40001)

    # Create upload directory if it doesn't exist
    upload_dir = Path("uploads") / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    parser = DocumentParser()
    parsed_content = ""
    source_files = []

    for file in files:
        # Save file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        source_files.append(file.filename)

        # Parse content based on type
        try:
            if input_type == "text":
                parsed_content += content.decode("utf-8") + "\n"
            elif input_type in ["doc", "docx"]:
                parsed_content += parser.parse_word(str(file_path)) + "\n"
            elif input_type == "pdf":
                parsed_content += parser.parse_pdf(str(file_path)) + "\n"
            elif input_type == "excel":
                parsed_content += parser.parse_excel(str(file_path)) + "\n"
            elif input_type == "image":
                # For images, save path for future OCR processing
                parsed_content += f"[Image: {file.filename}]\n"
        except Exception as e:
            return Fail(message=f"Failed to parse file {file.filename}: {str(e)}", code=50001)

    # Create requirement_raw entry
    db_req_raw = sql_models.RequirementRaw(
        title=f"Requirement from {input_type}",
        full_content=parsed_content,
        source_type=input_type,
        source_file=", ".join(source_files)
    )
    db.add(db_req_raw)
    db.commit()
    db.refresh(db_req_raw)

    return Success(data={
        "requirement_id": str(db_req_raw.id),
        "raw_chunks": len(source_files)
    })


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
    # Try to get from requirement_raw first
    requirement = db.query(sql_models.RequirementRaw).filter(sql_models.RequirementRaw.id == requirement_id).first()
    if requirement:
        return Success(data={
            "requirement_id": requirement.id,
            "title": requirement.title,
            "full_content": requirement.full_content,
            "source_type": requirement.source_type,
            "created_at": requirement.created_at.isoformat() if requirement.created_at else None
        })

    # Fallback to legacy table
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
    intent_service: IntentService = Depends(get_intent_service)
):
    # Try requirement_raw first
    requirement = db.query(sql_models.RequirementRaw).filter(sql_models.RequirementRaw.id == requirement_id).first()
    if not requirement:
        # Fallback to legacy table
        requirement = db.query(sql_models.Requirement).filter(sql_models.Requirement.id == requirement_id).first()

    if not requirement:
        return Fail(message="Requirement not found", code=40401, status_code=404)
    
    try:
        content = requirement.full_content if hasattr(requirement, 'full_content') else requirement.description
        intents = intent_service.analyze(content)
        return Success(data=intents)
    except Exception as e:
        return Fail(message=f"Intent analysis failed: {str(e)}")
