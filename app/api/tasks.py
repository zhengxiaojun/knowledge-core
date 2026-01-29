from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import sql_models
from app.schemas import task_schema
from app.models.sql_models import get_db
from app.core.response import Success, Fail

router = APIRouter()

@router.post("/")
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: task_schema.TaskCreate
):
    """
    Create a new task.
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

@router.get("/")
def read_tasks(
    db: Session = Depends(get_db),
    knowledge_base_id: str = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all tasks, optionally filtered by knowledge_base_id.
    """
    query = db.query(sql_models.Task)
    if knowledge_base_id:
        query = query.filter(sql_models.Task.knowledge_base_id == knowledge_base_id)
    
    tasks = query.offset(skip).limit(limit).all()
    response_data = [task_schema.TaskOut.model_validate(task).dict() for task in tasks]
    return Success(data=response_data)

@router.get("/{task_id}")
def read_task(
    *,
    db: Session = Depends(get_db),
    task_id: int,
):
    """
    Get a specific task by ID.
    """
    task = db.query(sql_models.Task).filter(sql_models.Task.id == task_id).first()
    if not task:
        return Fail(message="Task not found", code=40401, status_code=404)
    
    response_data = task_schema.TaskOut.model_validate(task)
    return Success(data=response_data.dict())

@router.patch("/{task_id}")
def update_task(
    *,
    db: Session = Depends(get_db),
    task_id: int,
    task_in: task_schema.TaskUpdate
):
    """
    Update a task.
    """
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
    task = db.query(sql_models.Task).filter(sql_models.Task.id == task_id).first()
    if not task:
        return Fail(message="Task not found", code=40401, status_code=404)
    
    db.delete(task)
    db.commit()
    
    return Success(message="Task deleted successfully")
