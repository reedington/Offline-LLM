from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Offline SME AI Assistant"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"
MODEL_DIR = PROJECT_ROOT / "models"
INDEX_DIR = PROJECT_ROOT / "indexes"
REPORTS_DIR = PROJECT_ROOT / "reports"

MODEL_PATH = Path(os.getenv("MODEL_PATH", MODEL_DIR / "model.gguf"))
LLM_CTX = int(os.getenv("LLM_CTX", "2048"))
LLM_THREADS = int(os.getenv("LLM_THREADS", str(max(1, min((os.cpu_count() or 2) // 2, 6)))))

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_LOCAL_FILES_ONLY = os.getenv("EMBEDDING_LOCAL_FILES_ONLY", "true").lower() != "false"

DEFAULT_CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "350"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
DEFAULT_TOP_K = int(os.getenv("TOP_K", "3"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))

ABSTENTION_MESSAGE = "I do not know based on the provided documents."
