from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TestCaseBase(BaseModel):
    requirement_id: int
    description: str
    expected_result: Optional[str] = None

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(BaseModel):
    description: Optional[str] = None
    expected_result: Optional[str] = None

class TestCaseOut(TestCaseBase):
    id: int
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True
