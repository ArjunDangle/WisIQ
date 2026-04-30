# FILE: services/query_understanding/extractors/intent_extractor.py

import os
from openai import AsyncOpenAI
from services.query_understanding.schemas.intent import QueryUnderstanding

# --- HARDENED API KEY VALIDATION ---
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("FATAL: OPENROUTER_API_KEY is not set in the environment. Please check your .env file.")
if "your-openrouter-key" in api_key:
    raise ValueError("FATAL: The default OPENROUTER_API_KEY is being used. Please replace it with your actual key.")
# --- END VALIDATION ---

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
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
    
    response = await client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "query_understanding",
                "schema": QueryUnderstanding.model_json_schema(),
                "strict": True
            }
        },
        temperature=0.0
    )
    
    result_str = response.choices[0].message.content
    return QueryUnderstanding.model_validate_json(result_str)