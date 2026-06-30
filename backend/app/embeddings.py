from __future__ import annotations

import hashlib

import numpy as np

from app.config import EMBEDDING_LOCAL_FILES_ONLY, EMBEDDING_MODEL_NAME


class EmbeddingModel:
    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME,
        local_files_only: bool = EMBEDDING_LOCAL_FILES_ONLY,
        allow_hash_fallback: bool = False,
    ):
        self.model_name = model_name
        self.local_files_only = local_files_only
        self.allow_hash_fallback = allow_hash_fallback
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            if self.allow_hash_fallback:
                return None
            raise RuntimeError("sentence-transformers is required for local embeddings.") from exc

        try:
            self._model = SentenceTransformer(self.model_name, local_files_only=self.local_files_only)
        except Exception as exc:
            if self.allow_hash_fallback:
                return None
            raise RuntimeError(
                f"Could not load local embedding model '{self.model_name}'. "
                "Cache it before offline use, or temporarily set EMBEDDING_LOCAL_FILES_ONLY=false while online."
            ) from exc
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)

        model = self._load_model()
        if model is None:
            return hash_embed(texts)

        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)


def hash_embed(texts: list[str], dimensions: int = 384) -> np.ndarray:
    vectors = np.zeros((len(texts), dimensions), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            column = int.from_bytes(digest[:4], "little") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vectors[row, column] += sign
        norm = np.linalg.norm(vectors[row])
        if norm > 0:
            vectors[row] /= norm
    return vectors
