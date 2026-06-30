import numpy as np

from app.chunking import chunk_documents, chunk_text
from app.config import ABSTENTION_MESSAGE
from app.document_loader import Document
from app.prompts import SYSTEM_PROMPT
from app.rag import RAGAssistant
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
