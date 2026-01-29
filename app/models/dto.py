from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel
from datetime import datetime


# ========== Requirement DTOs ==========

class RequirementRawDTO(BaseModel):
    """原始需求DTO"""
    id: Optional[int] = None
    title: str
    full_content: str
    source_type: Literal["text", "word", "pdf", "excel", "image"]
    source_file: Optional[str] = None
    created_at: Optional[datetime] = None


class RequirementStdDTO(BaseModel):
    """标准化需求DTO"""
    id: Optional[int] = None
    raw_req_id: int
    summary: Optional[str] = None
    business_domain: Optional[str] = None
    priority: Optional[Literal["P0", "P1", "P2", "P3"]] = None
    created_at: Optional[datetime] = None


# ========== Test Knowledge DTOs ==========

class TestKnowledgeUnitDTO(BaseModel):
    """测试知识单元DTO"""
    id: Optional[int] = None
    content: str
    type: Literal["TestPoint", "Scenario", "Risk"]
    confidence: Optional[float] = 0.5
    vector_id: Optional[str] = None
    graph_id: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None


class TestPointDTO(BaseModel):
    """测试点DTO（用于生成阶段）"""
    point_id: Optional[str] = None
    intent_id: Optional[str] = None
    category: Literal["正常", "异常", "边界", "normal", "abnormal", "boundary"]
    description: str


# ========== Test Case DTOs ==========

class TestCaseDTO(BaseModel):
    """测试用例DTO"""
    id: Optional[int] = None
    title: str
    precondition: Optional[str] = None
    steps: List[str] | str  # Can be list or JSON string
    expected: str
    related_req_id: Optional[int] = None
    test_point_id: Optional[int] = None
    status: Optional[Literal["draft", "confirmed", "executed"]] = "draft"
    created_by: Optional[Literal["ai", "manual"]] = "ai"
    created_at: Optional[datetime] = None


# ========== Defect DTOs ==========

class DefectDTO(BaseModel):
    """缺陷DTO"""
    id: Optional[int] = None
    defect_id: str
    title: str
    phenomenon: str
    root_cause: Optional[str] = None
    related_req_id: Optional[int] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


# ========== Intent DTOs ==========

class TestIntentDTO(BaseModel):
    """测试意图DTO"""
    intent_id: str
    description: str
    scope: Literal["functional", "exception", "risk", "boundary"]


# ========== Generation Task DTOs ==========

class GenerationTaskDTO(BaseModel):
    """生成任务DTO"""
    id: Optional[int] = None
    raw_req_id: int
    status: Literal["INIT", "RUNNING", "DONE", "FAILED"]
    progress: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class GenerationResultDTO(BaseModel):
    """生成结果DTO"""
    id: Optional[int] = None
    task_id: int
    test_point_id: Optional[int] = None
    test_case_content: str
    approved: bool = False
    created_at: Optional[datetime] = None


# ========== Vector Search DTOs ==========

class VectorSearchResultDTO(BaseModel):
    """向量检索结果DTO"""
    id: str
    content: str
    type: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


# ========== Graph DTOs ==========

class GraphNodeDTO(BaseModel):
    """图节点DTO"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]


class GraphRelationshipDTO(BaseModel):
    """图关系DTO"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class SubgraphDTO(BaseModel):
    """子图DTO"""
    nodes: List[GraphNodeDTO]
    relationships: List[GraphRelationshipDTO]
