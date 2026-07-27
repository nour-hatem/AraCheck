"""
retriever.py
------------
Owner: Member 3 (RAG Retrieval & Evaluation)
"""
import os
from getpass import getpass

from qdrant_client import QdrantClient

from src.rag_ingestion.embedder import embed_single

QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION", "aradoc_pubmed")

_client = None


def get_client() -> QdrantClient:
    global _client

    if _client is None:
        url = QDRANT_URL or input("Enter QDRANT_URL: ").strip()
        api_key = QDRANT_API_KEY or getpass("Enter QDRANT_API_KEY: ").strip()
        _client = QdrantClient(url=url, api_key=api_key)

    return _client


def search(query: str, top_k: int = 20, device: str = "cuda") -> list[dict]:
    client = get_client()
    query_vector = embed_single(query, device=device)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    )

    hits = []
    for point in results.points:
        hits.append({
            "id": point.id,
            "score": point.score,
            "pubmed_id": point.payload.get("pubmed_id"),
            "title": point.payload.get("title"),
            "content": point.payload.get("content"),
        })

    return hits


def retrieve(query: str, top_n: int = 5, candidate_k: int = 20, device: str = "cuda") -> list[dict]:
    from src.rag_retrieval.reranker import rerank

    candidates = search(query, top_k=candidate_k, device=device)

    if not candidates:
        return []

    reranked = rerank(query, candidates, top_n=top_n, device=device)
    return reranked
