"""
reranker.py
-----------
Owner: Member 3 (RAG Retrieval & Evaluation)
"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

RERANKER_MODEL = "BAAI/bge-reranker-base"

_tokenizer = None
_model = None


def get_reranker(device: str = "cuda"):
    global _tokenizer, _model

    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(RERANKER_MODEL)
        _model = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL)
        _model.eval()
        _model.to(device)
        print(f"[reranker] Model loaded: {RERANKER_MODEL}")

    return _tokenizer, _model


def rerank(query: str, candidates: list[dict], top_n: int = 5, device: str = "cuda") -> list[dict]:
    if not candidates:
        return []

    tokenizer, model = get_reranker(device=device)

    pairs = [[query, c["content"]] for c in candidates]

    with torch.no_grad():
        inputs = tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
        ).to(device)

        logits = model(**inputs, return_dict=True).logits.view(-1).float()
        scores = torch.sigmoid(logits).cpu().tolist()

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = score

    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_n]
