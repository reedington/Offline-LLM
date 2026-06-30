from __future__ import annotations

import psutil


def rss_mb() -> float:
    return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)


def build_metrics(store, model_loaded: bool, last_query_latency_ms: int | None) -> dict:
    index_ready = bool(store and getattr(store, "ready", False))
    documents = getattr(store, "documents", []) if store else []
    chunks = getattr(store, "chunks", []) if store else []
    return {
        "rss_mb": rss_mb(),
        "model_loaded": model_loaded,
        "index_ready": index_ready,
        "documents_count": len(documents),
        "chunks_count": len(chunks),
        "last_query_latency_ms": last_query_latency_ms,
    }
