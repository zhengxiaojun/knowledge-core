from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.sql_models import StatusEnum

class RequirementBase(BaseModel):
    name: str
    description: Optional[str] = None
    priority: int = 1

class RequirementCreate(RequirementBase):
    pass

class RequirementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[StatusEnum] = None

class RequirementOut(RequirementBase):
    id: int
    status: StatusEnum
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True
