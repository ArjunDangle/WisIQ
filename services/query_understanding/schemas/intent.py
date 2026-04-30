# FILE: services/query_understanding/schemas/intent.py

from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class QueryIntent(str, Enum):
    COMMAND_LOOKUP = "command_lookup"       # e.g., "Give me the AT command for OTAA"
    CONCEPTUAL = "conceptual"               # e.g., "What is a LoRaWAN Class C node?"
    TROUBLESHOOTING = "troubleshooting"     # e.g., "My gateway is in a reboot loop"
    TOPOLOGY = "topology"                   # e.g., "Which firmware works with WisDuo?"

class QueryUnderstanding(BaseModel):
    intent: QueryIntent = Field(
        description="The rigid intent bucket for the user's query."
    )
    hardware_entities: List[str] = Field(
        description="List of specific hardware models, modules, or families mentioned. Normalize to lowercase with no spaces/hyphens (e.g., 'RAK 3172' -> 'rak3172'). If none are mentioned, return an empty list.",
        default_factory=list
    )