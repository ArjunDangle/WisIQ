# FILE: services/retrieval/qdrant/init_and_load.py

import json
import uuid
import zlib
from pathlib import Path
from qdrant_client import QdrantClient, models
from tqdm import tqdm

# Dynamically resolve project root
BASE_DIR = Path(__file__).resolve().parents[3]
JSONL_PATH = BASE_DIR / "data" / "processed" / "knowledge_base.jsonl"

QDRANT_HOST = "127.0.0.1"
QDRANT_PORT = 6333
COLLECTION_NAME = "iot_docs"

def safe_sparse_index(key: str) -> int:
    """
    Qdrant sparse vectors require integer indices.
    If the BGE-M3 tokenizer outputs string token IDs, convert them.
    If it outputs raw words, convert them to a stable uint32 hash.
    """
    try:
        return int(key)
    except ValueError:
        return zlib.crc32(key.encode('utf-8'))

def init_and_load_qdrant():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # 1. Recreate the Collection (Ensures a clean slate)
    print(f"🛠️  Initializing Qdrant Collection: {COLLECTION_NAME}...")
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        # Dense Vector Config (1024 dims for BGE-M3)
        vectors_config={
            "dense": models.VectorParams(
                size=1024, 
                distance=models.Distance.COSINE
            )
        },
        # Sparse Vector Config (Lexical/Keyword matching)
        sparse_vectors_config={
            "sparse": models.SparseVectorParams()
        }
    )

    # 2. Create Payload Indexes for High-Speed Filtering
    print("⚡ Creating Payload Indexes for strict deterministic routing...")
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="document_level.product_codes",
        field_schema=models.PayloadSchemaType.KEYWORD
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="chunk_level.content_type",
        field_schema=models.PayloadSchemaType.KEYWORD
    )

    # 3. Read and Upload Data
    print(f"🚀 Loading Data from {JSONL_PATH}...")
    points =[]
    
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Processing JSONL"):
            if not line.strip(): continue
            
            item = json.loads(line)
            
            # Format Sparse Vectors for Qdrant
            sparse_dict = item["vectors"]["sparse"]
            indices = []
            values =[]
            for k, v in sparse_dict.items():
                indices.append(safe_sparse_index(k))
                values.append(float(v))
                
            # Create the Point Payload
            point_id = uuid.uuid4().hex
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "dense": item["vectors"]["dense"],
                        "sparse": models.SparseVector(
                            indices=indices,
                            values=values
                        )
                    },
                    # We store the full JSON (minus the huge vectors) as the searchable payload
                    payload={
                        "document_level": item["document_level"],
                        "chunk_level": item["chunk_level"],
                        "text": item["text"]
                    }
                )
            )

    # 4. Batch Upload
    print(f"💾 Uploading {len(points)} chunks to Qdrant...")
    batch_size = 250
    for i in tqdm(range(0, len(points), batch_size), desc="Uploading Batches"):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[i : i + batch_size]
        )

    print("✅ Phase 2 Complete! Vector database is locked and loaded.")

if __name__ == "__main__":
    init_and_load_qdrant()