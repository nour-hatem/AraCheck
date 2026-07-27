"""
ingest_books.py
---------------
Owner: Member 2 (RAG Ingestion)

"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from tqdm.auto import tqdm
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from src.rag_ingestion.embedder import embed_texts, VECTOR_SIZE
from src.rag_ingestion.chunker import chunk_text


# ==========================
# ==========================
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")  
COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION", "aradoc_pubmed")

DATASET_NAME = os.environ.get("DATASET_NAME", "MedRAG/pubmed")
TARGET = int(os.environ.get("INGEST_TARGET", "100000"))
BATCH_SIZE = int(os.environ.get("INGEST_BATCH_SIZE", "128"))
DEVICE = os.environ.get("EMBEDDING_DEVICE", "cpu")  


def get_qdrant_client() -> QdrantClient:
    if QDRANT_API_KEY:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(url=QDRANT_URL)


def ensure_clean_collection(client: QdrantClient):
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        print(f"[ingest] Collection '{COLLECTION_NAME}'excit.")
    else:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[ingest] Collection '{COLLECTION_NAME}' new.")


def upsert_batch(client: QdrantClient, point_id_start: int, texts: list[str], payloads: list[dict]) -> int:
    vectors = embed_texts(texts, batch_size=len(texts), device=DEVICE)
    points = [
        PointStruct(id=point_id_start + i, vector=vectors[i].tolist(), payload=payloads[i])
        for i in range(len(vectors))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def main():
    client = get_qdrant_client()
    ensure_clean_collection(client)

    ds = load_dataset(DATASET_NAME, split="train", streaming=True)

    batch_texts, batch_payloads = [], []
    point_id = 0
    pbar = tqdm(total=TARGET, desc="Ingesting")

    for row in ds:
        if point_id >= TARGET:
            break

        # for chunk in chunk_text(extracted_book_text): ...
        text = row["contents"]

        batch_texts.append(text)
        batch_payloads.append({
            "pubmed_id": row["PMID"],
            "title": row["title"],
            "content": row["content"],
        })

        if len(batch_texts) >= BATCH_SIZE:
            uploaded = upsert_batch(client, point_id, batch_texts, batch_payloads)
            point_id += uploaded
            pbar.update(uploaded)
            batch_texts, batch_payloads = [], []

    if batch_texts:
        uploaded = upsert_batch(client, point_id, batch_texts, batch_payloads)
        point_id += uploaded
        pbar.update(uploaded)

    pbar.close()
    print(f"\n[ingest] Done. Total points uploaded: {point_id}")


if __name__ == "__main__":
    main()
