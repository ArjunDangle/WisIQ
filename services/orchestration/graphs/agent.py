# FILE: services/orchestration/graphs/agent.py

from langgraph.graph import StateGraph, START, END
from services.orchestration.state.state import AgentState
from services.memory.context_builder.query_rewriter import rewrite_query_node
from services.query_understanding.extractors.intent_extractor import analyze_query
from services.orchestration.nodes.graph_traversal import extract_graph_neighborhood
from services.retrieval.qdrant.search import retrieve_context
from services.orchestration.nodes.rerank import rerank_context
from services.orchestration.nodes.generator import generate_response
from services.orchestration.nodes.fallback import fallback_response

async def extract_intent_node(state: AgentState) -> dict:
    """
    Extracts intent and hardware from the NEW, fully-contextualized standalone query.
    Because the rewriter injects the hardware context automatically, we no longer 
    need brittle logic to "carry over" old hardware states.
    """
    # 🚨 CHANGE: Analyze the rewritten query, not the raw user message
    target_query = state.get("standalone_query", state["messages"][-1].content)
    
    understanding = await analyze_query(target_query)
    
    return {
        "intent": understanding.intent.value,
        "extracted_hardware": understanding.hardware_entities
    }

def should_generate(state: AgentState) -> str:
    if state.get("circuit_breaker_tripped"):
        return "fallback"
    else:
        return "generate"

def build_agent_graph():
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("extract_intent", extract_intent_node)
    workflow.add_node("graph_traversal", extract_graph_neighborhood)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("rerank_context", rerank_context)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("fallback_response", fallback_response)

    # 🚨 CHANGE: Insert 'rewrite_query' at the very beginning of the flow
    workflow.add_edge(START, "rewrite_query")
    workflow.add_edge("rewrite_query", "extract_intent")
    workflow.add_edge("extract_intent", "graph_traversal")
    workflow.add_edge("graph_traversal", "retrieve_context")
    workflow.add_edge("retrieve_context", "rerank_context")

    workflow.add_conditional_edges(
        "rerank_context",
        should_generate,
        {
            "generate": "generate_response",
            "fallback": "fallback_response"
        }
    )
    
    workflow.add_edge("generate_response", END)
    workflow.add_edge("fallback_response", END)

    return workflow