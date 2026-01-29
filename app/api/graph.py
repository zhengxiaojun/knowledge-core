from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.graph_service import GraphService
from app.core.response import Success, Fail

router = APIRouter()

class GraphExpandRequest(BaseModel):
    node_ids: List[str]
    depth: int = 2

class GraphNode(BaseModel):
    id: str
    labels: List[str]
    properties: Dict[str, Any]

class GraphRelationship(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any]

class Subgraph(BaseModel):
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]

@router.post("/expand")
def expand_graph(
    req: GraphExpandRequest,
    graph_service: GraphService = Depends(GraphService),
):
    """
    From the test knowledge node, expand the relevant subgraph.
    """
    try:
        nodes, relationships = graph_service.get_subgraph_by_ids(
            node_ids=req.node_ids, 
            depth=req.depth
        )

        response_data = Subgraph(
            nodes=[GraphNode(**node) for node in nodes],
            relationships=[GraphRelationship(**rel) for rel in relationships]
        )
        
        return Success(data=response_data.dict())
    except Exception as e:
        return Fail(message=f"Graph expansion failed: {str(e)}")
