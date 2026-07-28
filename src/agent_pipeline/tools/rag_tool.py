"""
rag_tool.py
-----------
Owner: Member 3 (RAG Retrieval & Evaluation)
Wraps src.rag_retrieval.retriever.search() for use inside the LangGraph agent.
"""
from src.rag_retrieval.retriever import search

RAG_CONFIDENCE_THRESHOLD = 0.5


def rag_search(query: str, top_k: int = 5) -> list[dict]:
    return search(query, top_k=25)[:top_k]


def is_confident(hits: list[dict], threshold: float = RAG_CONFIDENCE_THRESHOLD) -> bool:
    if not hits:
        return False
    return hits[0].get("rerank_score", 0.0) >= threshold


def format_rag_context(hits: list[dict]) -> str:
    if not hits:
        return ""

    blocks = []
    for i, hit in enumerate(hits, start=1):
        title = hit.get("title", "")
        text = hit.get("text", "")
        blocks.append(f"[{i}] {title}\n{text}")

    return "\n\n".join(blocks)
