# FILE: services/orchestration/nodes/fallback.py

from langchain_core.messages import AIMessage
from services.orchestration.state.state import AgentState

async def fallback_response(state: AgentState) -> dict:
    """
    Triggered when the Reranker Circuit Breaker fails. 
    Guarantees no hallucination by actively declining to answer.
    """
    reply = (
        "I do not have high enough confidence in the available documentation to answer this question accurately. "
        "Because this system operates under a strict zero-hallucination policy, I must decline to guess. "
        "Please check the official RAKwireless documentation directly or rephrase your query."
    )
    return {"messages":[AIMessage(content=reply)]}