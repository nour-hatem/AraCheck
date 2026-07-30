"""
web_search.py
-------------
Owner: Member 4 (Agent & Web Search & Voice)
"""
import os

from tavily import TavilyClient

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "PUT_YOUR_TAVILY_KEY_HERE")

_client = None


def get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    return _client


_TAVILY_MAX_QUERY_LEN = 390  # Tavily hard limit is 400; use 390 for safety


def web_search(query: str, max_results: int = 5) -> list[dict]:
    client = get_client()

    # Tavily rejects queries longer than 400 characters — truncate safely
    if len(query) > _TAVILY_MAX_QUERY_LEN:
        query = query[:_TAVILY_MAX_QUERY_LEN].rsplit(" ", 1)[0]

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "[web_search] Tavily search failed (query len=%d): %s", len(query), exc
        )
        return []

    results = []
    for item in response.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
            "score": item.get("score", 0.0),
        })

    return results


def format_web_context(results: list[dict]) -> str:
    if not results:
        return ""

    blocks = []
    for i, r in enumerate(results, start=1):
        blocks.append(f"[{i}] {r['title']}\n{r['content']}\nSource: {r['url']}")

    return "\n\n".join(blocks)
