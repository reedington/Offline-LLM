from __future__ import annotations

import re
from typing import Protocol

from src.config import ABSTENTION_MESSAGE, DEFAULT_TOP_K
from src.prompts import build_rag_prompt


class Embedder(Protocol):
    def embed(self, texts: list[str]): ...


class Generator(Protocol):
    def generate(self, prompt: str, max_tokens: int = 512) -> str: ...


class RAGAssistant:
    def __init__(self, vector_store, embedder: Embedder, llm: Generator):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm = llm

    def answer(self, question: str, top_k: int = DEFAULT_TOP_K) -> dict:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        query_embedding = self.embedder.embed([question])[0]
        retrieved = self.vector_store.search(query_embedding, top_k=top_k)
        if not retrieved or _weak_retrieval(retrieved):
            return _abstention_result(retrieved)

        prompt = build_rag_prompt(question, retrieved)
        raw_answer = self.llm.generate(prompt, max_tokens=512)
        answer = _extract_answer(raw_answer)
        if not answer or ABSTENTION_MESSAGE.lower() in answer.lower():
            return _abstention_result(retrieved)

        evidence = [
            {
                "source_document": chunk["source_document"],
                "chunk_id": chunk["chunk_id"],
                "quote": _short_quote(chunk["text"]),
                "support_level": _support_level(chunk.get("score", 0.0)),
            }
            for chunk in retrieved
        ]
        return {"answer": answer, "evidence": evidence, "retrieved_chunks": retrieved}


def _weak_retrieval(retrieved: list[dict], min_score: float = 0.05) -> bool:
    best = max(float(item.get("score", 0.0)) for item in retrieved)
    return best < min_score


def _extract_answer(raw_answer: str) -> str:
    cleaned = raw_answer.strip()
    if not cleaned:
        return ""
    answer_match = re.search(r"Answer:\s*(.*?)(?:\n\s*Evidence:|$)", cleaned, flags=re.I | re.S)
    if answer_match:
        answer = answer_match.group(1).strip()
        return answer or ABSTENTION_MESSAGE
    return cleaned


def _short_quote(text: str, max_chars: int = 420) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def _support_level(score: float) -> str:
    if score >= 0.55:
        return "high"
    if score >= 0.25:
        return "medium"
    return "low"


def _abstention_result(retrieved: list[dict] | None = None) -> dict:
    retrieved = retrieved or []
    evidence = [
        {
            "source_document": chunk["source_document"],
            "chunk_id": chunk["chunk_id"],
            "quote": _short_quote(chunk["text"]),
            "support_level": "low",
        }
        for chunk in retrieved
    ]
    return {"answer": ABSTENTION_MESSAGE, "evidence": evidence, "retrieved_chunks": retrieved}
