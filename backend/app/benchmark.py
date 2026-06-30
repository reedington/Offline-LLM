from __future__ import annotations

import json
import time
from pathlib import Path

import psutil

from app.chunking import chunk_documents
from app.config import INDEX_DIR, MODEL_PATH, PROJECT_ROOT, REPORTS_DIR, SAMPLE_DOCS_DIR, TOP_K
from app.document_loader import load_documents
from app.embeddings import hash_embed
from app.llm import LlamaCppLLM, ModelNotFoundError
from app.rag import RAGAssistant
from app.schemas import DocumentMetadata
from app.tools import calculate_discount, calculate_invoice_total
from app.vector_store import VectorStore

EVAL_PATH = PROJECT_ROOT / "data" / "eval" / "sme_questions.json"
OUTPUT_PATH = REPORTS_DIR / "product_smoke_test.json"


def main() -> None:
    process = psutil.Process()
    started = time.perf_counter()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    eval_items = load_eval_items()
    store, chunks_count, documents = build_or_load_index()
    embedder = BenchmarkEmbedder()
    llm = LlamaCppLLM()

    results = []
    for item in eval_items:
        q_start = time.perf_counter()
        retrieved = []
        generation_status = "not_run"
        error = None

        if item["expected_behavior"] == "calculator":
            answer = calculator_answer(item["id"])
            generation_status = "calculator"
        else:
            query_embedding = embedder.embed([item["question"]])[0]
            retrieved = store.search(query_embedding, top_k=TOP_K)
            try:
                assistant = RAGAssistant(store, embedder, llm)
                rag_result = assistant.answer(item["question"], top_k=TOP_K)
                answer = rag_result["answer"]
                generation_status = "generated"
            except ModelNotFoundError as exc:
                answer = str(exc)
                generation_status = "model_missing"
                error = str(exc)

        results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "expected_behavior": item["expected_behavior"],
                "expected_source": item.get("expected_source", ""),
                "generation_status": generation_status,
                "latency_ms": int((time.perf_counter() - q_start) * 1000),
                "retrieved_count": len(retrieved),
                "retrieved_sources": [chunk["source_document"] for chunk in retrieved],
                "answer": answer,
                "error": error,
            }
        )

    payload = {
        "benchmark": "product_smoke_test",
        "model_path": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists(),
        "generation_status": "ready" if MODEL_PATH.exists() else "model_missing",
        "total_latency_ms": int((time.perf_counter() - started) * 1000),
        "rss_mb": round(process.memory_info().rss / (1024 * 1024), 1),
        "documents": [document.model_dump() for document in documents],
        "chunks": chunks_count,
        "top_k": TOP_K,
        "eval_path": str(EVAL_PATH),
        "results": results,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


def load_eval_items() -> list[dict]:
    if EVAL_PATH.exists():
        return json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    return [
        {
            "id": "q001",
            "question": "What is the payment period in the supplier agreement?",
            "expected_behavior": "answerable",
            "expected_source": "sample_supplier_agreement.txt",
            "notes": "Fallback question.",
        }
    ]


def build_or_load_index() -> tuple[VectorStore, int, list[DocumentMetadata]]:
    store = VectorStore(INDEX_DIR / "product_smoke")
    try:
        store.load()
        if store.ready and store.embeddings is not None and store.embeddings.shape[1] == 384:
            return store, len(store.chunks), store.documents
    except FileNotFoundError:
        pass

    raw_documents = load_documents(sorted(SAMPLE_DOCS_DIR.glob("*.txt")))
    chunks = chunk_documents(raw_documents)
    documents = [
        DocumentMetadata(
            filename=document.filename,
            file_type=document.metadata.get("file_type", "txt"),
            characters=len(document.text),
            chunks=sum(1 for chunk in chunks if chunk.source_document == document.filename),
        )
        for document in raw_documents
    ]
    vectors = hash_embed([chunk.text for chunk in chunks])
    store.build(chunks, vectors, documents)
    store.save()
    return store, len(chunks), documents


def calculator_answer(question_id: str) -> str:
    if question_id == "q009":
        total = calculate_invoice_total([{"unit_price": 12000, "quantity": 2}, {"unit_price": 4500, "quantity": 1}])
        return f"Invoice total: {total} NGN"
    if question_id == "q010":
        discounted = calculate_discount(12000, 5)
        return f"Discounted price: {discounted} NGN"
    return "Calculator question not configured."


class BenchmarkEmbedder:
    def embed(self, texts: list[str]):
        return hash_embed(texts)


if __name__ == "__main__":
    main()
