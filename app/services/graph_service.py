from neo4j import GraphDatabase
from app.core.config import settings
from typing import List, Dict, Any, Tuple

class GraphService:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        print("Successfully connected to Neo4j.")

    def close(self):
        self._driver.close()
        print("Successfully disconnected from Neo4j.")

    def _execute_query(self, query, parameters=None):
        with self._driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def add_node(self, label: str, properties: dict):
        query = f"MERGE (n:{label} {{id: $props.id}}) SET n += $props RETURN n"
        result = self._execute_query(query, parameters={"props": properties})
        return result[0]['n'] if result else None

    def add_relationship(self, start_node_label: str, start_node_id: str,
                         end_node_label: str, end_node_id: str,
                         relationship_type: str):
        query = (
            f"MATCH (a:{start_node_label} {{id: $start_id}}), (b:{end_node_label} {{id: $end_id}}) "
            f"MERGE (a)-[:{relationship_type}]->(b)"
        )
        self._execute_query(query, parameters={"start_id": start_node_id, "end_id": end_node_id})

    def get_subgraph_by_ids(self, node_ids: List[str], depth: int = 2) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Retrieves a subgraph starting from a list of node IDs up to a certain depth.
        Returns a tuple of (nodes, relationships).
        """
        query = """
        MATCH (n) WHERE n.id IN $node_ids
        CALL apoc.path.subgraphAll(n, {
            maxLevel: $depth
        })
        YIELD nodes, relationships
        UNWIND nodes as node
        UNWIND relationships as rel
        WITH collect(DISTINCT node) as distinct_nodes, collect(DISTINCT rel) as distinct_rels
        RETURN distinct_nodes, distinct_rels
        """
        
        result = self._execute_query(query, parameters={"node_ids": node_ids, "depth": depth})
        
        if not result or not result[0]['distinct_nodes']:
            return [], []

        raw_nodes = result[0]['distinct_nodes']
        raw_rels = result[0]['distinct_rels']

        nodes = [
            {
                "id": node['id'],
                "labels": list(node.labels),
                "properties": dict(node)
            } for node in raw_nodes
        ]
        
        relationships = [
            {
                "source": rel.start_node['id'],
                "target": rel.end_node['id'],
                "type": rel.type,
                "properties": dict(rel)
            } for rel in raw_rels
        ]

        return nodes, relationships
