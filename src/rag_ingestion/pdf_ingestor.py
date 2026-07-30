"""
pdf_ingestor.py
---------------
Owner: Member 2 (RAG Ingestion)

Processes a PDF file, extracts its text, chunks it, embeds the chunks,
and upserts them into the Qdrant vector database.
"""
from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("aracheck.pdf_ingestor")


def _extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    """
    Extract raw text from a PDF file using PyMuPDF (fitz).

    Returns:
        Tuple of (full_text, total_pages)

    Raises:
        ImportError: if PyMuPDF is not installed.
        ValueError: if the PDF is password-protected or unreadable.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise ImportError(
            "PyMuPDF is required for PDF processing. "
            "Install it with: pip install pymupdf"
        ) from e

    doc = fitz.open(pdf_path)
    if doc.needs_pass:
        raise ValueError("The uploaded PDF is password-protected and cannot be processed.")

    pages_text: list[str] = []
    for page in doc:
        pages_text.append(page.get_text())
    doc.close()

    full_text = "\n\n".join(pages_text)
    return full_text, len(pages_text)


def _upsert_to_qdrant(chunks: list[dict], collection_name: str = "medical_docs") -> int:
    """
    Embed chunks and upsert them into Qdrant.

    Args:
        chunks: List of dicts with keys 'text' and 'source'.
        collection_name: Target Qdrant collection.

    Returns:
        Number of points upserted.
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import PointStruct, VectorParams, Distance

    from src.rag_ingestion.embedder import embed_texts

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    # Create collection if it doesn't exist yet
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        # BAAI/bge-m3 produces 1024-dim embeddings
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        logger.info(f"[pdf_ingestor] Created Qdrant collection: {collection_name}")

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, device="cpu")

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload={"text": chunk["text"], "source": chunk["source"]},
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    client.upsert(collection_name=collection_name, points=points)
    logger.info(f"[pdf_ingestor] Upserted {len(points)} points into '{collection_name}'")
    return len(points)


def process_and_ingest_pdf(
    pdf_path: str,
    filename: str | None = None,
    collection_name: str = "medical_docs",
) -> dict:
    """
    Full pipeline: extract → chunk → embed → upsert.

    Args:
        pdf_path: Absolute path to the temporary PDF file.
        filename: Original filename (used as the source label in Qdrant).
        collection_name: Target Qdrant collection name.

    Returns:
        Dict with keys: filename, total_pages, total_chunks, status.

    Raises:
        ValueError: For invalid / unreadable PDFs.
        Exception: For embedding or Qdrant errors.
    """
    from src.rag_ingestion.chunker import chunk_pdf_book

    source_label = filename or Path(pdf_path).name

    logger.info(f"[pdf_ingestor] Processing PDF: {source_label}")

    # Step 1: Extract text
    full_text, total_pages = _extract_text_from_pdf(pdf_path)

    if not full_text.strip():
        raise ValueError(
            "The uploaded PDF appears to contain no extractable text. "
            "It may be a scanned image-only document."
        )

    # Step 2: Chunk
    chunks = chunk_pdf_book(full_text, source_name=source_label)
    total_chunks = len(chunks)
    logger.info(f"[pdf_ingestor] Chunked into {total_chunks} pieces ({total_pages} pages)")

    # Step 3: Embed & upsert
    _upsert_to_qdrant(chunks, collection_name=collection_name)

    return {
        "filename": source_label,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "status": "success",
    }
