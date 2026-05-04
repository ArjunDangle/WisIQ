# FILE: services/orchestration/nodes/rerank.py

import logging
from services.orchestration.state.state import AgentState
from services.retrieval.reranker.cross_encoder_model import RerankerModel

logger = logging.getLogger(__name__)
reranker = RerankerModel()

# The Confidence Threshold: Adjust this to be more or less strict.
# 0.30 is a solid baseline for the BGE-Reranker-Base with Sigmoid activation.
CONFIDENCE_THRESHOLD = 0.30 

async def rerank_context(state: AgentState) -> dict:
    user_query = state["messages"][-1].content
    chunks = state.get("retrieved_chunks", [])

    if not chunks:
        logger.warning("\n⚠️ [CIRCUIT BREAKER] TRIPPED! Qdrant returned 0 chunks.")
        return {"circuit_breaker_tripped": True, "confidence_score": 0.0}

    # 1. Pair the user's query with every chunk of text for Cross-Encoding
    pairs = [[user_query, chunk["content"]] for chunk in chunks]
    
    # 2. Score them using Apple Silicon (MPS)
    scores = reranker.predict(pairs)

    # 3. Attach scores and sort highest to lowest
    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[i])

    ranked_chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
    
    # 4. Keep only the absolute best Top 5 to pass to the LLM
    top_chunks = ranked_chunks[:5] 
    best_score = top_chunks[0]["rerank_score"] if top_chunks else 0.0
    
    # 5. Evaluate the Circuit Breaker
    circuit_breaker = best_score < CONFIDENCE_THRESHOLD

    # --- LOGGING FOR TERMINAL OBSERVABILITY ---
    logger.info(f"⚖️  [RERANKER] Rescored {len(chunks)} chunks.")
    if circuit_breaker:
        logger.warning(f"🚨 [CIRCUIT BREAKER] TRIPPED! Top score {best_score:.4f} is below threshold {CONFIDENCE_THRESHOLD}.")
        logger.warning(f"🛑 Halting LLM Generation. Routing to fallback.")
    else:
        logger.info(f"✅ [CIRCUIT BREAKER] PASSED. Top Score: {best_score:.4f} (Threshold: {CONFIDENCE_THRESHOLD})")
        logger.info(f"📂 [LLM PAYLOAD] The following Top 5 chunks are being sent to the LLM:")
        for i, c in enumerate(top_chunks):
            logger.info(f"   {i+1}.[{c['rerank_score']:.4f}] {c['header_path']}")

    return {
        "retrieved_chunks": top_chunks,
        "confidence_score": best_score,
        "circuit_breaker_tripped": circuit_breaker
    }