from __future__ import annotations

import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.chunking import chunk_documents
from app.config import DEFAULT_INDEX_NAME, FEATURE_AFRICAN_LANG, INDEX_DIR, MODEL_PATH, SAMPLE_DOCS_DIR, TOP_K
from app.language_bridge import get_bridge
from app.document_loader import load_documents
from app.embeddings import EmbeddingModel
from app.llm import LlamaCppLLM, ModelNotFoundError
from app.metrics import build_metrics
from app.rag import RAGAssistant
from app.schemas import CalculateRequest, ChatRequest, DocumentMetadata
from app.calculator_router import try_calculate
from app.tools import (
    calculate_days_until_due,
    calculate_discount,
    calculate_invoice_total,
    calculate_late_payment,
    calculate_margin,
    calculate_payment_due_date,
    calculate_profit,
    calculate_vat,
)
from app.vector_store import VectorStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

app = FastAPI(title="Offline SME AI Assistant", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_store: VectorStore | None = None
embedder: EmbeddingModel | None = None
llm: LlamaCppLLM | None = None
last_query_latency_ms: int | None = None


def get_embedder() -> EmbeddingModel:
    global embedder
    if embedder is None:
        embedder = EmbeddingModel()
    return embedder


def get_llm() -> LlamaCppLLM:
    global llm
    if llm is None:
        llm = LlamaCppLLM()
    return llm


def default_store() -> VectorStore:
    return VectorStore(INDEX_DIR / DEFAULT_INDEX_NAME)


def load_cached_store() -> VectorStore | None:
    global active_store
    if active_store and active_store.ready:
        return active_store
    store = default_store()
    try:
        store.load()
    except FileNotFoundError:
        return None
    active_store = store
    return active_store


@app.get("/health")
def health() -> dict:
    store = load_cached_store()
    return {
        "status": "ok",
        "model_loaded": MODEL_PATH.exists(),
        "index_ready": bool(store and store.ready),
        "documents_count": len(store.documents) if store else 0,
    }


@app.get("/metrics")
def metrics() -> dict:
    store = load_cached_store()
    return build_metrics(store, MODEL_PATH.exists(), last_query_latency_ms)


@app.get("/api/health")
def api_health() -> dict:
    payload = health()
    return {
        **payload,
        "ok": payload["status"] == "ok",
        "service": "offline-sme-ai-assistant",
    }


@app.get("/api/status")
def api_status() -> dict:
    payload = health()
    return {
        "model_exists": payload["model_loaded"],
        "model_path": str(MODEL_PATH),
        "default_top_k": TOP_K,
        "index_ready": payload["index_ready"],
        "documents_count": payload["documents_count"],
        "cached_indexes": sorted(path.name for path in INDEX_DIR.iterdir() if path.is_dir()),
        "service": "offline-sme-ai-assistant",
    }


@app.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(default=[]),
    use_samples: bool = Form(False),
) -> dict:
    global active_store

    paths: list[Path] = []
    if use_samples:
        paths.extend(sorted(SAMPLE_DOCS_DIR.glob("*.txt")))

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for upload in files:
            if not upload.filename:
                continue
            suffix = Path(upload.filename).suffix.lower()
            if suffix not in {".txt", ".pdf"}:
                raise HTTPException(status_code=400, detail=f"{upload.filename} is not a TXT or PDF file.")
            path = tmp_path / Path(upload.filename).name
            path.write_bytes(await upload.read())
            paths.append(path)

        if not paths:
            raise HTTPException(status_code=400, detail="No documents uploaded. Add TXT/PDF files first.")

        try:
            documents = load_documents(paths)
            chunks = chunk_documents(documents)
            document_metadata = [
                DocumentMetadata(
                    filename=document.filename,
                    file_type=document.metadata.get("file_type", ""),
                    characters=len(document.text),
                    chunks=sum(1 for chunk in chunks if chunk.source_document == document.filename),
                )
                for document in documents
            ]
            vectors = get_embedder().embed([chunk.text for chunk in chunks])
            store = default_store()
            store.build(chunks, vectors, document_metadata)
            store.save()
            active_store = store
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "documents": [document.model_dump() for document in document_metadata],
        "chunks": len(chunks),
        "index_ready": True,
        "message": f"Indexed {len(document_metadata)} document(s) into {len(chunks)} chunks.",
    }


