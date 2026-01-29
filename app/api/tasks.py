from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import json

from app.models import sql_models
from app.schemas import task_schema
from app.models.sql_models import get_db
from app.core.response import Success, Fail

router = APIRouter()


@router.get("/{task_id}")
def get_task_status(
    *,
    db: Session = Depends(get_db),
    task_id: int,
):
    """
    Query generation task status and results.
    This endpoint is specifically for GenerationTask which tracks test case generation.
    """
    # Try to get from GenerationTask table
    task = db.query(sql_models.GenerationTask).filter(
        sql_models.GenerationTask.id == task_id
    ).first()

    if task:
        # Get associated test cases from generation results
        results = db.query(sql_models.GenerationResult).filter(
            sql_models.GenerationResult.task_id == task_id
        ).all()

        test_cases = []
        for result in results:
            if result.test_case_content:
                try:
                    case_data = json.loads(result.test_case_content)
                    case_data['id'] = result.id
                    case_data['approved'] = result.approved
                    test_cases.append(case_data)
                except:
                    pass

        return Success(data={
            "task_id": task.id,
            "status": task.status.value,
            "progress": task.progress,
            "error_message": task.error_message,
            "test_cases": test_cases,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None
        })

    # Fallback to legacy Task table
    task = db.query(sql_models.Task).filter(sql_models.Task.id == task_id).first()
    if not task:
        return Fail(message="Task not found", code=40401, status_code=404)

    response_data = task_schema.TaskOut.model_validate(task)
    return Success(data=response_data.dict())


@router.get("/")
def list_tasks(
    db: Session = Depends(get_db),
    requirement_id: int = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    List generation tasks, optionally filtered by requirement_id.
    """
    query = db.query(sql_models.GenerationTask)

    if requirement_id:
        query = query.filter(sql_models.GenerationTask.raw_req_id == requirement_id)

    tasks = query.offset(skip).limit(limit).all()

    result = []
    for task in tasks:
        result.append({
            "task_id": task.id,
            "requirement_id": task.raw_req_id,
            "status": task.status.value,
            "progress": task.progress,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None
        })

    return Success(data=result)


# Legacy endpoints for backward compatibility

@router.post("/")
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: task_schema.TaskCreate
):
    """
    Create a new task (legacy endpoint).
    """
    kb = db.query(sql_models.KnowledgeBase).filter(sql_models.KnowledgeBase.id == task_in.knowledge_base_id).first()
    if not kb:
        return Fail(message="KnowledgeBase not found", code=40401, status_code=404)

    db_task = sql_models.Task(
        knowledge_base_id=task_in.knowledge_base_id,
        status=task_in.status
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    response_data = task_schema.TaskOut.model_validate(db_task)
    return Success(data=response_data.dict())


@router.patch("/{task_id}")
def update_task(
    *,
    db: Session = Depends(get_db),
    task_id: int,
    task_in: task_schema.TaskUpdate
):
    """
    Update a task (legacy endpoint).
    """
    # Try GenerationTask first
    task = db.query(sql_models.GenerationTask).filter(
        sql_models.GenerationTask.id == task_id
    ).first()

    if task:
        update_data = task_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)

        db.commit()
        db.refresh(task)

        return Success(data={
            "task_id": task.id,
            "status": task.status.value,
            "updated_at": task.created_at.isoformat() if task.created_at else None
        })

    # Fallback to legacy Task
    task = db.query(sql_models.Task).filter(sql_models.Task.id == task_id).first()
    if not task:
        return Fail(message="Task not found", code=40401, status_code=404)

    update_data = task_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    response_data = task_schema.TaskOut.model_validate(task)
    return Success(data=response_data.dict())


@router.delete("/{task_id}")
def delete_task(
    *,
    db: Session = Depends(get_db),
    task_id: int,
):
    """
    Delete a task.
    """
    # Try GenerationTask first
    task = db.query(sql_models.GenerationTask).filter(
        sql_models.GenerationTask.id == task_id
    ).first()

    if task:
        db.delete(task)
        db.commit()
        return Success(data={"message": "Task deleted successfully"})

    # Fallback to legacy Task
    task = db.query(sql_models.Task).filter(sql_models.Task.id == task_id).first()
    if not task:
        return Fail(message="Task not found", code=40401, status_code=404)

    db.delete(task)
    db.commit()
    return Success(data={"message": "Task deleted successfully"})
    """
    Delete a task.
    """
    task = db.query(sql_models.Task).filter(sql_models.Task.id == task_id).first()
    if not task:
        return Fail(message="Task not found", code=40401, status_code=404)
    
    db.delete(task)
    db.commit()
    
    return Success(message="Task deleted successfully")
