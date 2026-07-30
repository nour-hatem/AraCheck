"""
retriever.py
------------
Owner: Member 3 (RAG Retrieval & Evaluation).
Embeds queries via the Hugging Face InferenceClient (BAAI/bge-m3), so no
model weights are downloaded or run locally — this machine has no GPU and
limited internet. Requires HF_TOKEN in .env.
"""

import os
import re

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder

load_dotenv()

QDRANT_URL     = os.environ.get("QDRANT_URL",     "PUT_YOUR_URL_HERE")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "PUT_YOUR_KEY_HERE")
HF_TOKEN       = os.environ.get("HF_TOKEN",       "PUT_YOUR_HF_TOKEN_HERE")

COLLECTION_NAME = "aradoc_pubmed"
TEXT_FIELD      = "content"          # confirmed Qdrant payload key

EMBEDDING_MODEL = "BAAI/bge-m3"
RERANK_MODEL    = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEN_MODEL       = "Qwen/Qwen2.5-7B-Instruct"  # used only by multi_query_search

_client    = None
_hf_client = None
_reranker  = None


def get_client() -> QdrantClient:
    """Returns a cached Qdrant client."""
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return _client


def get_hf_client() -> InferenceClient:
    """Returns a cached Hugging Face InferenceClient."""
    global _hf_client
    if _hf_client is None:
        _hf_client = InferenceClient(api_key=HF_TOKEN)
    return _hf_client


def get_reranker() -> CrossEncoder:
    """Returns a cached cross-encoder reranker (validated best performer)."""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANK_MODEL)
    return _reranker


def _extract_dense_vector(raw_output) -> list:
    """
    Normalizes the feature_extraction() response into a flat, L2-normalized
    dense vector, regardless of whether the API returns a ready pooled vector
    or a per-token array.
    """
    arr = raw_output
    if hasattr(arr, "tolist"):
        arr = arr.tolist()
    while isinstance(arr, list) and len(arr) == 1 and isinstance(arr[0], list):
        arr = arr[0]
    vector = arr if isinstance(arr[0], (int, float)) else arr[0]
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm > 0 else vector


def embed_query(text: str) -> list:
    """Embeds a query using BAAI/bge-m3 via the HF Inference API."""
    client = get_hf_client()
    output = client.feature_extraction(text, model=EMBEDDING_MODEL)
    return _extract_dense_vector(output)


def rerank(query: str, hits: list[dict], top_k: int = 5) -> list[dict]:
    """Reranks candidate hits using the cross-encoder (validated best performer)."""
    if not hits:
        return []
    reranker = get_reranker()
    pairs = [(query, hit["text"]) for hit in hits]
    scores = reranker.predict(pairs)
    for hit, score in zip(hits, scores):
        hit["rerank_score"] = float(score)
    return sorted(hits, key=lambda h: h["rerank_score"], reverse=True)[:top_k]


def search(query: str, top_k: int = 25, final_top_k: int = 5) -> list[dict]:
    """
    Retrieves top_k candidates from Qdrant by vector similarity, then reranks
    them with the cross-encoder and returns the final final_top_k results
    (default 5, backward-compatible).

    Returns a list of dicts, each with:
      "text", "title", "score" (vector similarity), "payload" (raw Qdrant
      payload), "rerank_score" (cross-encoder score).
    """
    client = get_client()
    query_vector = embed_query(query)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )
    candidates = [
        {
            "text": point.payload.get(TEXT_FIELD, ""),
            "title": point.payload.get("title", ""),
            "score": point.score,
            "payload": point.payload,
        }
        for point in results.points
    ]
    return rerank(query, candidates, top_k=final_top_k)


def generate_query_variations(query: str, n: int = 3) -> list[str]:
    """
    Generates n alternative phrasings of the query using a small instruct
    model, to be used only by multi_query_search(). NOT used by default —
    benchmarked to give no reliable improvement over plain search().
    """
    client = get_hf_client()
    prompt = (
        f"Generate {n} alternative ways to phrase this medical question for a "
        f"search engine: {query}. One per line, no numbering."
    )
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=GEN_MODEL,
            max_tokens=150,
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        variations = []
        for line in lines:
            cleaned = re.sub(r"^\d+[\.\)]\s*|-\s*", "", line).strip()
            if cleaned:
                variations.append(cleaned)
        variations = variations[:n]
    except Exception:
        variations = []

    all_queries = [query]
    for v in variations:
        if v.lower() != query.lower() and v not in all_queries:
            all_queries.append(v)
    return all_queries


def reciprocal_rank_fusion(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """
    Fuses multiple ranked candidate lists using Reciprocal Rank Fusion (RRF),
    deduping by pubmed_id. Used only by multi_query_search().
    """
    rrf_scores = {}
    doc_map = {}
    for r_list in result_lists:
        for rank, hit in enumerate(r_list, start=1):
            doc_id = hit["payload"].get("pubmed_id") or hit.get("title") or hit["text"]
            if doc_id not in doc_map:
                doc_map[doc_id] = hit
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda d: rrf_scores[d], reverse=True)
    fused = []
    for doc_id in sorted_doc_ids:
        doc = dict(doc_map[doc_id])
        doc["rrf_score"] = rrf_scores[doc_id]
        fused.append(doc)
    return fused


def multi_query_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Optional alternative to search() using LLM query variations + RRF fusion
    + cross-encoder reranking. NOT the default — benchmarked on our 6-question
    test set and showed no reliable improvement (66.7% vs 70% precision for
    plain search()), plus added LLM-call latency. Kept available for future
    re-evaluation, not wired into rag_tool.py or eval_ragas.py by default.
    """
    client = get_client()
    queries = generate_query_variations(query)
    all_candidate_lists = []

    for q in queries:
        query_vector = embed_query(q)
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=25,
            with_payload=True,
        )
        candidates = [
            {
                "text": point.payload.get(TEXT_FIELD, ""),
                "title": point.payload.get("title", ""),
                "score": point.score,
                "payload": point.payload,
            }
            for point in results.points
        ]
        all_candidate_lists.append(candidates)

    fused = reciprocal_rank_fusion(all_candidate_lists, k=60)
    return rerank(query, fused[:25], top_k=top_k)


if __name__ == "__main__":
    test_query = "What are the symptoms of type 2 diabetes?"
    hits = search(test_query)
    for i, hit in enumerate(hits, start=1):
        print(f"\n[{i}] vec_score={hit['score']:.4f}  rerank_score={hit['rerank_score']:.4f}")
        print(f"Title: {hit['title']}")
        print(hit["text"][:300])
