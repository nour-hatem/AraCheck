import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

def ingest_books(data_dir: str):
    print(f"Starting ingestion from {data_dir}...")
    # Add real processing logic here
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_books("./data/books")
