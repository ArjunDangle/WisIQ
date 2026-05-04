# FILE: app/routes/chat.py

import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from services.orchestration.graphs.agent import build_agent_graph

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

# Standard Redis URI matching our docker-compose configuration
REDIS_URI = "redis://127.0.0.1:6379/0"

@router.post("/query")
async def chat_endpoint(request: ChatRequest):
    
    # 🚨 UPDATE: We define an async generator to yield Server-Sent Events (SSE)
    async def event_generator():
        try:
            async with AsyncRedisSaver.from_conn_string(REDIS_URI) as checkpointer:
                await checkpointer.asetup()
                
                workflow = build_agent_graph()
                agent = workflow.compile(checkpointer=checkpointer)
                
                config = {"configurable": {"thread_id": request.session_id}}
                inputs = {"messages": [HumanMessage(content=request.message)]}
                
                # Use version="v2" of LangGraph's event streaming API
                async for event in agent.astream_events(inputs, config=config, version="v2"):
                    kind = event["event"]
                    tags = event.get("tags", [])
                    name = event.get("name", "")

                    # 1. EMIT METADATA EARLY: Capture the intent and hardware as soon as extraction finishes
                    if kind == "on_chain_end" and name == "extract_intent":
                        node_output = event["data"].get("output", {})
                        if isinstance(node_output, dict):
                            meta = {
                                "type": "metadata",
                                "intent_detected": node_output.get("intent", "unknown"),
                                "hardware_detected": node_output.get("extracted_hardware", [])
                            }
                            # Yield SSE formatted data
                            yield f"data: {json.dumps(meta)}\n\n"

                    # 2. EMIT TOKENS: Stream the final answer token-by-token
                    # We check for our custom tag to ensure we don't stream the query rewriter's thoughts
                    elif kind == "on_chat_model_stream" and "final_generator" in tags:
                        content = event["data"]["chunk"].content
                        if content:
                            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

                    # 3. EMIT FALLBACK: If the circuit breaker trips, stream the fallback message
                    elif kind == "on_chain_end" and name == "fallback_response":
                        node_output = event["data"].get("output", {})
                        if isinstance(node_output, dict) and "messages" in node_output:
                            fallback_msg = node_output["messages"][0].content
                            yield f"data: {json.dumps({'type': 'token', 'content': fallback_msg})}\n\n"

                # 4. EMIT END EVENT: Tell the frontend the stream is officially closed
                yield f"data: {json.dumps({'type': 'end'})}\n\n"

        except Exception as e:
            print("--- AGENT ERROR ---")
            traceback.print_exc()
            print("--- END TRACE ---")
            # Ensure the frontend fails gracefully rather than hanging indefinitely
            error_msg = {"type": "error", "message": "An internal system error occurred while generating the response."}
            yield f"data: {json.dumps(error_msg)}\n\n"

    # Return as a text/event-stream media type
    return StreamingResponse(event_generator(), media_type="text/event-stream")