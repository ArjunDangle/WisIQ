# FILE: services/ingestion/pipelines/ingest.py

import os
import sys
import time
import json
from pathlib import Path
from tqdm import tqdm
import logging

# Dynamically resolve project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from services.ingestion.schemas.payload import ProcessedPayload, DocumentLevel, ChunkLevel, Vectors
from services.ingestion.parsers.markdown_parser import parse_markdown_file
from services.ingestion.chunking.heuristics import classify_content
from services.ingestion.embeddings.bge_m3 import DualEmbeddingModel
from services.ingestion.parsers.deterministic_graph import extract_deterministic_triplets

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Production Paths
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "product-categories"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Batch Size optimized for Apple M4
BATCH_SIZE = 16 

def run_full_ingestion():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_DIR / "knowledge_base.jsonl"
    graph_file = PROCESSED_DIR / "graph_triplets.jsonl"
    
    md_files = list(RAW_DIR.rglob("*.md"))
    logging.info(f"Discovered {len(md_files)} Markdown files across the entire knowledge base.")

    if not md_files:
        logging.error(f"No markdown files found in {RAW_DIR}.")
        return

    chunk_queue = []
    global_triplets =[] # 🚨 NEW: Store relationships for Neo4j

    logging.info("--- PHASE 1: Parsing, Chunking & Triplet Extraction ---")
    for file_path in tqdm(md_files, desc="Parsing MD Files", unit="file"):
        doc_meta, chunks = parse_markdown_file(str(file_path))
        
        if not doc_meta:
            continue 
            
        for chunk in chunks:
            # 🚨 NEW: Extract and collect Deterministic Graph Triplets
            triplets = extract_deterministic_triplets(doc_meta, chunk["text"])
            global_triplets.extend(triplets)
            
            chunk_queue.append({
                "doc_meta": doc_meta,
                "text": chunk["text"],
                "header_path": chunk["header_path"],
                "chunk_index": chunk["chunk_index"],
                "content_type": classify_content(chunk["text"])
            })

    total_chunks = len(chunk_queue)
    logging.info(f"Extraction complete. Produced {total_chunks} highly-contextual chunks.")

    # 🚨 NEW: Save purely factual, deterministic triplets to disk
    # Deduplicate facts (e.g. only need to know RAK7289v2 runs WisGateOS once)
    unique_triplets = {f"{t['source']}|{t['relation']}|{t['target']}": t for t in global_triplets}.values()
    with open(graph_file, 'w', encoding='utf-8') as f:
        for t in unique_triplets:
            f.write(json.dumps(t) + "\n")
    logging.info(f"✅ Generated {len(unique_triplets)} Deterministic Knowledge Graph Triplets.")

    logging.info("--- PHASE 2: Dual-Vector Generation & Validation ---")
    model = DualEmbeddingModel()

    with open(output_file, 'w', encoding='utf-8') as f:
        for i in tqdm(range(0, total_chunks, BATCH_SIZE), desc="Embedding & Saving", unit="batch"):
            batch = chunk_queue[i : i + BATCH_SIZE]
            batch_texts = [b["text"] for b in batch]
            
            # Generate Vectors
            batch_vectors = model.encode_batch(batch_texts)
            
            # Assemble & Validate
            for j, item in enumerate(batch):
                try:
                    payload = ProcessedPayload(
                        document_level=DocumentLevel(**item["doc_meta"]),
                        chunk_level=ChunkLevel(
                            header_path=item["header_path"],
                            content_type=item["content_type"],
                            chunk_index=item["chunk_index"]
                        ),
                        vectors=Vectors(
                            dense=batch_vectors[j]["dense"],
                            sparse=batch_vectors[j]["sparse"]
                        ),
                        text=item["text"]
                    )
                    f.write(payload.model_dump_json() + "\n")
                except Exception as e:
                    logging.error(f"Schema Validation failed for chunk '{item['header_path']}': {e}")
            
            time.sleep(0.01)

    logging.info(f"✅ Full Pipeline Complete! Qdrant and Neo4j files ready.")

if __name__ == "__main__":
    run_full_ingestion()