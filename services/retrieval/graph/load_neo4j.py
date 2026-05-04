# FILE: services/retrieval/graph/load_neo4j.py

import json
import asyncio
from pathlib import Path
from neo4j import AsyncGraphDatabase

# Resolve path automatically
PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRIPLETS_FILE = PROJECT_ROOT / "data" / "processed" / "graph_triplets.jsonl"

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "adminpassword")

async def load_deterministic_graph():
    if not TRIPLETS_FILE.exists():
        print(f"❌ Error: {TRIPLETS_FILE} not found. Run ingestion first.")
        return

    driver = AsyncGraphDatabase.driver(URI, auth=AUTH)
    print("🚀 Connecting to Neo4j to load deterministic facts...")
    
    triplets =[]
    with open(TRIPLETS_FILE, "r") as f:
        for line in f:
            triplets.append(json.loads(line))
            
    async with driver.session() as session:
        # Clear existing graph to ensure clean slate
        await session.run("MATCH (n) DETACH DELETE n")
        
        # Load relationships using standard Cypher (No APOC required)
        for t in triplets:
            # We construct a dynamic cypher string to use the variable relationship type
            # (Neo4j requires relationship types to be static in the query string)
            query = f"""
            MERGE (s:Entity {{id: $source}})
            MERGE (tgt:Entity {{id: $target}})
            MERGE (s)-[:{t['relation']}]->(tgt)
            """
            await session.run(query, source=t["source"], target=t["target"])
            
    print(f"✅ Successfully mapped {len(triplets)} deterministic rules into Neo4j.")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(load_deterministic_graph())