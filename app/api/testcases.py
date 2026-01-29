from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import sql_models
from app.schemas import testcase_schema
from app.models.sql_models import get_db
from app.core.response import Success, Fail

router = APIRouter()

@router.post("/")
def create_test_case(
    *,
    db: Session = Depends(get_db),
    tc_in: testcase_schema.TestCaseCreate
):
    """
    Create a new test case.
    """
    requirement = db.query(sql_models.Requirement).filter(sql_models.Requirement.id == tc_in.requirement_id).first()
    if not requirement:
        return Fail(message="Requirement not found", code=40401, status_code=404)

    db_tc = sql_models.TestCase(
        requirement_id=tc_in.requirement_id,
        description=tc_in.description,
        expected_result=tc_in.expected_result
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
        query = query.filter(sql_models.TestCase.requirement_id == requirement_id)
    
    test_cases = query.offset(skip).limit(limit).all()
    response_data = [testcase_schema.TestCaseOut.model_validate(tc).dict() for tc in test_cases]
    return Success(data=response_data)

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
    
    response_data = testcase_schema.TestCaseOut.model_validate(test_case)
    return Success(data=response_data.dict())

@router.patch("/{test_case_id}")
def update_test_case(
    *,
    db: Session = Depends(get_db),
    test_case_id: int,
    tc_in: testcase_schema.TestCaseUpdate
):
    """
    Update a test case.
    """
    test_case = db.query(sql_models.TestCase).filter(sql_models.TestCase.id == test_case_id).first()
    if not test_case:
        return Fail(message="Test case not found", code=40401, status_code=404)

    update_data = tc_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test_case, field, value)
    
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    
    response_data = testcase_schema.TestCaseOut.model_validate(test_case)
    return Success(data=response_data.dict())
