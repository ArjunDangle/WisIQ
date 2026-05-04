# FILE: services/orchestration/nodes/generator.py

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from services.orchestration.state.state import AgentState

# LangChain ChatOpenAI Wrapper
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "your-openrouter-key"),
    model="meta-llama/llama-3.1-70b-instruct",
    temperature=0.1
)

async def generate_response(state: AgentState) -> dict:
    """
    LangGraph Node: Synthesizes Retrieved Context (Qdrant), Guardrails (Postgres), 
    and Topologies (Neo4j) into the final answer.
    """
    retrieved_chunks = state.get("retrieved_chunks",[])
    neighborhood = state.get("graph_neighborhood", {})
    graph_facts = state.get("graph_facts",[]) # 🚨 Retrieve Neo4j facts
    is_eol_flagged = state.get("is_eol_flagged", False)

    # 1. Build Ground-Truth Context String (Qdrant)
    context_str = ""
    for chunk in retrieved_chunks:
        context_str += f"---[{', '.join(chunk['product_codes'])}] {chunk['header_path']} ---\n{chunk['content']}\n\n"

    # 2. Build Graph Fact String (Neo4j)
    graph_fact_str = "\n".join(graph_facts) if graph_facts else "No direct hardware relationships mapped."

    # 3. Build Guardrail Directives (Postgres)
    unrecognized_hardware =[hw for hw, info in neighborhood.items() if info["status"] == "unrecognized"]
    guardrail_instructions = ""
    
    if unrecognized_hardware:
        guardrail_instructions += f"\n🚨 CRITICAL: The user asked about {', '.join(unrecognized_hardware)}. You MUST state that you do not recognize this hardware in the product catalog before answering anything else.\n"
        
    if is_eol_flagged:
        guardrail_instructions += "\n🚨 CRITICAL: One or more of the requested products are End-of-Life (EOL). You MUST begin your response with a clear warning that the product is End-of-Life and no longer actively supported.\n"

    # 4. Construct System Prompt
    system_prompt = f"""
You are an elite, highly precise technical support AI for IoT hardware (WisGate, WisDuo, etc.).
Your primary mandate is ZERO HALLUCINATION. 
You will answer the user's question using ONLY the provided Graph Facts and Retrieved Context below. 
If the context does not contain the answer, you must decline to answer and state that the documentation does not cover this.
Do not invent AT commands or firmware versions. Do not guess.

{guardrail_instructions}

=== GRAPH KNOWLEDGE FACTS (Entity Relationships) ===
{graph_fact_str}
==================================================

=== RETRIEVED CONTEXT (Documentation Chunks) ===
{context_str if context_str else "No relevant context found in the database."}
================================================
"""

    # 5. Construct Message Payload
    messages = [SystemMessage(content=system_prompt)]
    recent_history = state["messages"][-3:]
    messages.extend(recent_history)

    # 6. Generate Response
    response = await llm.ainvoke(messages)
    
    return {"messages": [response]}