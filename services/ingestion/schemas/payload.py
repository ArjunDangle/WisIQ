from pydantic import BaseModel
from typing import List, Dict

class DocumentLevel(BaseModel):
    url_slug: str
    product_category: str
    product_codes: List[str]
    doc_type: str
    tags: List[str]
    keywords: List[str]

class ChunkLevel(BaseModel):
    header_path: str
    content_type: str
    chunk_index: int

class Vectors(BaseModel):
    dense: List[float]
    sparse: Dict[str, float]

class ProcessedPayload(BaseModel):
    document_level: DocumentLevel
    chunk_level: ChunkLevel
    vectors: Vectors
    text: str