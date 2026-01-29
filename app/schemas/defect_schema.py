from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DefectBase(BaseModel):
    defect_id: str
    title: str
    phenomenon: Optional[str] = None
    root_cause: Optional[str] = None
    severity: Optional[str] = None


class DefectCreate(DefectBase):
    related_req_id: Optional[int] = None
    status: Optional[str] = None


class DefectUpdate(BaseModel):
    title: Optional[str] = None
    phenomenon: Optional[str] = None
    root_cause: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


class DefectOut(DefectBase):
    id: int
    related_req_id: Optional[int] = None
    status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
