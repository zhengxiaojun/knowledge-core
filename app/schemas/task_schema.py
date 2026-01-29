from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.sql_models import StatusEnum

class TaskBase(BaseModel):
    knowledge_base_id: str
    status: StatusEnum = StatusEnum.PENDING

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    status: Optional[StatusEnum] = None

class TaskOut(TaskBase):
    id: int
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True
