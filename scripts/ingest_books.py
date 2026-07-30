"""
scripts/ingest_books.py
-----------------------
Utility script to batch-ingest medical PDF books into Qdrant.

Run from the project root:
    python -m scripts.ingest_books
  or:
    python scripts/ingest_books.py
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so 'src.*' imports resolve correctly
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.rag_ingestion.pdf_ingestor import process_and_ingest_pdf


def ingest_books(data_dir: str) -> None:
    """
    Ingest all PDF files found in data_dir into the Qdrant vector database.

    Args:
        data_dir: Path to the directory containing medical PDF books.
    """
    books_path = Path(data_dir)
    if not books_path.exists():
        print(f"[ingest_books] Directory not found: {books_path}")
        sys.exit(1)

    pdfs = sorted(books_path.glob("*.pdf"))
    if not pdfs:
        print(f"[ingest_books] No PDF files found in: {books_path}")
        return

    print(f"[ingest_books] Found {len(pdfs)} PDF(s) in {books_path}")
    for pdf_path in pdfs:
        print(f"  -> Processing: {pdf_path.name}")
        try:
            result = process_and_ingest_pdf(str(pdf_path), filename=pdf_path.name)
            print(
                f"     Done: {result['total_pages']} pages, "
                f"{result['total_chunks']} chunks, status={result['status']}"
            )
        except Exception as e:
            print(f"     ERROR: {e}")

    print("[ingest_books] Ingestion complete.")


if __name__ == "__main__":
    data_directory = sys.argv[1] if len(sys.argv) > 1 else "./data/books"
    ingest_books(data_directory)
