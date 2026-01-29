"""
Dependency injection for services.
Provides factory functions for creating service instances with proper dependencies.
"""
from functools import lru_cache
from app.services.milvus_service import MilvusService
from app.services.graph_service import GraphService
from app.services.retrieval_service import RetrievalService
from app.services.extraction_service import ExtractionService
from app.services.intent_service import IntentService
from app.services.generation_service import GenerationService


# Singleton instances
_milvus_service = None
_graph_service = None
_retrieval_service = None
_extraction_service = None
_intent_service = None
_generation_service = None


def get_milvus_service() -> MilvusService:
    """Get or create MilvusService singleton."""
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
    return _milvus_service


def get_graph_service() -> GraphService:
    """Get or create GraphService singleton."""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service


def get_retrieval_service() -> RetrievalService:
    """Get or create RetrievalService singleton."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService(
            milvus_service=get_milvus_service(),
            graph_service=get_graph_service()
        )
    return _retrieval_service


def get_extraction_service() -> ExtractionService:
    """Get or create ExtractionService singleton."""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService(
            graph_service=get_graph_service(),
            milvus_service=get_milvus_service()
        )
    return _extraction_service


def get_intent_service() -> IntentService:
    """Get or create IntentService singleton."""
    global _intent_service
    if _intent_service is None:
        _intent_service = IntentService()
    return _intent_service


def get_generation_service() -> GenerationService:
    """Get or create GenerationService singleton."""
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService(
            retrieval_service=get_retrieval_service()
        )
    return _generation_service


# Cleanup function
def cleanup_services():
    """Cleanup all service instances."""
    global _graph_service
    if _graph_service is not None:
        try:
            _graph_service.close()
        except Exception as e:
            print(f"Error closing graph service: {e}")
