# Offline SME AI Assistant Report

## Summary

Current phase: English RAG backend integration with product benchmarking and live metrics. This v1 builds a local English-only RAG assistant for SME business documents. It supports TXT and PDF uploads, local chunk embeddings, cached vector search, GGUF inference, evidence display, strict abstention when retrieved evidence does not support an answer, and product-level memory/status instrumentation.

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
- `GET /metrics`
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

## Phase 3 Benchmarking

Product smoke benchmark command:

```bash
cd backend
python -m app.benchmark
```

Output path:

```text
reports/product_smoke_test.json
```

The benchmark measures:

- sample document loading
- chunking and local index build/load
- top-k retrieval behavior
- calculator question handling
- model-missing behavior when `models/model.gguf` is absent
- per-question latency
- process RSS memory through `psutil`

Profiler placeholders:

- model name: TBD
- quantization: TBD
- tokens/sec from ADTC profiler: TBD
- first-token latency: TBD
- product RSS memory: TBD
- peak RSS memory: TBD
- temperature/throttling status: TBD
- retrieval accuracy notes: TBD
- abstention behavior notes: TBD

## Phase 4: Model Testing and Profiler Integration

Phase 4 prepares the project to test real local GGUF models and compare them honestly before choosing the final competition model. No NLLB, African-language mode, fine-tuning, LightRAG, cloud APIs, Streamlit, or Gradio were added. No model is auto-downloaded; GGUF files are placed manually under `models/`.

Added tooling:

- `backend/app/model_profiles.py`: candidate model configuration profiles (planning only; files are not required to exist).
- `backend/app/model_benchmark.py`: loads each GGUF under `models/`, runs three short prompts, and writes `reports/model_benchmark.json`. Safe when no models or no `llama-cpp-python` are present.
- `scripts/run_adtc_profiler_participant.sh`, `scripts/run_adtc_profiler_audit.sh`, `scripts/compare_adtc_reports.sh`: friendly wrappers around the official ADTC profiler.
- `reports/model_benchmark.template.json` and `reports/adtc_profiler_notes.md`.

Measurement placeholders (to be filled only with real measured values):

- Selected model: TBD
- Quantization: TBD
- Model path: `models/model.gguf`
- Product benchmark: `reports/product_smoke_test.json`
- Model benchmark: `reports/model_benchmark.json`
- ADTC participant report: `reports/submission.json`
- Tokens/sec: TBD
- First-token latency: TBD
- Peak RSS: TBD
- Product RSS: TBD
- Thermal status: TBD
- Decision: TBD

Decision policy:

- We will choose the smallest model that clears the accuracy bar.
- A larger model is only used if the measured accuracy gain justifies the memory, speed, and thermal cost.
- We do not invent values. `TBD`/`null` placeholders remain until real measurements exist.
- RAM ceiling is 7 GB; safe target is 5.5–6 GB product peak RSS.

The official ADTC profiler (`reports/submission.json`) measures the model/runtime. The product benchmark (`reports/product_smoke_test.json`) and internal model benchmark (`reports/model_benchmark.json`) measure full app behavior and candidate comparison. Both kinds of measurement are needed, and a profiler pass is never claimed unless actually run.

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
