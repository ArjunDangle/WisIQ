# FILE: services/ingestion/schemas/graph.py

from pydantic import BaseModel, Field
from typing import List

class Triplet(BaseModel):
    source: str = Field(description="The primary entity (e.g., 'RAK7289v2', 'AT+JOIN')")
    relation: str = Field(description="The relationship action (e.g., 'RUNS_ON', 'REQUIRES', 'HAS_FEATURE', 'CONNECTS_TO')")
    target: str = Field(description="The target entity (e.g., 'WisGateOS 2', 'AppKey')")

class GraphExtraction(BaseModel):
    triplets: List[Triplet] = Field(description="List of factual relationships extracted from the text.")