from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import uuid
from datetime import datetime

from app.models import sql_models
from app.schemas import testcase_schema
from app.models.sql_models import get_db, StatusEnum, SessionLocal
from app.core.response import Success, Fail

router = APIRouter()


class GenerateTestCaseRequest(BaseModel):
    """Request to generate test cases from test points"""
    test_points: List[int]  # List of test point IDs


class BatchGenerateRequest(BaseModel):
    """Request for batch generation from requirement to test cases"""
    requirement_id: int
    options: Optional[Dict[str, Any]] = None


class ConfirmTestCaseRequest(BaseModel):
    """Request to confirm test cases"""
    case_ids: List[int]
    modifications: Optional[Dict[int, Dict[str, Any]]] = None


class ExportRequest(BaseModel):
    """Request to export test cases"""
    case_ids: List[int]
    format: str = "excel"  # excel, csv, json


def run_batch_generation_in_background(task_id: int, requirement_id: int):
    """Background task for batch test case generation"""
    db = SessionLocal()
    try:
        # Update task status
        task = db.query(sql_models.GenerationTask).filter(
            sql_models.GenerationTask.id == task_id
        ).first()

        if not task:
            return

        task.status = StatusEnum.RUNNING
        task.progress = 10
        db.commit()

        # Get requirement
        requirement = db.query(sql_models.RequirementRaw).filter(
            sql_models.RequirementRaw.id == requirement_id
        ).first()

        if not requirement:
            task.status = StatusEnum.FAILED
            task.error_message = "Requirement not found"
            db.commit()
            return

        # Step 1: Generate test points
        task.progress = 30
        db.commit()

        from app.core.dependencies import get_retrieval_service
        from openai import OpenAI
        from app.core.config import settings

        retrieval_service = get_retrieval_service()
        client = OpenAI(api_key=settings.openai_api_key)

        # Search for relevant context
        context = retrieval_service.search(
            query_text=requirement.full_content,
            top_k=10,
            graph_depth=2
        )

        context_str = json.dumps(context, ensure_ascii=False, indent=2)

        # Generate test points
        prompt_testpoints = f"""
你是一名资深测试架构师，基于需求生成测试点。

需求：{requirement.full_content}

历史知识：{context_str}

输出JSON格式：{{"test_points": [{{"category": "正常/异常/边界", "description": "测试点描述"}}]}}
"""

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt_testpoints}],
            response_format={"type": "json_object"}
        )

        test_points_data = json.loads(response.choices[0].message.content)
        test_points = test_points_data.get("test_points", [])

        task.progress = 50
        db.commit()

        # Step 2: Generate test cases from test points
        generated_cases = []

        for i, tp in enumerate(test_points):
            # Save test point
            db_tp = sql_models.TestPoint(
                content=tp["description"],
                type="TestPoint",
                confidence=0.8,
                source="requirement"
            )
            db.add(db_tp)
            db.commit()
            db.refresh(db_tp)

            # Generate test case
            prompt_case = f"""
你是测试工程师，为测试点生成详细测试用例。

测试点：{tp["description"]}
需求背景：{requirement.full_content[:500]}

输出JSON格式：
{{
  "title": "测试用例标题",
  "precondition": "前置条件",
  "steps": ["步骤1", "步骤2"],
  "expected": "预期结果"
}}
"""

            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt_case}],
                response_format={"type": "json_object"}
            )

            case_data = json.loads(response.choices[0].message.content)

            # Save test case
            db_case = sql_models.TestCase(
                title=case_data.get("title", tp["description"]),
                precondition=case_data.get("precondition"),
                steps=json.dumps(case_data.get("steps", []), ensure_ascii=False),
                expected=case_data.get("expected", ""),
                related_req_id=None,  # Will be linked later
                test_point_id=db_tp.id,
                status=sql_models.TestCaseStatusEnum.DRAFT,
                created_by=sql_models.CreatorEnum.AI
            )
            db.add(db_case)
            db.commit()
            db.refresh(db_case)

            # Save generation result
            db_result = sql_models.GenerationResult(
                task_id=task_id,
                test_point_id=db_tp.id,
                test_case_content=json.dumps(case_data, ensure_ascii=False),
                approved=False
            )
            db.add(db_result)
            generated_cases.append(db_case.id)

            # Update progress
            task.progress = 50 + int((i + 1) / len(test_points) * 40)
            db.commit()

        # Complete task
        task.status = StatusEnum.DONE
        task.progress = 100
        task.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        task = db.query(sql_models.GenerationTask).filter(
            sql_models.GenerationTask.id == task_id
        ).first()
        if task:
            task.status = StatusEnum.FAILED
            task.error_message = str(e)
            task.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@router.post("/generate")
