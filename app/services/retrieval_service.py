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
        
        enriched_results = []
        
        for res in vector_results:
            graph_id = res.get("id") # The 'id' from Milvus is the graph_id
            if not graph_id:
                continue

            # 2. Graph traversal to get context
            subgraph_paths = self.graph_service.get_subgraph(start_node_id=graph_id, depth=graph_depth)
            
            # 3. Combine and format results
            # For simplicity, we'll just add the raw subgraph to the result for now.
            # A more advanced implementation would process this into a cleaner format.
            res['context_graph'] = self._format_subgraph(subgraph_paths)
            enriched_results.append(res)
            
        return enriched_results

    def _format_subgraph(self, subgraph_paths: List[Dict]) -> Dict:
        """
        Formats the raw subgraph paths into a clean nodes-and-edges structure.
        """
        nodes = {}
        edges = set()

        for path_data in subgraph_paths:
            path = path_data.get('path')
            if not path:
                continue
            
            for node in path.nodes:
                node_id = node.get("id")
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": list(node.labels)[0],
                        "properties": dict(node)
                    }
            
            for rel in path.relationships:
                edge_tuple = (rel.start_node.get("id"), rel.type, rel.end_node.get("id"))
                edges.add(edge_tuple)

        return {
            "nodes": list(nodes.values()),
            "edges": [{"source": s, "relation": r, "target": t} for s, r, t in edges]
        }
