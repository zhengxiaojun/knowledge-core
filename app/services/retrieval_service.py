from typing import List, Dict
from app.services.milvus_service import MilvusService
from app.services.graph_service import GraphService

class RetrievalService:
    def __init__(self, milvus_service: MilvusService, graph_service: GraphService):
        self.milvus_service = milvus_service
        self.graph_service = graph_service

    def search(self, query_text: str, top_k: int = 10, graph_depth: int = 1) -> List[Dict]:
        """
        Performs a hybrid search using both vector search and graph traversal.
        """
        # 1. Vector search to get initial candidates
        vector_results = self.milvus_service.search(query_text=query_text, top_k=top_k)
        
        if graph_depth == 0:
            # Return only vector search results without graph expansion
            return vector_results

        enriched_results = []
        
        # Collect all graph IDs for batch subgraph retrieval
        graph_ids = [res.get("graph_id") or res.get("id") for res in vector_results if res.get("graph_id") or res.get("id")]

        if not graph_ids:
            return vector_results

        # 2. Graph traversal to get context for all nodes at once
        try:
            nodes, relationships = self.graph_service.get_subgraph_by_ids(node_ids=graph_ids, depth=graph_depth)
            subgraph = {
                "nodes": nodes,
                "relationships": relationships
            }
        except Exception as e:
            print(f"Warning: Graph traversal failed: {e}")
            subgraph = {"nodes": [], "relationships": []}

        # 3. Combine and format results
        for res in vector_results:
            res['context_graph'] = subgraph
            enriched_results.append(res)
            
        return enriched_results

