from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.sql_models import StatusEnum

class KnowledgeBaseBase(BaseModel):
    requirement_id: int

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(BaseModel):
    status: Optional[StatusEnum] = None

class KnowledgeBaseOut(KnowledgeBaseBase):
    id: str
    status: StatusEnum
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True
