# FILE: app/routes/chat.py

import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from services.orchestration.graphs.agent import build_agent_graph

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    intent_detected: str
    hardware_detected: list

# Standard Redis URI matching our docker-compose configuration
REDIS_URI = "redis://127.0.0.1:6379/0"

@router.post("/query", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # 1. Use the official async context manager to safely connect to Redis.
        # This ensures the connection is properly opened and closed for each API call.
        async with AsyncRedisSaver.from_conn_string(REDIS_URI) as checkpointer:
            
            # Essential: Initialize the Redis indices for the LangGraph checkpointer.
            # This is the core part of the fix to ensure the checkpointer can operate.
            await checkpointer.asetup()
            
            # 2. Get the workflow and compile with the connected checkpointer
            workflow = build_agent_graph()
            agent = workflow.compile(checkpointer=checkpointer)
            
            # 3. Setup the LangGraph config (thread_id dictates the conversation session)
            config = {"configurable": {"thread_id": request.session_id}}
            
            # 4. Inject the new human message into the graph
            inputs = {"messages": [HumanMessage(content=request.message)]}
            
            # 5. Execute the Graph asynchronously
            final_state = await agent.ainvoke(inputs, config=config)
            
            # 6. Extract the results from the final state
            reply = final_state["messages"][-1].content
            intent = final_state.get("intent", "unknown")
            hardware = final_state.get("extracted_hardware", [])
            
            return ChatResponse(
                reply=reply,
                intent_detected=intent,
                hardware_detected=hardware
            )
            
    except Exception as e:
        # Print the full error traceback to the FastAPI console for easier debugging
        print("--- AGENT ERROR ---")
        traceback.print_exc()
        print("--- END TRACE ---")
        raise HTTPException(status_code=500, detail=str(e))