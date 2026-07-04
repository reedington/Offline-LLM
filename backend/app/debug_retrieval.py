"""Inspect what the vector store retrieves for a question.

Usage (from backend/):
    python -m app.debug_retrieval --question "What must BrightMart provide when reporting damaged goods?"
    python -m app.debug_retrieval --question "..." --top-k 5 --rebuild

Reads the cached default index (or rebuilds it from data/sample_docs with
--rebuild) and prints the top chunks with scores, sources, chunk ids, and a
short text preview. Pure inspection tool — no generation, no cloud calls.
"""

from __future__ import annotations

import argparse

from app.chunking import chunk_documents
from app.config import DEFAULT_INDEX_NAME, INDEX_DIR, SAMPLE_DOCS_DIR, TOP_K
from app.document_loader import load_documents
from app.embeddings import EmbeddingModel
from app.rag import weak_retrieval
from app.schemas import DocumentMetadata
from app.vector_store import VectorStore


def build_sample_store(embedder: EmbeddingModel) -> VectorStore:
    paths = sorted(SAMPLE_DOCS_DIR.glob("*.txt"))
    documents = load_documents(paths)
    chunks = chunk_documents(documents)
    metadata = [
        DocumentMetadata(
            filename=document.filename,
            file_type=document.metadata.get("file_type", ""),
            characters=len(document.text),
            chunks=sum(1 for chunk in chunks if chunk.source_document == document.filename),
        )
        for document in documents
    ]
    store = VectorStore(INDEX_DIR / DEFAULT_INDEX_NAME)
    store.build(chunks, embedder.embed([chunk.text for chunk in chunks]), metadata)
    return store


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect retrieval for a question.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the index from data/sample_docs instead of loading the cache.")
    args = parser.parse_args()

    embedder = EmbeddingModel()
    if args.rebuild:
        store = build_sample_store(embedder)
        print(f"Rebuilt index from {SAMPLE_DOCS_DIR} ({len(store.chunks)} chunks).")
    else:
        store = VectorStore(INDEX_DIR / DEFAULT_INDEX_NAME)
        try:
            store.load()
            print(f"Loaded cached index '{DEFAULT_INDEX_NAME}' ({len(store.chunks)} chunks).")
        except FileNotFoundError:
            store = build_sample_store(embedder)
            print(f"No cached index; rebuilt from {SAMPLE_DOCS_DIR} ({len(store.chunks)} chunks).")

    query_embedding = embedder.embed([args.question])[0]
    retrieved = store.search(query_embedding, top_k=args.top_k)

    print(f"\nQuestion: {args.question}")
    print(f"Top-k: {args.top_k} | weak_retrieval: {weak_retrieval(retrieved) if retrieved else 'n/a (nothing retrieved)'}\n")
    for rank, chunk in enumerate(retrieved, start=1):
        preview = " ".join(chunk["text"].split())[:160]
        print(f"#{rank} score={chunk.get('score', 0.0):.4f} source={chunk['source_document']} chunk_id={chunk['chunk_id']}")
        print(f"    {preview}\n")


if __name__ == "__main__":
    main()
