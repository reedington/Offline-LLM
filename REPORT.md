# Offline SME AI Assistant Report

## Summary

Current phase: English RAG backend integration. This v1 builds a local English-only RAG assistant for SME business documents. It supports TXT and PDF uploads, local chunk embeddings, cached vector search, GGUF inference, evidence display, and strict abstention when retrieved evidence does not support an answer.

## Current Scope

- Local GGUF loader through `llama-cpp-python`
- React + Vite + Tailwind browser UI
- FastAPI backend
- TXT/PDF document loading
- 350-token approximate chunks with 50-token overlap
- Local embedding model via `sentence-transformers`
- Local vector search with FAISS when available, NumPy fallback otherwise
- Cached index files under `indexes/`
- Top-k retrieval set to 3
- Answer / Evidence output format
- Deterministic calculator helpers
- Product benchmark with latency and rough memory reporting

## Phase 2 Integration

Implemented backend modules under `backend/app/`:

- `config.py`
- `llm.py`
- `document_loader.py`
- `chunking.py`
- `embeddings.py`
- `vector_store.py`
- `rag.py`
- `prompts.py`
- `schemas.py`
- `tools.py`
- `benchmark.py`

Implemented FastAPI endpoints:

- `GET /health`
- `POST /upload`
- `GET /documents`
- `POST /chat`
- `POST /tools/calculate`

## Web App

The app runs with a FastAPI backend and React frontend:

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000

cd ../frontend
npm run dev
```

The Vite frontend proxies backend calls during development. After `npm run build`, FastAPI serves the built frontend from `frontend/dist`.

## Visual Direction

The UI uses a dark ADTC-style product aesthetic: deep premium background, cream typography, amber/gold highlights, rounded dark cards, clear Answer / Evidence cards, offline/local status pills, and practical workspace layout for SME owners.

## Offline Constraints

The app does not call cloud LLM APIs. Runtime model files and embedding model files must already exist locally for a fully offline run.

## Profiling Notes

Default configuration targets a small quantized GGUF model placeholder at `models/model.gguf` with:

- `n_ctx=2048`
- configurable `LLM_THREADS`
- low top-k retrieval
- compact context prompt

The product benchmark reports rough RSS memory through `psutil`.

## Retrieval Strategy

Documents are chunked into approximately 350-token windows with 50-token overlap. Chunks are embedded locally with Sentence Transformers and stored in `indexes/default`. Retrieval uses top-k = 3 by default with FAISS when available and a NumPy similarity fallback otherwise.

## Abstention Strategy

The prompt requires answers only from retrieved context and forbids hidden reasoning. If evidence is missing or retrieval is too weak, the assistant returns exactly:

`I do not know based on the provided documents.`

## Known v1 Limitations

- English only
- No NLLB
- NLLB remains future v1.5 work after English RAG is stable
- No fine-tuning
- No LightRAG
- No OCR for scanned PDFs
- No advanced document permissioning
- No multi-user state management
