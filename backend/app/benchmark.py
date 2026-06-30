from __future__ import annotations

import json
import time

import psutil

from app.chunking import chunk_documents
from app.config import INDEX_DIR, MODEL_PATH, REPORTS_DIR, SAMPLE_DOCS_DIR, TOP_K
from app.document_loader import load_documents
from app.embeddings import EmbeddingModel
from app.llm import LlamaCppLLM, ModelNotFoundError
from app.rag import RAGAssistant
from app.schemas import DocumentMetadata
from app.tools import calculate_invoice_total
from app.vector_store import VectorStore


QUESTIONS = [
    "What is the payment period in the supplier agreement?",
    "Can customers return opened hygiene products?",
    "What is the unit price of the solar lantern?",
    "What is the warranty period for refrigerated trucks?",
    "What is the invoice total for two solar lanterns and one water filter cartridge?",
]


def main() -> None:
    process = psutil.Process()
    started = time.perf_counter()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    documents = load_documents(sorted(SAMPLE_DOCS_DIR.glob("*.txt")))
    chunks = chunk_documents(documents)
    metadata = [
        DocumentMetadata(
            filename=document.filename,
            file_type=document.metadata.get("file_type", "txt"),
            characters=len(document.text),
            chunks=sum(1 for chunk in chunks if chunk.source_document == document.filename),
        )
        for document in documents
    ]
    embedder = EmbeddingModel(allow_hash_fallback=True)
    vectors = embedder.embed([chunk.text for chunk in chunks])
    store = VectorStore(INDEX_DIR / "product_smoke")
    store.build(chunks, vectors, metadata)
    store.save()

    llm = LlamaCppLLM()
    results = []
    for question in QUESTIONS:
        q_start = time.perf_counter()
        if "invoice total" in question:
            answer = f"Invoice total: {calculate_invoice_total([{'unit_price': 12000, 'quantity': 2}, {'unit_price': 4500, 'quantity': 1}])} NGN"
            result = {"answer": answer, "evidence": [], "retrieved_chunks": []}
        else:
            try:
                assistant = RAGAssistant(store, embedder, llm)
                result = assistant.answer(question, top_k=TOP_K)
            except ModelNotFoundError as exc:
                result = {"answer": str(exc), "evidence": [], "retrieved_chunks": []}
        results.append(
            {
                "question": question,
                "latency_ms": int((time.perf_counter() - q_start) * 1000),
                "answer": result["answer"],
                "evidence_count": len(result["evidence"]),
                "retrieved_count": len(result["retrieved_chunks"]),
            }
        )

    payload = {
        "model_path": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists(),
        "total_latency_ms": int((time.perf_counter() - started) * 1000),
        "rss_mb": round(process.memory_info().rss / (1024 * 1024), 1),
        "documents": [item.model_dump() for item in metadata],
        "chunks": len(chunks),
        "results": results,
    }
    output = REPORTS_DIR / "product_smoke_test.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
