from fastapi import FastAPI
from qdrant_client import QdrantClient
import psycopg2

app = FastAPI()

# Qdrant
qdrant = QdrantClient(host="localhost", port=6333)

# Postgres
pg_conn = psycopg2.connect(
    host="localhost",
    database="rag_db",
    user="admin",
    password="admin"
)

@app.get("/health")
def health():
    # Qdrant check
    collections = qdrant.get_collections()

    # Postgres check
    cur = pg_conn.cursor()
    cur.execute("SELECT 1;")
    cur.fetchone()

    return {
        "qdrant": "ok",
        "postgres": "ok",
        "collections": collections.dict()
    }