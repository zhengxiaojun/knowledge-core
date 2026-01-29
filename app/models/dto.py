from typing import List, Optional, Literal
from pydantic import BaseModel


class RequirementDTO(BaseModel):
    requirement_id: str
    title: str
    full_content: str
    source_type: Literal["text", "word", "pdf"]
    created_at: Optional[str] = None


class TestCaseDTO(BaseModel):
    id: str
    title: str
    precondition: Optional[str] = None
    steps: List[str]
    expected: str


class DefectDTO(BaseModel):
    id: str
    title: str
    phenomenon: str
    root_cause: Optional[str] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None


class TestKnowledgeUnitDTO(BaseModel):
    id: str
    content: str
    type: Literal["TestPoint", "Scenario", "Risk"]
    graph_id: Optional[str] = None
    confidence: Optional[float] = None
