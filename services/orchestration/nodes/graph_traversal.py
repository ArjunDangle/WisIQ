# FILE: services/orchestration/nodes/graph_traversal.py

from prisma import Prisma
from typing import Dict, Any
from services.orchestration.state.state import AgentState

async def extract_graph_neighborhood(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph Node: Takes extracted hardware, queries Postgres (our Knowledge Graph),
    and builds a 'Graph Neighborhood' representing the strict reality of the hardware.
    """
    hardware_list = state.get("extracted_hardware",[])
    
    neighborhood = {}
    is_eol_flagged = False
    
    # If the LLM didn't detect any hardware, return empty graph context
    if not hardware_list:
        return {
            "graph_neighborhood": neighborhood,
            "is_eol_flagged": is_eol_flagged
        }

    # Initialize Prisma (Connecting if not already connected by FastAPI)
    db = Prisma()
    if not db.is_connected():
        await db.connect()

    for hw_code in hardware_list:
        # Traverse the Graph: ProductCode -> ProductFamily
        record = await db.productcode.find_unique(
            where={"code": hw_code},
            include={"family": True} # Follow the edge to the parent node
        )
        
        if record:
            neighborhood[hw_code] = {
                "status": "recognized",
                "family": record.family.name if record.family else "unknown",
                "is_eol": record.is_eol
            }
            # If ANY hardware in the query is EOL, trip the circuit breaker
            if record.is_eol:
                is_eol_flagged = True
        else:
            # The LLM hallucinated a product name, or the user mistyped it
            neighborhood[hw_code] = {
                "status": "unrecognized",
                "family": "none",
                "is_eol": False
            }

    return {
        # This dictionary is merged back into our global LangGraph AgentState
        "graph_neighborhood": neighborhood,
        "is_eol_flagged": is_eol_flagged
    }