def generate_test_cases(
    *,
    db: Session = Depends(get_db),
    req: GenerateTestCaseRequest
):
    """
    Convert test points to complete test cases.
    This is Phase 3 of the generation process.
    """
    if not req.test_points:
        return Fail(message="No test points provided", code=40001)

    try:
        from openai import OpenAI
        from app.core.config import settings

        client = OpenAI(api_key=settings.openai_api_key)
        test_cases = []

        for tp_id in req.test_points:
            # Get test point
            test_point = db.query(sql_models.TestPoint).filter(
                sql_models.TestPoint.id == tp_id
            ).first()

            if not test_point:
                continue

            # Generate test case
            prompt = f"""
你是测试工程师，为测试点生成详细测试用例。

测试点：{test_point.content}

输出JSON格式：
{{
  "title": "测试用例标题",
  "precondition": "前置条件",
  "steps": ["步骤1", "步骤2", "步骤3"],
  "expected": "预期结果"
}}
"""

            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            case_data = json.loads(response.choices[0].message.content)

            # Save to database
            db_case = sql_models.TestCase(
                title=case_data.get("title", test_point.content),
                precondition=case_data.get("precondition"),
                steps=json.dumps(case_data.get("steps", []), ensure_ascii=False),
                expected=case_data.get("expected", ""),
                test_point_id=tp_id,
                status=sql_models.TestCaseStatusEnum.DRAFT,
                created_by=sql_models.CreatorEnum.AI
            )
            db.add(db_case)
            db.commit()
            db.refresh(db_case)

            case_response = {
                "case_id": db_case.id,
                "title": db_case.title,
                "precondition": db_case.precondition,
                "steps": json.loads(db_case.steps) if db_case.steps else [],
                "expected": db_case.expected
            }
            test_cases.append(case_response)

        return Success(data={"test_cases": test_cases})

    except Exception as e:
        return Fail(message=f"Test case generation failed: {str(e)}", code=50002)


