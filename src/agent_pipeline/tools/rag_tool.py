"""
rag_tool.py

Owner: Member 3 (RAG Retrieval & Core UI).

Wraps retriever.search() into a single clean function for M4 to call from
the LangGraph agent. M4 does not need to import anything from rag_retrieval
directly — only get_medical_context() is the public interface.
"""

from src.rag_retrieval.retriever import search


def get_medical_context(query: str, top_k: int = 5) -> str:
    """
    Retrieves relevant medical context for a query using RAG (Tier 2).
    Returns a formatted string ready to inject into an LLM prompt, with
    numbered sources for citation (e.g. [1], [2]) matching the project's
    citation format.
    Each source line includes the title and pubmed_id so the agent/UI
    can build a citation reference.
    """
    hits = search(query)
    if not hits:
        return ""

    formatted = []
    for i, hit in enumerate(hits, start=1):
        pubmed_id = hit["payload"].get("pubmed_id", "N/A")
        formatted.append(f"[{i}] {hit['title']} (PMID: {pubmed_id})\n{hit['text']}")

    return "\n\n".join(formatted)


if __name__ == "__main__":
    result = get_medical_context("What are the symptoms of type 2 diabetes?")
    print(result)
