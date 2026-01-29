import uuid
import json
from typing import Dict
from openai import OpenAI
from app.core.config import settings
from app.core.prompts import PromptTemplates
from app.services.graph_service import GraphService
from app.services.milvus_service import MilvusService

class ExtractionService:
    def __init__(self, graph_service: GraphService, milvus_service: MilvusService):
        self.graph_service = graph_service
        self.milvus_service = milvus_service
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def _call_llm_for_extraction(self, text: str) -> Dict:
        prompt = PromptTemplates.get_knowledge_extraction_prompt(text)

        response = self.openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=settings.llm_temperature
        )
        
        return json.loads(response.choices[0].message.content)

    def extract_and_store(self, requirement_id: str, knowledge_base_id: str, text: str):
        """
        Orchestrates the extraction and storage process, associating all data with a knowledge_base_id.
        """
        extracted_data = self._call_llm_for_extraction(text)
        
        nodes_to_upsert_in_milvus = []
        temp_id_to_graph_id = {}

        # 1. Add requirement node to graph
        self.graph_service.add_node("Requirement", {"id": requirement_id, "content": "Root requirement", "knowledge_base_id": knowledge_base_id})

        # 2. Process and store nodes
        for node_data in extracted_data.get("nodes", []):
            graph_id = f"K-{uuid.uuid4().hex[:8].upper()}"
            temp_id = node_data["id"]
            temp_id_to_graph_id[temp_id] = graph_id
            
            node_properties = {
                "id": graph_id,
                "content": node_data["content"],
                "requirement_id": requirement_id,
                "knowledge_base_id": knowledge_base_id
            }
            # Dynamically use the node type from LLM output
            node_type = node_data.get("type", "TestPoint") # Default to TestPoint
            self.graph_service.add_node(node_type, node_properties)
            
            nodes_to_upsert_in_milvus.append({
                "id": graph_id,
                "content": node_data["content"],
                "type": node_type,
                "graph_id": graph_id,
                "knowledge_base_id": knowledge_base_id,
                "confidence": node_data.get("confidence", 1.0)
            })
            
            # Use "DERIVE" relationship as per the database design
            self.graph_service.add_relationship("Requirement", requirement_id, node_type, graph_id, "DERIVE")

        # 3. Upsert to Milvus
        if nodes_to_upsert_in_milvus:
            self.milvus_service.upsert(nodes_to_upsert_in_milvus)

        # 4. Process and store relationships
        for edge_data in extracted_data.get("edges", []):
            source_temp_id = edge_data["source"]
            target_temp_id = edge_data["target"]
            
            source_graph_id = temp_id_to_graph_id.get(source_temp_id)
            target_graph_id = temp_id_to_graph_id.get(target_temp_id)
            
            source_node_type = next((n["type"] for n in extracted_data["nodes"] if n["id"] == source_temp_id), "TestPoint")
            target_node_type = next((n["type"] for n in extracted_data["nodes"] if n["id"] == target_temp_id), "TestPoint")

            if all([source_graph_id, target_graph_id, source_node_type, target_node_type]):
                self.graph_service.add_relationship(
                    source_node_type, source_graph_id,
                    target_node_type, target_graph_id,
                    edge_data["relation"]
                )
        
        return {
            "knowledge_base_id": knowledge_base_id,
            "processed_nodes": len(nodes_to_upsert_in_milvus),
            "processed_edges": len(extracted_data.get("edges", []))
        }
