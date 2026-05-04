# FILE: services/orchestration/nodes/graph_traversal.py

from typing import Dict, Any
from services.orchestration.state.state import AgentState
from app.dependencies.db import prisma_client
from services.retrieval.graph.neo4j_client import get_graph_facts

async def extract_graph_neighborhood(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Node: 
    1. Validates SKU/EOL Taxonomy against PostgreSQL.
    2. Extracts mapped knowledge facts from Neo4j (True GraphRAG).
    """
    hardware_list = state.get("extracted_hardware",[])
    
    neighborhood = {}
    is_eol_flagged = False
    
    # If no hardware detected, return empty context
    if not hardware_list:
        return {
            "graph_neighborhood": neighborhood,
            "graph_facts":[],
            "is_eol_flagged": is_eol_flagged
        }

    # --- 1. POSTGRES: Strict Taxonomy & EOL Guardrails ---
    for hw_code in hardware_list:
        # Utilize the global Prisma client
        record = await prisma_client.productcode.find_unique(
            where={"code": hw_code},
            include={"family": True} 
        )
        
        if record:
            neighborhood[hw_code] = {
                "status": "recognized",
                "family": record.family.name if record.family else "unknown",
                "is_eol": record.is_eol
            }
            if record.is_eol:
                is_eol_flagged = True
        else:
            neighborhood[hw_code] = {
                "status": "unrecognized",
                "family": "none",
                "is_eol": False
            }

    # --- 2. NEO4J: GraphRAG Knowledge Traversals ---
    # Fetch factual triplets based on the valid hardware recognized
    valid_hardware = [hw for hw, info in neighborhood.items() if info["status"] == "recognized"]
    graph_facts = await get_graph_facts(valid_hardware)

    return {
        "graph_neighborhood": neighborhood,
        "graph_facts": graph_facts, # Inject Neo4j facts into State
        "is_eol_flagged": is_eol_flagged
    }