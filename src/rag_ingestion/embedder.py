"""
embedder.py
-----------

Owner: Member 2 (RAG Ingestion)
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"
VECTOR_SIZE = 1024  ثابت ومتغيرش

_model = None  

def get_model(device: str = "cuda") -> SentenceTransformer:

    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, device=device)
        print(f"[embedder] Model loaded: {MODEL_NAME} | dim={_model.get_sentence_embedding_dimension()}")
    return _model


def embed_texts(texts: list[str], batch_size: int = 32, device: str = "cuda"):

    model = get_model(device=device)
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=False,
    )
    return embeddings


def embed_single(text: str, device: str = "cuda"):

    model = get_model(device=device)
    return model.encode(text, normalize_embeddings=True).tolist()
