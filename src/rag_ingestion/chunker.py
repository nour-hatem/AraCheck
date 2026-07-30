"""
chunker.py
----------
Text chunking utilities for RAG document processing.
"""
from __future__ import annotations

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Minimal pure-Python fallback for text splitting
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size=1000, chunk_overlap=150, separators=None):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap

            def split_text(self, text: str) -> list[str]:
                chunks = []
                start = 0
                while start < len(text):
                    end = start + self.chunk_size
                    chunks.append(text[start:end])
                    start = end - self.chunk_overlap
                    if start >= len(text):
                        break
                return chunks

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_text(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text]
    splitter = get_splitter()
    return splitter.split_text(text)


def chunk_pdf_book(raw_text: str, source_name: str) -> list[dict]:
    chunks = chunk_text(raw_text)
    return [{"text": c, "source": source_name} for c in chunks]