@app.post("/api/index/build")
async def api_build_index(
    index_name: str = Form(DEFAULT_INDEX_NAME),
    use_samples: bool = Form(False),
    files: list[UploadFile] = File(default=[]),
) -> dict:
    return await upload_documents(files=files, use_samples=use_samples)


@app.get("/documents")
def documents() -> dict:
    store = load_cached_store()
    return {"documents": [document.model_dump() for document in store.documents] if store else []}


@app.post("/api/index/{index_name}/load")
def api_load_index(index_name: str) -> dict:
    global active_store
    store = default_store()
    try:
        store.load()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    active_store = store
    return {
        "index_name": DEFAULT_INDEX_NAME,
        "chunks": len(store.chunks),
        "documents": [document.model_dump() for document in store.documents],
        "message": f"Loaded cached index '{DEFAULT_INDEX_NAME}'.",
    }


def answer_english(question: str, top_k: int) -> dict:
    """The stable English path: deterministic calculator first, then RAG."""
    calc_result = try_calculate(question)
    if calc_result is not None:
        return calc_result

    store = load_cached_store()
    if not store or not store.ready:
        raise HTTPException(status_code=400, detail="No documents are indexed. Upload documents before asking questions.")

    try:
        assistant = RAGAssistant(store, get_embedder(), get_llm())
        return assistant.answer(question, top_k=top_k)
    except ModelNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    global last_query_latency_ms
    started = time.perf_counter()

    try:
        result = None
        if FEATURE_AFRICAN_LANG:
            result = get_bridge().process(
                request.question,
                lambda english_question: answer_english(english_question, request.top_k),
            )
        if result is None:
            result = answer_english(request.question, request.top_k)
    finally:
        last_query_latency_ms = int((time.perf_counter() - started) * 1000)

    return {**result, "latency_ms": last_query_latency_ms}


@app.post("/api/ask")
async def api_ask(payload: dict) -> dict:
    return await chat(ChatRequest(question=str(payload.get("question", "")), top_k=int(payload.get("top_k") or TOP_K)))


@app.post("/tools/calculate")
def calculate(request: CalculateRequest) -> dict:
    operation = request.operation.strip().lower().replace("_", " ")
    try:
        if operation == "profit":
            result = calculate_profit(_required(request.cost, "cost"), _required(request.revenue, "revenue"))
        elif operation == "margin":
            result = calculate_margin(_required(request.cost, "cost"), _required(request.revenue, "revenue"))
        elif operation == "discount":
            result = calculate_discount(
                _required(request.original_price, "original_price"),
                _required(request.discount_percent, "discount_percent"),
            )
        elif operation in {"invoice total", "invoice_total"}:
            result = calculate_invoice_total(request.items or [])
        elif operation in {"vat", "tax"}:
            result = calculate_vat(_required(request.amount, "amount"), request.vat_rate_percent)
        elif operation in {"payment due date", "due date"}:
            if request.invoice_date is None or request.net_days is None:
                raise ValueError("invoice_date and net_days are required.")
            result = calculate_payment_due_date(request.invoice_date, request.net_days).isoformat()
        elif operation in {"days until due", "payment term days"}:
            if request.due_date is None or request.as_of is None:
                raise ValueError("due_date and as_of are required.")
            result = calculate_days_until_due(request.due_date, request.as_of)
        elif operation in {"late payment", "late payment date"}:
            if request.due_date is None or request.as_of is None:
                raise ValueError("due_date and as_of are required.")
            result = calculate_late_payment(request.due_date, request.as_of)
        else:
            raise ValueError("Unsupported calculator operation.")
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"operation": operation, "result": result}


def _required(value, name: str) -> float:
    if value is None:
        raise ValueError(f"{name} is required.")
    return float(value)


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{path:path}")
def frontend(path: str) -> FileResponse:
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found. Run 'cd frontend && npm run build'.")
    return FileResponse(index)
