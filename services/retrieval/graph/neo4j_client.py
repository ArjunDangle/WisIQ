# FILE: services/retrieval/graph/neo4j_client.py

import os
from neo4j import AsyncGraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "adminpassword")

# Global driver to maintain connection pool
driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

async def get_graph_facts(entities: list) -> list:
    """
    Queries Neo4j for immediate relationships (1-hop) connected to the extracted entities.
    Returns a list of human-readable fact strings for the LLM.
    """
    if not entities:
        return[]

    # Normalize entities to lowercase
    normalized_entities = [e.lower() for e in entities]

    cypher_query = """
    MATCH (n)-[r]-(m)
    WHERE toLower(n.id) IN $entities
    RETURN n.id AS source, type(r) AS relation, m.id AS target
    LIMIT 20
    """
    
    facts =[]
    try:
        async with driver.session() as session:
            result = await session.run(cypher_query, entities=normalized_entities)
            records = await result.data()
            
            for record in records:
                facts.append(f"({record['source']}) - [{record['relation']}] -> ({record['target']})")
    except Exception as e:
        print(f"⚠️ Neo4j Warning: Failed to fetch facts: {e}")
            
    return facts