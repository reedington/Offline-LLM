from __future__ import annotations

from dataclasses import dataclass

from src.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_TOKENS
from src.document_loader import Document


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_document: str
    text: str
    metadata: dict


def approximate_tokens(text: str) -> list[str]:
    return text.split()


def chunk_text(
    text: str,
    source_document: str,
    chunk_size: int = DEFAULT_CHUNK_TOKENS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    tokens = approximate_tokens(text)
    if not tokens:
        return []

    chunks: list[Chunk] = []
    step = chunk_size - overlap
    for index, start in enumerate(range(0, len(tokens), step)):
        window = tokens[start : start + chunk_size]
        if not window:
            break
        chunk_id = f"{source_document}::chunk-{index:04d}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                source_document=source_document,
                text=" ".join(window),
                metadata={"start_token": start, "end_token": start + len(window)},
            )
        )
        if start + chunk_size >= len(tokens):
            break
    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int = DEFAULT_CHUNK_TOKENS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_text(document.text, document.filename, chunk_size, overlap))
    if not chunks:
        raise ValueError("No chunks were created from the provided documents.")
    return chunks
