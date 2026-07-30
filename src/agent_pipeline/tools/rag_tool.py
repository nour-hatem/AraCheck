"""
rag_tool.py

Owner: Member 3 (RAG Retrieval & Core UI).

Wraps retriever.search() into a single clean function for M4 to call from
the LangGraph agent. M4 does not need to import anything from rag_retrieval
directly.

Public interface (for M4):
  - get_medical_context(query)                      -> str   (unchanged, backward-compat)
  - get_medical_context_with_confidence(query, ...)  -> dict  (use for tier routing)
  - compute_margin(hits)                             -> float (exposed for testing)
  - is_confident(hits, ...)                          -> bool  (exposed for testing)

Confidence signal design notes
-------------------------------
rerank_score is the raw output of CrossEncoder.predict() from the
cross-encoder/ms-marco-MiniLM-L-6-v2 model. It is an unbounded regression
score (observed range in our corpus: approx -5 to +7) -- NOT a probability.
Do not treat 0.5 as a meaningful threshold on this scale.

Why margin-based confidence instead of a fixed absolute threshold?
  - We calibrated from only 12 test questions, which is too small a sample to
    reliably fit a single threshold that generalises to production queries.
  - An absolute threshold is fragile to corpus and query distribution shifts.
  - The margin (top-1 score minus average of the remaining top-k scores) is
    self-normalising: it measures how much the top result *stands out* from
    the rest, regardless of absolute score scale.

Provisional values (to be recalibrated from real usage data):
  margin_threshold = 1.0  -- top-1 must beat the rest by at least this much.
  absolute_floor   = 0.0  -- top-1 must still exceed this floor even when the
                             margin looks large (guards against misleading margins
                             when all hits are weak or negative, e.g. top-1=-0.2
                             vs rest=-3.0 gives a "confident" margin=2.8 despite
                             nothing being truly relevant).

Both values will be revisited once logs/rag_confidence_log.jsonl accumulates
sufficient real production queries and their outcomes.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.rag_retrieval.retriever import search

logger = logging.getLogger(__name__)

# JSONL log file for future recalibration of margin_threshold / absolute_floor.
# One record per get_medical_context_with_confidence() call.
# NOTE: assumes rag_tool.py is 4 directories below project root; update if the file moves.
_LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "rag_confidence_log.jsonl"


def _append_log(record: dict) -> None:
    """Appends one JSON record to the confidence log (creates dir/file as needed)."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        logger.warning("rag_tool: failed to write confidence log", exc_info=True)


def compute_margin(hits: list[dict]) -> float:
    """
    Returns the gap between the top-1 rerank_score and the average of the
    remaining top-k rerank_scores.

    A large positive margin means the top result clearly outscores the rest
    (high retrieval confidence). A small or negative margin means the results
    are bunched together and no single answer stands out (low confidence).

    Returns 0.0 when hits is empty or contains only one result.
    """
    if not hits or len(hits) < 2:
        return 0.0
    top1 = hits[0]["rerank_score"]
    rest_avg = sum(h["rerank_score"] for h in hits[1:]) / len(hits[1:])
    return top1 - rest_avg


def is_confident(
    hits: list[dict],
    margin_threshold: float = 1.0,
    absolute_floor: float = 0.0,
) -> bool:
    """
    Confidence gate combining two complementary signals:

    1. Margin check: top-1 rerank_score must beat the average of the
       remaining top-k results by at least margin_threshold.
    2. Absolute floor: top-1 must still be above absolute_floor even when
       the margin looks large -- this catches the case where all hits are
       weak/negative (e.g. top-1=-0.2, rest=-3.0 produces a margin of 2.8
       but nothing is actually relevant).

    Returns:
        True  -- Tier 2 (RAG) can answer; route query to get_medical_context().
        False -- No confident answer found; M4 should fall back to Tier 3 (web search).

    Note: margin_threshold=1.0 and absolute_floor=0.0 are provisional starting
    values derived from a 12-question benchmark. Recalibrate from
    logs/rag_confidence_log.jsonl once real production data is available.
    """
    if not hits:
        return False
    top1 = hits[0]["rerank_score"]
    if top1 < absolute_floor:
        return False
    return compute_margin(hits) >= margin_threshold


