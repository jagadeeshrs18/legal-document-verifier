"""
embed_dataset.py
-----------------
Converts the reference legal dataset into vector (embedding) form and
stores it in a persistent ChromaDB vector database, ready for semantic
search in the next pipeline stage (clause classification / risk
matching against real legislation).

Run this once:
    pip install sentence-transformers chromadb
    python embed_dataset.py

It will:
  1. Walk data/reference/legislation_and_templates/ and chunk every
     document (see chunker.py)
  2. Embed every chunk using the 'all-MiniLM-L6-v2' sentence-transformer
     model (same model family used in Devika's LexIQ project, so results
     are comparable / mergeable with that work)
  3. Store the vectors + text + metadata in a local ChromaDB database
     at data/vector_db/

This only needs to be run once (or again if the reference dataset
changes) - the resulting data/vector_db/ folder is then just loaded,
not recomputed, every time the app runs.
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

from chunker import chunk_all_documents

REFERENCE_DIR = "../data/reference/legislation_and_templates"
VECTOR_DB_DIR = "../data/vector_db"
COLLECTION_NAME = "legal_reference"
MODEL_NAME = "all-MiniLM-L6-v2"   # small, fast, CPU-friendly, 384-dim vectors
BATCH_SIZE = 64


def main():
    print(f"Loading embedding model '{MODEL_NAME}' (downloads once, then cached)...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.\n")

    print("Chunking reference dataset...")
    chunks = chunk_all_documents(REFERENCE_DIR)
    print(f"  {len(chunks)} chunks ready to embed.\n")

    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Embedding and storing in ChromaDB at '{VECTOR_DB_DIR}'...")
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        done = min(i + BATCH_SIZE, len(chunks))
        print(f"  {done}/{len(chunks)} chunks embedded", end="\r")

    print(f"\n\nDone. Collection '{COLLECTION_NAME}' now has {collection.count()} vectors.")
    print(f"Vector database saved to: {VECTOR_DB_DIR}/")


if __name__ == "__main__":
    main()
