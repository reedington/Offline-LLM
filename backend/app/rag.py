from __future__ import annotations

import re
from typing import Protocol

from app.config import ABSTENTION_MESSAGE, TOP_K
from app.prompts import build_rag_prompt


class Embedder(Protocol):
    def embed(self, texts: list[str]): ...


class Generator(Protocol):
    def generate(self, prompt: str, max_tokens: int = 512) -> str: ...


class RAGAssistant:
    def __init__(self, vector_store, embedder: Embedder, llm: Generator):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm = llm

    def answer(self, question: str, top_k: int = TOP_K) -> dict:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        if not getattr(self.vector_store, "chunks", []):
            return abstention_result([])

        query_embedding = self.embedder.embed([question])[0]
        retrieved = self.vector_store.search(query_embedding, top_k=top_k)
        if not retrieved or weak_retrieval(retrieved):
            return abstention_result(retrieved)

        prompt = build_rag_prompt(question, retrieved)
        raw_answer = self.llm.generate(prompt, max_tokens=512)
        answer = extract_answer(raw_answer)
        if not answer or ABSTENTION_MESSAGE.lower() in answer.lower():
            return abstention_result(retrieved)

        evidence = [
            {
                "source_document": chunk["source_document"],
                "chunk_id": chunk["chunk_id"],
                "quote": short_quote(chunk["text"]),
                "confidence": confidence(chunk.get("score", 0.0)),
            }
            for chunk in retrieved
        ]
        return {"answer": answer, "evidence": evidence, "retrieved_chunks": clean_chunks(retrieved)}


def weak_retrieval(retrieved: list[dict], min_score: float = 0.05) -> bool:
    return max(float(item.get("score", 0.0)) for item in retrieved) < min_score


def extract_answer(raw_answer: str) -> str:
    cleaned = raw_answer.strip()
    if not cleaned:
        return ""
    match = re.search(r"Answer:\s*(.*?)(?:\n\s*Evidence:|$)", cleaned, flags=re.I | re.S)
    if match:
        answer = match.group(1).strip()
        return answer or ABSTENTION_MESSAGE
    return cleaned


def short_quote(text: str, max_chars: int = 420) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def confidence(score: float) -> str:
    if score >= 0.55:
        return "high"
    if score >= 0.25:
        return "medium"
    return "low"


def clean_chunks(chunks: list[dict]) -> list[dict]:
    return [
        {
            "source_document": chunk["source_document"],
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "score": float(chunk.get("score", 0.0)),
        }
        for chunk in chunks
    ]


def abstention_result(retrieved: list[dict] | None = None) -> dict:
    retrieved = retrieved or []
    return {
        "answer": ABSTENTION_MESSAGE,
        "evidence": [
            {
                "source_document": chunk["source_document"],
                "chunk_id": chunk["chunk_id"],
                "quote": short_quote(chunk["text"]),
                "confidence": "low",
            }
            for chunk in retrieved
        ],
        "retrieved_chunks": clean_chunks(retrieved),
    }
