import os
from fastapi import FastAPI, HTTPException
from qdrant_client import QdrantClient
import psycopg2
from psycopg2 import pool

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
def startup():
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


@app.on_event("shutdown")
def shutdown():
    if pg_pool:
        pg_pool.closeall()


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
        "collections": collections.dict(),
    }