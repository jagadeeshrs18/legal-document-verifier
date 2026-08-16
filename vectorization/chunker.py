"""
chunker.py
----------
Splits the reference legal dataset (data/reference/legislation_and_templates/)
into overlapping text chunks ready for embedding.

Why chunking is needed: embedding models have a limited input size, and
a whole Act (e.g. the Indian Contract Act, 1872) can be 50+ pages. We
split each document into ~120-word chunks with a small overlap so that
each chunk stays small enough to embed accurately, while the overlap
prevents a sentence from being awkwardly cut in half between chunks.
"""

import json
from pathlib import Path

CHUNK_WORDS = 120     # target chunk size in words
OVERLAP_WORDS = 20    # words repeated between consecutive chunks


def _chunk_text(text: str, chunk_words: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_words
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end >= len(words):
            break
        start = end - overlap  # step forward, but re-include the overlap
    return chunks


def load_and_chunk_document(json_path: Path) -> list[dict]:
    """Load one reference JSON file and return a list of chunk dicts,
    each carrying metadata back to its source document/page."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    chunks_out = []

    for page in data.get("pages", []):
        page_text = page.get("text", "")
        page_number = page.get("page_number")
        for i, chunk_text in enumerate(_chunk_text(page_text)):
            chunk_id = f"{meta.get('filename', json_path.stem)}_p{page_number}_c{i}"
            chunks_out.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "metadata": {
                    "category": str(meta.get("category", "unknown")),
                    "subcategory": str(meta.get("subcategory", "unknown")),
                    "doc_type": str(meta.get("doc_type", "unknown")),
                    "filename": str(meta.get("filename", json_path.stem)),
                    "page": str(page_number),
                },
            })

    return chunks_out


def chunk_all_documents(reference_dir: str) -> list[dict]:
    """Walk the whole reference dataset directory and chunk every JSON file."""
    all_chunks = []
    for json_path in Path(reference_dir).rglob("*.json"):
        try:
            all_chunks.extend(load_and_chunk_document(json_path))
        except Exception as e:
            print(f"  Skipped {json_path.name}: {e}")
    return all_chunks
