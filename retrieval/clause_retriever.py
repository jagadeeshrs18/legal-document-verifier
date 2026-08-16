"""
clause_retriever.py
--------------------
For every clause extracted from an uploaded contract, finds the most
relevant matching provisions in the vectorized Indian legal reference
dataset (data/vector_db/, built by vectorization/embed_dataset.py).

This is the bridge between:
  - Stage 2 (clause segmentation of the uploaded contract), and
  - Stage 5 (risk / red-flag detection),
by grounding each clause in the actual law it relates to.

Usage:
    from retrieval.clause_retriever import ClauseRetriever

    retriever = ClauseRetriever()
    clauses_with_matches = retriever.attach_matches(clauses)
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

VECTOR_DB_DIR = str(Path(__file__).resolve().parent.parent / "data" / "vector_db")
COLLECTION_NAME = "legal_reference"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 3  # how many matching law excerpts to attach per clause


class ClauseRetriever:
    """Loads the embedding model + vector DB once, then can be reused
    across many upload requests without reloading each time."""

    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        self.collection = client.get_collection(COLLECTION_NAME)

    def find_matches(self, clause_text: str, top_k: int = TOP_K) -> list[dict]:
        """Return the top_k most relevant law/template excerpts for a
        single clause of contract text."""
        if not clause_text.strip():
            return []

        query_embedding = self.model.encode([clause_text]).tolist()
        result = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )

        matches = []
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            matches.append({
                "source_document": meta.get("filename", "unknown"),
                "category": meta.get("category", "unknown"),
                "subcategory": meta.get("subcategory", "unknown"),
                "page": meta.get("page", "?"),
                "excerpt": doc,
                # ChromaDB cosine distance: 0 = identical, 2 = opposite.
                # Converted to an intuitive 0-100% relevance score.
                "relevance_pct": round(max(0.0, 1 - dist / 2) * 100, 1),
            })
        return matches

    def attach_matches(self, clauses: list[dict], top_k: int = TOP_K) -> list[dict]:
        """Takes the list of clause dicts produced by
        segmentation.clause_segmenter.segment_clauses() and attaches a
        'law_matches' list to each one."""
        for clause in clauses:
            clause["law_matches"] = self.find_matches(clause["text"], top_k=top_k)
        return clauses