def get_medical_context(query: str, top_k: int = 5) -> str:
    """
    Retrieves relevant medical context for a query using RAG (Tier 2).
    Returns a formatted string ready to inject into an LLM prompt, with
    numbered sources for citation (e.g. [1], [2]) matching the project's
    citation format.
    Each source line includes the title and pubmed_id so the agent/UI
    can build a citation reference.

    Backward-compatible: returns str only. For confidence-gated tier routing,
    use get_medical_context_with_confidence() instead.
    top_k is passed through to the retriever's reranking stage.
    """
    hits = search(query, final_top_k=top_k)
    if not hits:
        return ""

    formatted = []
    for i, hit in enumerate(hits[:top_k], start=1):
        pubmed_id = hit["payload"].get("pubmed_id", "N/A")
        formatted.append(f"[{i}] {hit['title']} (PMID: {pubmed_id})\n{hit['text']}")

    return "\n\n".join(formatted)


def get_medical_context_with_confidence(
    query: str,
    top_k: int = 5,
    margin_threshold: float = 1.0,
    absolute_floor: float = 0.0,
) -> dict:
    """
    Retrieves RAG context AND a confidence signal so M4 can decide tier routing
    without making a second call to the retriever.

    Args:
        query:            The medical question to retrieve context for.
        top_k:            Number of top reranked results to retrieve and format
                          (default 5). Passed through to the retriever's reranking stage.
        margin_threshold: Minimum margin (top-1 minus rest-avg) to be confident.
        absolute_floor:   Minimum absolute top-1 score regardless of margin.

    Returns a dict:
        {
            "context":          str,    # formatted sources, same as get_medical_context()
            "is_confident":     bool,   # True -> RAG can answer; False -> fall back to web
            "top_rerank_score": float | None,  # top-1 raw CrossEncoder score; None if no hits
            "margin":           float,  # top-1 minus avg(rest) (for debugging/logging)
        }

    Side effect: appends one line to logs/rag_confidence_log.jsonl for future
    recalibration of margin_threshold and absolute_floor from real production data.

    Why a separate function and not changing get_medical_context()?
    M4 already has a contract with the str-only signature. Adding this as a new
    function lets M4 migrate to confidence-gated routing incrementally without
    breaking any existing call site.
    """
    hits = search(query, final_top_k=top_k)

    if not hits:
        return {
            "context": "",
            "is_confident": False,
            "top_rerank_score": None,
            "margin": 0.0,
        }

    top_score = hits[0]["rerank_score"]
    margin = compute_margin(hits)
    confident = is_confident(hits, margin_threshold, absolute_floor)

    # Log for future recalibration — only when hits is non-empty
    _append_log(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "top_rerank_score": top_score,
            "margin": margin,
            "is_confident": confident,
            "num_hits": len(hits),
        }
    )

    formatted = []
    for i, hit in enumerate(hits[:top_k], start=1):
        pubmed_id = hit["payload"].get("pubmed_id", "N/A")
        formatted.append(f"[{i}] {hit['title']} (PMID: {pubmed_id})\n{hit['text']}")

    return {
        "context": "\n\n".join(formatted),
        "is_confident": confident,
        "top_rerank_score": top_score,
        "margin": margin,
    }


if __name__ == "__main__":
    result = get_medical_context_with_confidence(
        "What are the symptoms of type 2 diabetes?"
    )
    print(f"is_confident     : {result['is_confident']}")
    print(f"top_rerank_score : {result['top_rerank_score']:.4f}")
    print(f"margin           : {result['margin']:.4f}")
    print(f"context[:200]    : {result['context'][:200]}")
