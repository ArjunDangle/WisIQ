# FILE: services/query_understanding/extractors/intent_extractor.py

import os
from langchain_openai import ChatOpenAI
from services.query_understanding.schemas.intent import QueryUnderstanding

# --- HARDENED API KEY VALIDATION ---
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("FATAL: OPENROUTER_API_KEY is not set in the environment. Please check your .env file.")
if "your-openrouter-key" in api_key:
    raise ValueError("FATAL: The default OPENROUTER_API_KEY is being used. Please replace it with your actual key.")
# --- END VALIDATION ---

# 🚨 FIX B: Adopt LangChain ChatOpenAI wrapper with structured output capabilities
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    model="meta-llama/llama-3.1-8b-instruct",
    temperature=0.0
)

# Force the LLM to output our exact Pydantic schema
structured_llm = llm.with_structured_output(
    QueryUnderstanding, 
    method="json_schema", 
    strict=True
)

async def analyze_query(query: str) -> QueryUnderstanding:
    system_prompt = """
    You are a highly precise taxonomy extraction engine for IoT hardware documentation.
    Your SOLE job is to analyze the user's query, classify its intent, and extract mentioned hardware entities.

    ## Rules for Intent Classification ##
    - 'conceptual': Used for questions like "What is X?", "Explain Y", overviews, specs, or general questions.
    - 'command_lookup': Used ONLY when the user explicitly asks for code, syntax, scripts, or AT Commands.
    - 'troubleshooting': Used for errors, bugs, or "how to fix" questions.

    ## Rules for Hardware Extraction ##
    - Hardware entities are specific model names (e.g., 'rak3172', 'rak7289cv2', 'rak10701-plus').
    - Hardware entities can be product families (e.g., 'wisgate', 'wisduo').
    - CRITICAL: DO NOT extract technical concepts, protocols, or commands as hardware (e.g., 'lorawan', 'otaa', 'abp' are NOT hardware).

    Normalize all extracted hardware names to lowercase without spaces or hyphens.
    """
    
    messages =[
        ("system", system_prompt),
        ("human", query)
    ]
    
    result = await structured_llm.ainvoke(messages)
    return result