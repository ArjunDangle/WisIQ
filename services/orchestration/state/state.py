# FILE: services/orchestration/state/state.py

import operator
from typing import Annotated, Sequence, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    standalone_query: str
    intent: str
    extracted_hardware: List[str]
    graph_neighborhood: Dict[str, Any]
    
    # 🚨 NEW: Neo4j Structured Facts
    graph_facts: List[str]
    
    is_eol_flagged: bool
    retrieved_chunks: List[Dict[str, Any]]
    confidence_score: float
    circuit_breaker_tripped: bool