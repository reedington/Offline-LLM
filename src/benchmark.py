from __future__ import annotations

import time

import psutil

from src.chunking import chunk_documents
from src.config import DEFAULT_TOP_K, INDEX_DIR, MODEL_PATH, SAMPLE_DOCS_DIR
from src.document_loader import load_documents_from_paths
from src.embeddings import EmbeddingModel
from src.llm import LlamaCppLLM, ModelNotFoundError
from src.rag import RAGAssistant
from src.vector_store import VectorStore


QUESTIONS = [
    "What is the payment period in the supplier agreement?",
    "Can customers return opened hygiene products?",
    "What is the unit price of the solar lantern?",
]


def main() -> None:
    started = time.perf_counter()
    process = psutil.Process()
    if not MODEL_PATH.exists():
        print(
            f"GGUF model not found at {MODEL_PATH}. "
            "Place a small quantized model at models/model.gguf before running generation."
        )
        return

    docs = load_documents_from_paths(sorted(SAMPLE_DOCS_DIR.glob("*.txt")))
    chunks = chunk_documents(docs)
    embedder = EmbeddingModel(allow_hash_fallback=True)
    embeddings = embedder.embed([chunk.text for chunk in chunks])
    store = VectorStore(INDEX_DIR / "benchmark")
    store.build(chunks, embeddings)
    store.save()

    llm = LlamaCppLLM()
    assistant = RAGAssistant(store, embedder, llm)
    for question in QUESTIONS:
        q_start = time.perf_counter()
        try:
            result = assistant.answer(question, top_k=DEFAULT_TOP_K)
        except ModelNotFoundError as exc:
            print(exc)
            return
        latency = time.perf_counter() - q_start
        format_ok = bool(result["answer"] and result["evidence"])
        print(f"QUESTION: {question}")
        print(f"LATENCY_SECONDS: {latency:.2f}")
        print(f"FORMAT_OK: {format_ok}")
        print(f"ANSWER: {result['answer']}")
        print()

    rss_mb = process.memory_info().rss / (1024 * 1024)
    total_latency = time.perf_counter() - started
    print(f"TOTAL_SECONDS: {total_latency:.2f}")
    print(f"RSS_MB: {rss_mb:.1f}")


if __name__ == "__main__":
    main()
