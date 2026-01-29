from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.sql_models import TestKnowledgeTypeEnum


class TestPointBase(BaseModel):
    content: str
    type: TestKnowledgeTypeEnum
    confidence: Optional[float] = 0.5
    source: Optional[str] = None


class TestPointCreate(TestPointBase):
    pass


class TestPointUpdate(BaseModel):
    content: Optional[str] = None
    type: Optional[TestKnowledgeTypeEnum] = None
    confidence: Optional[float] = None
    vector_id: Optional[str] = None
    graph_id: Optional[str] = None


class TestPointOut(TestPointBase):
    id: int
    vector_id: Optional[str] = None
    graph_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
