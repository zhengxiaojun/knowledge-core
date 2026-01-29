from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.sql_models import StatusEnum


class GenerationTaskBase(BaseModel):
    raw_req_id: int


class GenerationTaskCreate(GenerationTaskBase):
    pass


class GenerationTaskUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class GenerationTaskOut(GenerationTaskBase):
    id: int
    status: StatusEnum
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationResultBase(BaseModel):
    task_id: int
    test_point_id: Optional[int] = None
    test_case_content: str


class GenerationResultCreate(GenerationResultBase):
    approved: bool = False


class GenerationResultUpdate(BaseModel):
    approved: Optional[bool] = None


class GenerationResultOut(GenerationResultBase):
    id: int
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Request/Response schemas for API
class BatchGenerateRequest(BaseModel):
    requirement_id: int
    options: Optional[Dict[str, Any]] = None


class BatchGenerateResponse(BaseModel):
    task_id: int
    status: str


class TaskStatusResponse(BaseModel):
    task_id: int
    status: str
    progress: int
    error_message: Optional[str] = None
    test_cases: List[Dict[str, Any]] = []
    created_at: str
    finished_at: Optional[str] = None
