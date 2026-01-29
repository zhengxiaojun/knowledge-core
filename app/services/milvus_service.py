import os
import uuid
from typing import List, Dict
from openai import OpenAI
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
from app.core.config import settings

class MilvusService:
    def __init__(self, alias="default"):
        self.alias = alias
        self.collection_name = "test_knowledge_vectors"
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        try:
            connections.connect(
                alias=self.alias,
                uri=settings.milvus_uri,
                token=settings.milvus_token,
            )
            print("Successfully connected to Milvus.")
            self._init_collection()
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            raise

    def _init_collection(self):
        if not utility.has_collection(self.collection_name, using=self.alias):
            print(f"Collection '{self.collection_name}' not found. Creating a new one.")
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="graph_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="knowledge_base_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="confidence", dtype=DataType.FLOAT),
            ]
            schema = CollectionSchema(fields, "Test Knowledge Vectors Collection")
            self.collection = Collection(self.collection_name, schema, using=self.alias)
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 200},
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
            print("Collection and index created successfully.")
        else:
            self.collection = Collection(self.collection_name, using=self.alias)
            print(f"Collection '{self.collection_name}' already exists.")

        self.collection.load()
        print("Collection loaded into memory.")

    def _get_embedding(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            input=[text],
            model=self.embedding_model
        )
        return response.data[0].embedding

    def upsert(self, data: List[Dict]) -> Dict:
        if not data:
            return {"status": "No data provided", "inserted_count": 0}

        entities = {
            "id": [], "embedding": [], "content": [], "type": [],
            "graph_id": [], "knowledge_base_id": [], "confidence": [],
        }

        for item in data:
            entities["id"].append(item.get("id", str(uuid.uuid4())))
            entities["embedding"].append(self._get_embedding(item["content"]))
            entities["content"].append(item["content"])
            entities["type"].append(item["type"])
            entities["graph_id"].append(item["graph_id"])
            entities["knowledge_base_id"].append(item["knowledge_base_id"])
            entities["confidence"].append(item.get("confidence", 1.0))

        try:
            result = self.collection.insert([
                entities["id"], entities["embedding"], entities["content"],
                entities["type"], entities["graph_id"], entities["knowledge_base_id"],
                entities["confidence"],
            ])
            self.collection.flush()
            return {"status": "success", "insert_result": result}
        except Exception as e:
            print(f"Failed to upsert data to Milvus: {e}")
            raise

    def search(self, query_text: str, top_k: int = 10) -> List[Dict]:
        query_embedding = self._get_embedding(query_text)
        
        search_params = {"metric_type": "COSINE", "params": {"ef": 10}}
        
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["id", "content", "type", "graph_id", "knowledge_base_id", "confidence"]
        )
        
        formatted_results = []
        for hit in results[0]:
            entity_data = {
                "id": hit.entity.get("id"),
                "content": hit.entity.get("content"),
                "type": hit.entity.get("type"),
                "graph_id": hit.entity.get("graph_id"),
                "knowledge_base_id": hit.entity.get("knowledge_base_id"),
                "confidence": hit.entity.get("confidence"),
                "score": hit.distance,
            }
            formatted_results.append(entity_data)
        return formatted_results

    def close(self):
        try:
            connections.disconnect(self.alias)
            print("Successfully disconnected from Milvus.")
        except Exception as e:
            print(f"Failed to disconnect from Milvus: {e}")
