from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"
INDEX_DIR = PROJECT_ROOT / "indexes"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODEL_DIR = PROJECT_ROOT / "models"

MODEL_PATH = Path(os.getenv("MODEL_PATH", MODEL_DIR / "model.gguf")).expanduser()
DEFAULT_INDEX_NAME = os.getenv("INDEX_NAME", "default")

LLM_CTX = int(os.getenv("LLM_CTX", "2048"))
LLM_THREADS = int(os.getenv("LLM_THREADS", str(max(1, min((os.cpu_count() or 2) // 2, 6)))))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "512"))

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_LOCAL_FILES_ONLY = os.getenv("EMBEDDING_LOCAL_FILES_ONLY", "true").lower() != "false"

CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "350"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "3"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))

ABSTENTION_MESSAGE = "I do not know based on the provided documents."

# Experimental African-language bridge (Phase 6D). Disabled by default; the
# stable product path is English RAG. No cloud APIs: translation only works
# when a local NLLB CTranslate2 model directory is present.
FEATURE_AFRICAN_LANG = os.getenv("FEATURE_AFRICAN_LANG", "false").lower() == "true"
NLLB_CT2_DIR = Path(os.getenv("NLLB_CT2_DIR", MODEL_DIR / "nllb-ct2")).expanduser()
NLLB_TOKENIZER_DIR = Path(os.getenv("NLLB_TOKENIZER_DIR", MODEL_DIR / "nllb-tokenizer")).expanduser()
