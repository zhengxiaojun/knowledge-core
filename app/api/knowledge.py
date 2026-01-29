from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.retrieval_service import RetrievalService
from app.core.response import Success, Fail

router = APIRouter()

class SearchRequest(BaseModel):
    query_text: str
    top_k: int = 10

class SearchResult(BaseModel):
    id: str
    content: str
    type: str
    score: float

@router.post("/search")
def search(
    req: SearchRequest,
    retrieval_service: RetrievalService = Depends(RetrievalService),
):
    """
    Based on semantic similarity, retrieve test knowledge.
    The search method of retrieval_service returns a list of dictionaries, 
    each containing vector search results and graph context.
    This endpoint should only return the vector search part.
    """
    try:
        # The retrieval_service.search might return more data than needed.
        # We only extract the fields required by the API spec.
        search_results = retrieval_service.search(
            query_text=req.query_text,
            top_k=req.top_k,
            graph_depth=0 # We don't need graph expansion here
        )
        
        # Map the results to the SearchResult model
        response_data = [
            SearchResult(
                id=res.get("id"),
                content=res.get("content"),
                type=res.get("type"),
                score=res.get("score")
            ) for res in search_results
        ]
        
        return Success(data=[res.dict() for res in response_data])
    except Exception as e:
        return Fail(message=f"Search failed: {str(e)}")
