# FILE: app/main.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
import psycopg2
from psycopg2 import pool

# 🚨 FIX: Load environment variables from .env file at the very beginning
load_dotenv()

from app.routes.chat import router as chat_router 
from app.dependencies.db import prisma_client

app = FastAPI()

# ---- Config (env-driven) ----
PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
PG_PORT = int(os.getenv("PG_PORT", 6543))
PG_DB = os.getenv("PG_DB", "rag_db")
PG_USER = os.getenv("PG_USER", "admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "admin")

QDRANT_HOST = os.getenv("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# ---- Clients / Pools ----
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

pg_pool: pool.SimpleConnectionPool | None = None

@app.on_event("startup")
async def startup():
    global pg_pool
    pg_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=5,
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        connect_timeout=3,
    )
    
    # Connect Prisma globally on application startup
    if not prisma_client.is_connected():
        await prisma_client.connect()

@app.on_event("shutdown")
async def shutdown():
    if pg_pool:
        pg_pool.closeall()
        
    # Disconnect Prisma gracefully on shutdown
    if prisma_client.is_connected():
        await prisma_client.disconnect()

@app.get("/health")
def health():
    # Qdrant check
    try:
        collections = qdrant.get_collections()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant error: {e}")

    # Postgres check
    try:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        finally:
            pg_pool.putconn(conn)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Postgres error: {e}")

    return {
        "qdrant": "ok",
        "postgres": "ok",
        "prisma": "connected" if prisma_client.is_connected() else "disconnected",
        "collections": collections.dict(),
    }

app.include_router(chat_router, prefix="/chat", tags=["Chat"])