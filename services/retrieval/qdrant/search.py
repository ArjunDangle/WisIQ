# FILE: services/retrieval/qdrant/search.py
# (Only the top part is modified to use standalone_query, the rest remains the same)

import zlib
import logging
from qdrant_client import QdrantClient, models
from services.orchestration.state.state import AgentState
from services.ingestion.embeddings.bge_m3 import DualEmbeddingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QDRANT_HOST = "127.0.0.1"
QDRANT_PORT = 6333
COLLECTION_NAME = "iot_docs"

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedder = DualEmbeddingModel()

def safe_sparse_index(key: str) -> int:
    try: return int(key)
    except ValueError: return zlib.crc32(key.encode('utf-8'))

async def retrieve_context(state: AgentState) -> dict:
    # 🚨 CHANGE: Use the optimized, standalone query for the vector search
    search_query = state.get("standalone_query", state["messages"][-1].content)
    neighborhood = state.get("graph_neighborhood", {})

    must_conditions =[]
    valid_hardware =[hw for hw, info in neighborhood.items() if info.get("status") == "recognized"]
    if valid_hardware:
        must_conditions.append(models.FieldCondition(
            key="document_level.product_codes", 
            match=models.MatchAny(any=valid_hardware)
        ))
        
    query_filter = models.Filter(must=must_conditions) if must_conditions else None
    
    # Encode the highly contextualized query
    query_vectors = embedder.encode_batch([search_query])[0]
    sparse_indices = [safe_sparse_index(k) for k in query_vectors["sparse"].keys()]
    sparse_values = [float(v) for v in query_vectors["sparse"].values()]

    FETCH_LIMIT = 15

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(query=models.SparseVector(indices=sparse_indices, values=sparse_values), using="sparse", limit=FETCH_LIMIT),
            models.Prefetch(query=query_vectors["dense"], using="dense", limit=FETCH_LIMIT)
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=query_filter,
        limit=FETCH_LIMIT 
    )

    retrieved_chunks =[]
    for point in results.points:
        retrieved_chunks.append({
            "header_path": point.payload["chunk_level"]["header_path"],
            "product_codes": point.payload["document_level"]["product_codes"],
            "content": point.payload["text"],
            "qdrant_rrf_score": point.score
        })
    
    logger.info(f"\n🔍 [QDRANT] Retrieved {len(retrieved_chunks)} chunks using Query: '{search_query}'")
    return {"retrieved_chunks": retrieved_chunks}