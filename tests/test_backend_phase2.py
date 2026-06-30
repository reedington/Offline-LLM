import numpy as np
import pytest

from app.chunking import chunk_documents, chunk_text
from app.config import ABSTENTION_MESSAGE
from app.document_loader import Document
from app.prompts import SYSTEM_PROMPT
from app.rag import RAGAssistant
from app.schemas import DocumentMetadata
from app.tools import calculate_discount, calculate_invoice_total, calculate_margin, calculate_profit


def test_backend_chunking_creates_non_empty_chunks_and_preserves_source():
    document = Document(filename="policy.txt", text=" ".join(["returns"] * 80), metadata={"file_type": "txt"})
    chunks = chunk_documents([document], chunk_size=32, overlap=8)

    assert chunks
    assert chunks[0].source_document == "policy.txt"
    assert chunks[0].chunk_id.startswith("policy.txt::chunk-")


def test_backend_chunk_text_has_metadata():
    chunks = chunk_text("one two three four five six", "sample.txt", chunk_size=3, overlap=1)

    assert chunks[0].metadata["start_token"] == 0
    assert chunks[0].metadata["end_token"] == 3


def test_backend_prompt_contains_required_abstention_and_format():
    assert ABSTENTION_MESSAGE in SYSTEM_PROMPT
    assert "Answer:" in SYSTEM_PROMPT
    assert "Evidence:" in SYSTEM_PROMPT
    assert "chain-of-thought" in SYSTEM_PROMPT


def test_backend_calculator_functions():
    assert calculate_profit(70, 100) == 30
    assert calculate_margin(70, 100) == 30
    assert calculate_discount(100, 15) == 85
    assert calculate_invoice_total([{"unit_price": 100, "quantity": 2}, {"unit_price": 50}]) == 250


class DummyEmbedder:
    def embed(self, texts):
        return np.array([[1.0, 0.0]], dtype=np.float32)


class DummyLLM:
    def generate(self, prompt, max_tokens=512):
        return "Answer:\nThis should not be used.\n\nEvidence:"


class EmptyStore:
    chunks = []

    def search(self, query_embedding, top_k=3):
        return []


class WeakStore:
    chunks = [object()]

    def search(self, query_embedding, top_k=3):
        return [
            {
                "source_document": "doc.txt",
                "chunk_id": "doc.txt::chunk-0000",
                "text": "Unrelated context.",
                "score": 0.0,
            }
        ]


def test_backend_rag_abstains_when_no_chunks_exist():
    result = RAGAssistant(EmptyStore(), DummyEmbedder(), DummyLLM()).answer("What is the policy?")

    assert result["answer"] == ABSTENTION_MESSAGE
    assert result["evidence"] == []


def test_backend_rag_abstains_when_no_evidence_is_available():
    result = RAGAssistant(WeakStore(), DummyEmbedder(), DummyLLM()).answer("What is the policy?")

    assert result["answer"] == ABSTENTION_MESSAGE
    assert result["evidence"][0]["confidence"] == "low"


class StrongStore:
    ready = True
    chunks = [object()]
    documents = [DocumentMetadata(filename="doc.txt", file_type="txt", characters=32, chunks=1)]

    def search(self, query_embedding, top_k=3):
        return [
            {
                "source_document": "doc.txt",
                "chunk_id": "doc.txt::chunk-0000",
                "text": "Payment terms are net 30 days.",
                "score": 0.9,
            }
        ]


class AnsweringLLM:
    def generate(self, prompt, max_tokens=512):
        return "Answer:\nPayment terms are net 30 days.\n\nEvidence:\n- Source document: doc.txt"


class MissingModelLLM:
    def generate(self, prompt, max_tokens=512):
        from app.llm import ModelNotFoundError

        raise ModelNotFoundError("GGUF model not found at models/model.gguf.")


def test_chat_endpoint_returns_structured_answer(monkeypatch):
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    monkeypatch.setattr(backend_main, "active_store", StrongStore())
    monkeypatch.setattr(backend_main, "get_embedder", lambda: DummyEmbedder())
    monkeypatch.setattr(backend_main, "get_llm", lambda: AnsweringLLM())

    response = TestClient(backend_main.app).post("/chat", json={"question": "What are the payment terms?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Payment terms are net 30 days."
    assert payload["evidence"][0]["source_document"] == "doc.txt"
    assert payload["evidence"][0]["confidence"] == "high"
    assert payload["retrieved_chunks"][0]["chunk_id"] == "doc.txt::chunk-0000"
    assert isinstance(payload["latency_ms"], int)


def test_metrics_endpoint_returns_status_fields(monkeypatch):
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    monkeypatch.setattr(backend_main, "active_store", StrongStore())
    monkeypatch.setattr(backend_main, "last_query_latency_ms", 123)

    response = TestClient(backend_main.app).get("/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["rss_mb"], (int, float))
    assert payload["index_ready"] is True
    assert payload["documents_count"] == 1
    assert payload["chunks_count"] == 1
    assert payload["last_query_latency_ms"] == 123


def test_chat_missing_model_returns_friendly_error(monkeypatch):
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    monkeypatch.setattr(backend_main, "active_store", StrongStore())
    monkeypatch.setattr(backend_main, "get_embedder", lambda: DummyEmbedder())
    monkeypatch.setattr(backend_main, "get_llm", lambda: MissingModelLLM())

    response = TestClient(backend_main.app).post("/chat", json={"question": "What are payment terms?"})

    assert response.status_code == 400
    assert "GGUF model not found" in response.json()["detail"]


def test_chat_unanswerable_returns_exact_abstention(monkeypatch):
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    store = WeakStore()
    store.ready = True
    store.documents = [DocumentMetadata(filename="doc.txt", file_type="txt", characters=20, chunks=1)]
    monkeypatch.setattr(backend_main, "active_store", store)
    monkeypatch.setattr(backend_main, "get_embedder", lambda: DummyEmbedder())
    monkeypatch.setattr(backend_main, "get_llm", lambda: AnsweringLLM())

    response = TestClient(backend_main.app).post("/chat", json={"question": "Who is the CFO?"})

    assert response.status_code == 200
    assert response.json()["answer"] == ABSTENTION_MESSAGE


def test_calculator_endpoint_works():
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    response = TestClient(backend_main.app).post(
        "/tools/calculate",
        json={
            "operation": "invoice_total",
            "items": [{"unit_price": 12000, "quantity": 2}, {"unit_price": 4500, "quantity": 1}],
        },
    )

    assert response.status_code == 200
    assert response.json()["result"] == 28500


def test_benchmark_writes_product_smoke_json(tmp_path, monkeypatch):
    from app import benchmark

    output = tmp_path / "product_smoke_test.json"
    monkeypatch.setattr(benchmark, "OUTPUT_PATH", output)
    monkeypatch.setattr(benchmark, "build_or_load_index", lambda: (StrongStore(), 1, StrongStore.documents))
    monkeypatch.setattr(benchmark, "BenchmarkEmbedder", lambda: DummyEmbedder())
    monkeypatch.setattr(benchmark, "LlamaCppLLM", lambda: MissingModelLLM())
    benchmark.main()

    assert output.exists()
    payload = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert payload["benchmark"] == "product_smoke_test"
    assert "rss_mb" in payload
    assert payload["generation_status"] in {"ready", "model_missing"}
