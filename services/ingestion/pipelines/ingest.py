import os
import sys
import time
from pathlib import Path
from tqdm import tqdm
import logging

# Dynamically resolve project root to ensure imports and paths work from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from services.ingestion.schemas.payload import ProcessedPayload, DocumentLevel, ChunkLevel, Vectors
from services.ingestion.parsers.markdown_parser import parse_markdown_file
from services.ingestion.chunking.heuristics import classify_content
from services.ingestion.embeddings.bge_m3 import DualEmbeddingModel

# Set up logging to output cleanly alongside tqdm progress bars
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Production Paths
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "product-categories"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# M4 Memory Protection: 16 is the sweet spot. Fast, but won't freeze macOS.
BATCH_SIZE = 16 

def run_full_ingestion():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PROCESSED_DIR / "knowledge_base.jsonl"
    
    # 1. Gather all MD files across the entire directory structure
    md_files = list(RAW_DIR.rglob("*.md"))
    logging.info(f"Discovered {len(md_files)} Markdown files across the entire knowledge base.")

    if not md_files:
        logging.error(f"No markdown files found in {RAW_DIR}. Please check your paths.")
        return

    chunk_queue =[]

    # 2. Phase 1: Parse Frontmatter, Classify, and Slice into hierarchical chunks
    logging.info("--- PHASE 1: Parsing & Chunking ---")
    for file_path in tqdm(md_files, desc="Parsing MD Files", unit="file"):
        doc_meta, chunks = parse_markdown_file(str(file_path))
        
        if not doc_meta:
            continue # Skip files without frontmatter or unreadable files
            
        for chunk in chunks:
            chunk_queue.append({
                "doc_meta": doc_meta,
                "text": chunk["text"],
                "header_path": chunk["header_path"],
                "chunk_index": chunk["chunk_index"],
                "content_type": classify_content(chunk["text"])
            })

    total_chunks = len(chunk_queue)
    logging.info(f"Extraction complete. Produced {total_chunks} highly-contextual chunks.")
    logging.info("--- PHASE 2: Dual-Vector Generation & Validation ---")

    # 3. Initialize Model (Loads BGE-M3 into Apple M4 Unified Memory)
    model = DualEmbeddingModel()

    # 4. Batch Vectorize, Validate via Pydantic, and write to JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        # We iterate over the chunks in manageable batches
        for i in tqdm(range(0, total_chunks, BATCH_SIZE), desc="Embedding & Saving", unit="batch"):
            batch = chunk_queue[i : i + BATCH_SIZE]
            batch_texts = [b["text"] for b in batch]
            
            # Generate Vectors via M4 Compute
            batch_vectors = model.encode_batch(batch_texts)
            
            # Assemble & Validate Payload
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
                    
                    # Write strictly validated payload to disk
                    f.write(payload.model_dump_json() + "\n")
                    
                except Exception as e:
                    logging.error(f"Schema Validation failed for chunk '{item['header_path']}': {e}")
            
            # M4 OS Thread Scheduler protection - Prevents the laptop from locking up
            time.sleep(0.01)

    logging.info(f"✅ Full Pipeline Complete! {total_chunks} valid chunks embedded and saved.")
    logging.info(f"📁 Output File: {output_file}")

if __name__ == "__main__":
    run_full_ingestion()