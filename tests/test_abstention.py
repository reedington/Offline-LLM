import numpy as np

from src.config import ABSTENTION_MESSAGE
from src.rag import RAGAssistant


class DummyEmbedder:
    def embed(self, texts):
        return np.array([[1.0, 0.0]], dtype=np.float32)


class DummyLLM:
    def __init__(self, text):
        self.text = text

    def generate(self, prompt, max_tokens=512):
        return self.text


class EmptyStore:
    def search(self, query_embedding, top_k=3):
        return []


class Store:
    def __init__(self, score=0.8):
        self.score = score

    def search(self, query_embedding, top_k=3):
        return [
            {
                "chunk_id": "doc::chunk-0000",
                "source_document": "doc.txt",
                "text": "Payment terms are net 30 days.",
                "score": self.score,
                "metadata": {},
            }
        ]


def test_abstains_when_no_chunks_are_retrieved():
    assistant = RAGAssistant(EmptyStore(), DummyEmbedder(), DummyLLM("unused"))
    result = assistant.answer("What are payment terms?")

    assert result["answer"] == ABSTENTION_MESSAGE
    assert result["evidence"] == []


def test_abstains_when_llm_returns_abstention():
    assistant = RAGAssistant(Store(), DummyEmbedder(), DummyLLM(f"Answer:\n{ABSTENTION_MESSAGE}\n\nEvidence:"))
    result = assistant.answer("What are payment terms?")

    assert result["answer"] == ABSTENTION_MESSAGE


def test_returns_answer_with_evidence_when_supported():
    assistant = RAGAssistant(Store(), DummyEmbedder(), DummyLLM("Answer:\nPayment is due in 30 days.\n\nEvidence:"))
    result = assistant.answer("What are payment terms?")

    assert result["answer"] == "Payment is due in 30 days."
    assert result["evidence"][0]["source_document"] == "doc.txt"
