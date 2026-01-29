"""Knowledge feedback service for knowledge base evolution."""
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models import sql_models
from app.core.dependencies import get_milvus_service, get_graph_service


class KnowledgeFeedbackService:
    """Service for handling knowledge feedback and evolution."""

    def __init__(self, db: Session):
        self.db = db
        self.milvus_service = get_milvus_service()
        self.graph_service = get_graph_service()

    def feedback_from_confirmed_testcase(self, testcase_id: int) -> Dict[str, Any]:
        """
        Extract knowledge from confirmed test case and add to knowledge base.
        This implements the knowledge feedback loop.
        """
        testcase = self.db.query(sql_models.TestCase).filter(
            sql_models.TestCase.id == testcase_id
        ).first()

        if not testcase or testcase.status != sql_models.TestCaseStatusEnum.CONFIRMED:
            return {"status": "failed", "reason": "Test case not confirmed"}

        # Check if test point already exists
        if testcase.test_point_id:
            test_point = self.db.query(sql_models.TestPoint).filter(
                sql_models.TestPoint.id == testcase.test_point_id
            ).first()
            if test_point:
                # Update confidence
                test_point.confidence = min(1.0, float(test_point.confidence or 0.5) + 0.1)
                self.db.commit()
                return {
                    "status": "updated",
                    "test_point_id": test_point.id,
                    "new_confidence": float(test_point.confidence)
                }

        # Create new test point from confirmed case
        test_point = sql_models.TestPoint(
            content=testcase.title,
            type=sql_models.TestKnowledgeTypeEnum.TEST_POINT,
            confidence=0.8,  # High confidence for human-confirmed cases
            source="confirmed_case"
        )
        self.db.add(test_point)
        self.db.commit()
        self.db.refresh(test_point)

        # Update testcase reference
        testcase.test_point_id = test_point.id
        self.db.commit()

        # Add to vector database
        try:
            self.milvus_service.upsert([{
                "id": f"TP-{test_point.id}",
                "content": test_point.content,
                "type": test_point.type.value,
                "graph_id": f"TP-{test_point.id}",
                "knowledge_base_id": "feedback",
                "confidence": float(test_point.confidence)
            }])
        except Exception as e:
            print(f"Failed to add to Milvus: {e}")

        # Add to graph database
        try:
            self.graph_service.add_node("TestPoint", {
                "id": f"TP-{test_point.id}",
                "content": test_point.content,
                "type": test_point.type.value,
                "confidence": float(test_point.confidence)
            })

            # Create relationship with test case
            self.graph_service.add_node("TestCase", {
                "id": f"TC-{testcase.id}",
                "title": testcase.title
            })
            self.graph_service.add_relationship(
                "TestPoint", f"TP-{test_point.id}",
                "TestCase", f"TC-{testcase.id}",
                "COVERED_BY"
            )
        except Exception as e:
            print(f"Failed to add to Neo4j: {e}")

        return {
            "status": "success",
            "test_point_id": test_point.id,
            "message": "Knowledge extracted from confirmed test case"
        }

    def feedback_from_defect(self, defect_id: int) -> Dict[str, Any]:
        """
        Extract risk point from defect and add to knowledge base.
        """
        defect = self.db.query(sql_models.Defect).filter(
            sql_models.Defect.id == defect_id
        ).first()

        if not defect:
            return {"status": "failed", "reason": "Defect not found"}

        # Create risk point
        risk_content = f"Risk: {defect.title}"
        if defect.phenomenon:
            risk_content += f" - {defect.phenomenon}"

        risk_point = sql_models.TestPoint(
            content=risk_content,
            type=sql_models.TestKnowledgeTypeEnum.RISK,
            confidence=0.9,
            source="defect"
        )
        self.db.add(risk_point)
        self.db.commit()
        self.db.refresh(risk_point)

        # Add to vector and graph databases
        try:
            self.milvus_service.upsert([{
                "id": f"RISK-{risk_point.id}",
                "content": risk_point.content,
                "type": "Risk",
                "graph_id": f"RISK-{risk_point.id}",
                "knowledge_base_id": "defect_feedback",
                "confidence": 0.9
            }])

            self.graph_service.add_node("TestPoint", {
                "id": f"RISK-{risk_point.id}",
                "content": risk_point.content,
                "type": "Risk",
                "confidence": 0.9
            })

            # Link to defect
            self.graph_service.add_node("Defect", {
                "id": defect.defect_id,
                "title": defect.title
            })
            self.graph_service.add_relationship(
                "TestPoint", f"RISK-{risk_point.id}",
                "Defect", defect.defect_id,
                "TRIGGERED"
            )
        except Exception as e:
            print(f"Failed to add to vector/graph DB: {e}")

        return {
            "status": "success",
            "risk_point_id": risk_point.id,
            "message": "Risk point extracted from defect"
        }

    def batch_feedback_confirmed_cases(self, limit: int = 100) -> Dict[str, Any]:
        """
        Batch process confirmed test cases for knowledge feedback.
        """
        confirmed_cases = self.db.query(sql_models.TestCase).filter(
            sql_models.TestCase.status == sql_models.TestCaseStatusEnum.CONFIRMED,
            sql_models.TestCase.test_point_id == None
        ).limit(limit).all()

        success_count = 0
        failed_count = 0

        for case in confirmed_cases:
            result = self.feedback_from_confirmed_testcase(case.id)
            if result.get("status") in ["success", "updated"]:
                success_count += 1
            else:
                failed_count += 1

        return {
            "processed": success_count + failed_count,
            "success": success_count,
            "failed": failed_count
        }
