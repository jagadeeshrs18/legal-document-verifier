"""
query_test.py
-------------
Quick sanity check after running embed_dataset.py: run a few sample
legal questions against the vector database and see what comes back.

Run:
    python query_test.py
"""

from sentence_transformers import SentenceTransformer
import chromadb

VECTOR_DB_DIR = "../data/vector_db"
COLLECTION_NAME = "legal_reference"
MODEL_NAME = "all-MiniLM-L6-v2"

SAMPLE_QUERIES = [
    "what counts as valid consideration in a contract",
    "penalty for late payment to an MSME supplier",
    "grounds for termination of an employment agreement",
    "confidentiality obligations in an NDA",
]


def main():
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    print(f"Collection '{COLLECTION_NAME}' has {collection.count()} vectors.\n")

    for query in SAMPLE_QUERIES:
        query_embedding = model.encode([query]).tolist()
        result = collection.query(query_embeddings=query_embedding, n_results=3)

        print(f"Query: {query}")
        for doc, meta, dist in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            print(f"  [{meta['filename']} p.{meta['page']}] (distance={dist:.3f})")
            print(f"    {doc[:150]}...")
        print()


if __name__ == "__main__":
    main()
