# FILE: services/orchestration/nodes/generator.py

import os
from openai import AsyncOpenAI
from langchain_core.messages import AIMessage
from services.orchestration.state.state import AgentState

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "your-openrouter-key")
)

async def generate_response(state: AgentState) -> dict:
    """
    LangGraph Node: Synthesizes the retrieved context and graph neighborhood into the final answer.
    Enforces Zero-Hallucination and EOL guardrails.
    """
    user_message = state["messages"][-1].content
    retrieved_chunks = state.get("retrieved_chunks",[])
    neighborhood = state.get("graph_neighborhood", {})
    is_eol_flagged = state.get("is_eol_flagged", False)

    # 1. Build the Ground-Truth Context String
    context_str = ""
    for chunk in retrieved_chunks:
        # We inject the exact header path so the LLM knows the hierarchical context
        context_str += f"--- [{', '.join(chunk['product_codes'])}] {chunk['header_path']} ---\n"
        context_str += f"{chunk['content']}\n\n"

    # 2. Build the Guardrail Directives based on Postgres Graph Traversal
    unrecognized_hardware = []
    recognized_hardware =[]
    
    for hw, info in neighborhood.items():
        if info["status"] == "unrecognized":
            unrecognized_hardware.append(hw)
        elif info["status"] == "recognized":
            recognized_hardware.append(hw)

    guardrail_instructions = ""
    
    if unrecognized_hardware:
        guardrail_instructions += f"\n🚨 CRITICAL: The user asked about {', '.join(unrecognized_hardware)}. You MUST state that you do not recognize this hardware in the product catalog before answering anything else.\n"
        
    if is_eol_flagged:
        guardrail_instructions += "\n🚨 CRITICAL: One or more of the requested products are End-of-Life (EOL). You MUST begin your response with a clear warning that the product is End-of-Life and no longer actively supported.\n"

    # 3. Construct the System Prompt
    system_prompt = f"""
You are an elite, highly precise technical support AI for IoT hardware (WisGate, WisDuo, etc.).
Your primary mandate is ZERO HALLUCINATION. 
You will answer the user's question using ONLY the provided 'Retrieved Context' below. 
If the context does not contain the answer, you must decline to answer and state that the documentation does not cover this.
Do not invent AT commands or firmware versions. Do not guess.

{guardrail_instructions}

=== RETRIEVED CONTEXT ===
{context_str if context_str else "No relevant context found in the database."}
=========================
"""

    # 4. Generate the Response using a powerful reasoning model (e.g., Llama 3 70B or GPT-4o)
    response = await client.chat.completions.create(
        model="meta-llama/llama-3.1-70b-instruct", 
        messages=[
            {"role": "system", "content": system_prompt},
            # Pass the recent conversational history for context
            *[{"role": "user" if m.type == "human" else "assistant", "content": m.content} for m in state["messages"][-3:]]
        ],
        temperature=0.1 # Keep it highly deterministic
    )
    
    final_answer = response.choices[0].message.content
    
    # 5. Return the new message to append to the LangGraph state
    return {"messages":[AIMessage(content=final_answer)]}