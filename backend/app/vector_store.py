from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.chunking import Chunk
from app.schemas import DocumentMetadata


class VectorStore:
    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.chunks: list[Chunk] = []
        self.embeddings: np.ndarray | None = None
        self.documents: list[DocumentMetadata] = []
        self._faiss_index = None

    @property
    def ready(self) -> bool:
        return self.embeddings is not None and bool(self.chunks)

    def build(self, chunks: list[Chunk], embeddings: np.ndarray, documents: list[DocumentMetadata]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length.")
        if not chunks:
            raise ValueError("Cannot build an empty vector index.")
        self.chunks = chunks
        self.embeddings = _normalize(np.asarray(embeddings, dtype=np.float32))
        self.documents = documents
        self._build_faiss()

    def _build_faiss(self) -> None:
        self._faiss_index = None
        if self.embeddings is None:
            return
        try:
            import faiss
        except ImportError:
            return
        index = faiss.IndexFlatIP(int(self.embeddings.shape[1]))
        index.add(self.embeddings)
        self._faiss_index = index

    def save(self) -> None:
        if self.embeddings is None:
            raise ValueError("No vector index has been built.")
        self.index_dir.mkdir(parents=True, exist_ok=True)
        np.save(self.index_dir / "embeddings.npy", self.embeddings)
        chunks_payload = [
            {
                "chunk_id": chunk.chunk_id,
                "source_document": chunk.source_document,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for chunk in self.chunks
        ]
        documents_payload = [document.model_dump() for document in self.documents]
        (self.index_dir / "chunks.json").write_text(json.dumps(chunks_payload, indent=2), encoding="utf-8")
        (self.index_dir / "documents.json").write_text(json.dumps(documents_payload, indent=2), encoding="utf-8")

    def load(self) -> None:
        embeddings_path = self.index_dir / "embeddings.npy"
        chunks_path = self.index_dir / "chunks.json"
        documents_path = self.index_dir / "documents.json"
        if not embeddings_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(f"No cached index found at {self.index_dir}.")
        self.embeddings = np.load(embeddings_path).astype(np.float32)
        chunks_payload = json.loads(chunks_path.read_text(encoding="utf-8"))
        self.chunks = [
            Chunk(
                chunk_id=item["chunk_id"],
                source_document=item["source_document"],
                text=item["text"],
                metadata=item.get("metadata", {}),
            )
            for item in chunks_payload
        ]
        if documents_path.exists():
            self.documents = [DocumentMetadata(**item) for item in json.loads(documents_path.read_text(encoding="utf-8"))]
        else:
            counts: dict[str, int] = {}
            for chunk in self.chunks:
                counts[chunk.source_document] = counts.get(chunk.source_document, 0) + 1
            self.documents = [
                DocumentMetadata(filename=name, file_type=Path(name).suffix.lstrip("."), characters=0, chunks=count)
                for name, count in sorted(counts.items())
            ]
        self._build_faiss()

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[dict]:
        if self.embeddings is None or not self.chunks:
            return []
        top_k = max(1, min(top_k, len(self.chunks)))
        query = _normalize(np.asarray(query_embedding, dtype=np.float32).reshape(1, -1))

        if self._faiss_index is not None:
            scores, indices = self._faiss_index.search(query, top_k)
            pairs = zip(indices[0].tolist(), scores[0].tolist())
        else:
            scores = self.embeddings @ query[0]
            indices = np.argsort(scores)[::-1][:top_k]
            pairs = ((int(index), float(scores[index])) for index in indices)

        results = []
        for index, score in pairs:
            if index < 0:
                continue
            chunk = self.chunks[index]
            results.append(
                {
                    "source_document": chunk.source_document,
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "score": float(score),
                    "metadata": chunk.metadata,
                }
            )
        return results


def _normalize(vectors: np.ndarray) -> np.ndarray:
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)
