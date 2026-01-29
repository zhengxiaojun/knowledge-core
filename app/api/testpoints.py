from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from app.models import sql_models
from app.models.sql_models import get_db
from app.core.response import Success, Fail
from app.services.retrieval_service import RetrievalService
from app.services.generation_service import GenerationService

router = APIRouter()


class GenerateTestPointsRequest(BaseModel):
    requirement_id: int
    history_context: Optional[Dict[str, Any]] = None


class TestPointResponse(BaseModel):
    point_id: str
    intent_id: Optional[str] = None
    category: str
    description: str


@router.post("/generate")
def generate_test_points(
    *,
    db: Session = Depends(get_db),
    req: GenerateTestPointsRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Generate test points based on requirement and historical knowledge.

    This is Phase 2 of the generation process:
    Phase 1: Intent Analysis (already done via /requirements/{id}/intent)
    Phase 2: Test Point Generation (this endpoint)
    Phase 3: Test Case Generation (via /testcases/generate)
    """
    # Get requirement
    requirement = db.query(sql_models.RequirementRaw).filter(
        sql_models.RequirementRaw.id == req.requirement_id
    ).first()

    if not requirement:
        # Fallback to legacy table
        requirement = db.query(sql_models.Requirement).filter(
            sql_models.Requirement.id == req.requirement_id
        ).first()

    if not requirement:
        return Fail(message="Requirement not found", code=40401, status_code=404)

    try:
        # Get requirement content
        content = requirement.full_content if hasattr(requirement, 'full_content') else requirement.description

        # Retrieve relevant historical knowledge
        if req.history_context:
            context = req.history_context
        else:
            # Auto-retrieve context using vector search + graph expansion
            search_results = retrieval_service.search(
                query_text=content,
                top_k=10,
                graph_depth=2
            )
            context = search_results

        # Generate test points using LLM
        from openai import OpenAI
        from app.core.config import settings
        import uuid

        client = OpenAI(api_key=settings.openai_api_key)

        context_str = json.dumps(context, ensure_ascii=False, indent=2)

        prompt = f"""
你是一名资深测试架构师，擅长从需求中提取测试点。

【任务】
基于以下需求和历史测试知识，生成结构化的测试点列表。

【需求内容】
{content}

【历史测试知识】
{context_str}

【输出要求】
生成JSON数组，每个测试点包含：
- category: "正常" | "异常" | "边界"
- description: 测试点描述（简洁明确）

示例输出：
{{
  "test_points": [
    {{"category": "正常", "description": "验证用户登录成功流程"}},
    {{"category": "异常", "description": "验证密码错误时的提示"}},
    {{"category": "边界", "description": "验证密码长度限制"}}
  ]
}}
"""

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=settings.llm_temperature
        )

        result = json.loads(response.choices[0].message.content)
        test_points = result.get("test_points", [])

        # Save test points to database
        saved_points = []
        for tp in test_points:
            # Determine type based on category
            type_mapping = {
                "正常": "TestPoint",
                "异常": "Risk",
                "边界": "Scenario"
            }

            db_test_point = sql_models.TestPoint(
                content=tp["description"],
                type=type_mapping.get(tp["category"], "TestPoint"),
                confidence=0.8,
                source="requirement"
            )
            db.add(db_test_point)
            db.commit()
            db.refresh(db_test_point)

            point_response = TestPointResponse(
                point_id=str(db_test_point.id),
                intent_id=None,
                category=tp["category"],
                description=tp["description"]
            )
            saved_points.append(point_response.dict())

        return Success(data={"test_points": saved_points})

    except Exception as e:
        return Fail(message=f"Test point generation failed: {str(e)}", code=50002)


@router.get("/{point_id}")
def get_test_point(
    *,
    db: Session = Depends(get_db),
    point_id: int
):
    """Get a specific test point by ID"""
    test_point = db.query(sql_models.TestPoint).filter(
        sql_models.TestPoint.id == point_id
    ).first()

    if not test_point:
        return Fail(message="Test point not found", code=40401, status_code=404)

    return Success(data={
        "point_id": str(test_point.id),
        "description": test_point.content,
        "type": test_point.type,
        "confidence": float(test_point.confidence) if test_point.confidence else 0.5
    })


@router.get("/")
def list_test_points(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all test points"""
    test_points = db.query(sql_models.TestPoint).offset(skip).limit(limit).all()

    result = []
    for tp in test_points:
        result.append({
            "point_id": str(tp.id),
            "description": tp.content,
            "type": tp.type,
            "confidence": float(tp.confidence) if tp.confidence else 0.5,
            "created_at": tp.created_at.isoformat() if tp.created_at else None
        })

    return Success(data=result)