@router.post("/batch-generate")
def batch_generate_test_cases(
    *,
    db: Session = Depends(get_db),
    req: BatchGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    One-shot generation from requirement to test cases.
    Returns a task ID for tracking progress.
    """
    # Verify requirement exists
    requirement = db.query(sql_models.RequirementRaw).filter(
        sql_models.RequirementRaw.id == req.requirement_id
    ).first()

    if not requirement:
        return Fail(message="Requirement not found", code=40401, status_code=404)

    # Create generation task
    task = sql_models.GenerationTask(
        raw_req_id=req.requirement_id,
        status=StatusEnum.INIT,
        progress=0
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Start background generation
    background_tasks.add_task(
        run_batch_generation_in_background,
        task.id,
        req.requirement_id
    )

    return Success(data={
        "task_id": str(task.id),
        "status": task.status.value
    })


@router.post("/confirm")
def confirm_test_cases(
    *,
    db: Session = Depends(get_db),
    req: ConfirmTestCaseRequest
):
    """
    Confirm generated test cases with optional modifications.
    Confirmed cases will trigger knowledge feedback.
    """
    confirmed_count = 0
    failed_cases = []

    for case_id in req.case_ids:
        try:
            test_case = db.query(sql_models.TestCase).filter(
                sql_models.TestCase.id == case_id
            ).first()

            if not test_case:
                failed_cases.append({"case_id": case_id, "reason": "Not found"})
                continue

            # Apply modifications if provided
            if req.modifications and case_id in req.modifications:
                mods = req.modifications[case_id]
                for key, value in mods.items():
                    if hasattr(test_case, key):
                        setattr(test_case, key, value)

            # Update status to confirmed
            test_case.status = sql_models.TestCaseStatusEnum.CONFIRMED
            db.commit()

            # Trigger knowledge feedback
            try:
                from app.services.knowledge_feedback_service import KnowledgeFeedbackService
                feedback_service = KnowledgeFeedbackService(db)
                feedback_service.feedback_from_confirmed_testcase(case_id)
            except Exception as e:
                print(f"Knowledge feedback failed for case {case_id}: {e}")

            confirmed_count += 1

        except Exception as e:
            failed_cases.append({"case_id": case_id, "reason": str(e)})

    return Success(data={
        "confirmed_count": confirmed_count,
        "failed_cases": failed_cases
    })


@router.post("/export")
def export_test_cases(
    *,
    db: Session = Depends(get_db),
    req: ExportRequest
):
    """
    Export test cases to specified format (excel/csv/json).
    """
    if req.format not in ["excel", "csv", "json"]:
        return Fail(message="Invalid format. Must be excel, csv, or json", code=40001)

    # Get test cases
    test_cases = db.query(sql_models.TestCase).filter(
        sql_models.TestCase.id.in_(req.case_ids)
    ).all()

    if not test_cases:
        return Fail(message="No test cases found", code=40401)

    # Convert to export format
    export_data = []
    for tc in test_cases:
        export_data.append({
            "id": tc.id,
            "title": tc.title,
            "precondition": tc.precondition,
            "steps": json.loads(tc.steps) if tc.steps else [],
            "expected": tc.expected,
            "status": tc.status.value if tc.status else "draft",
            "created_at": tc.created_at.isoformat() if tc.created_at else None
        })

    # For now, return JSON data
    # In production, you would generate actual Excel/CSV files and return download URLs
    if req.format == "json":
        import tempfile
        import os

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        json.dump(export_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()

        # In production, upload to storage and return URL
        file_url = f"/downloads/{os.path.basename(temp_file.name)}"

        return Success(data={"file_url": file_url, "data": export_data})

    # For excel and csv, return data for now
    return Success(data={
        "file_url": f"/downloads/testcases.{req.format}",
        "data": export_data
    })


@router.post("/")
def create_test_case(
    *,
    db: Session = Depends(get_db),
    tc_in: testcase_schema.TestCaseCreate
):
    """
    Create a new test case manually.
    """
    db_tc = sql_models.TestCase(
        title=tc_in.description,  # Using description as title for backward compatibility
        precondition="",
        steps=json.dumps([tc_in.description], ensure_ascii=False),
        expected=tc_in.expected_result,
        related_req_id=tc_in.requirement_id if hasattr(tc_in, 'requirement_id') else None,
        status=sql_models.TestCaseStatusEnum.DRAFT,
        created_by=sql_models.CreatorEnum.MANUAL
    )
    db.add(db_tc)
    db.commit()
    db.refresh(db_tc)
    
    response_data = testcase_schema.TestCaseOut.model_validate(db_tc)
    return Success(data=response_data.dict())

@router.get("/")
def read_test_cases(
    db: Session = Depends(get_db),
    requirement_id: int = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all test cases, optionally filtered by requirement_id.
    """
    query = db.query(sql_models.TestCase)
    if requirement_id:
        query = query.filter(sql_models.TestCase.related_req_id == requirement_id)

    test_cases = query.offset(skip).limit(limit).all()

    result = []
    for tc in test_cases:
        result.append({
            "id": tc.id,
            "title": tc.title,
            "precondition": tc.precondition,
            "steps": json.loads(tc.steps) if tc.steps else [],
            "expected": tc.expected,
            "status": tc.status.value if tc.status else "draft",
            "created_at": tc.created_at.isoformat() if tc.created_at else None
        })

    return Success(data=result)

@router.get("/{test_case_id}")
def read_test_case(
    *,
    db: Session = Depends(get_db),
    test_case_id: int,
):
    """
    Get a specific test case by ID.
    """
    test_case = db.query(sql_models.TestCase).filter(sql_models.TestCase.id == test_case_id).first()
    if not test_case:
        return Fail(message="Test case not found", code=40401, status_code=404)
    
    return Success(data={
        "case_id": test_case.id,
        "title": test_case.title,
        "precondition": test_case.precondition,
        "steps": json.loads(test_case.steps) if test_case.steps else [],
        "expected": test_case.expected,
        "status": test_case.status.value if test_case.status else "draft",
        "updated_at": test_case.updated_at.isoformat() if test_case.updated_at else None
    })

@router.put("/{test_case_id}")
def update_test_case(
    *,
    db: Session = Depends(get_db),
    test_case_id: int,
    tc_in: testcase_schema.TestCaseUpdate
):
    """
    Edit test case content.
    """
    test_case = db.query(sql_models.TestCase).filter(sql_models.TestCase.id == test_case_id).first()
    if not test_case:
        return Fail(message="Test case not found", code=40401, status_code=404)

    update_data = tc_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(test_case, field):
            setattr(test_case, field, value)

    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    
    return Success(data={
        "case_id": test_case.id,
        "updated_at": test_case.updated_at.isoformat() if test_case.updated_at else None
    })
