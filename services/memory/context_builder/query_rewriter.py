# FILE: services/memory/context_builder/query_rewriter.py

import os
from openai import AsyncOpenAI
from services.orchestration.state.state import AgentState

api_key = os.getenv("OPENROUTER_API_KEY")
client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

async def rewrite_query_node(state: AgentState) -> dict:
    """
    Looks at the conversation history and rewrites the latest user message 
    into a self-contained, standalone query that explicitly includes all context.
    """
    messages = state["messages"]
    latest_query = messages[-1].content

    # If it's the first message, there is no history to contextualize.
    if len(messages) <= 1:
        return {"standalone_query": latest_query}

    # Format history for the LLM
    history_text = ""
    for msg in messages[:-1]:  # Exclude the very last message
        role = "User" if msg.type == "human" else "AI"
        history_text += f"{role}: {msg.content}\n"

    system_prompt = f"""
    You are an expert query rewriting engine. 
    Look at the conversation history and the user's latest follow-up question.
    Rewrite the follow-up question into a SINGLE, standalone search query that includes all relevant hardware names, software names, or context from the history.
    DO NOT answer the question. ONLY output the rewritten query.
    If the question is already completely standalone, just output it exactly as is.

    === HISTORY ===
    {history_text}
    """

    response = await client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": latest_query}
        ],
        temperature=0.0
    )

    rewritten_query = response.choices[0].message.content.strip()
    return {"standalone_query": rewritten_query}