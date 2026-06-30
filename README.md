# Offline SME AI Assistant

An English-only, offline document RAG assistant for SMEs. It runs as a polished local web app with a React + Vite + Tailwind frontend and a FastAPI backend. It loads PDF/TXT business documents, builds a cached local vector index, retrieves evidence, and answers using a small GGUF model through `llama-cpp-python`.

Current phase: English RAG backend integration. The app is intentionally v1-simple: no NLLB, no fine-tuning, no LightRAG, no agents, and no cloud APIs in the product path.

## What It Does

- Upload PDF and TXT documents through a premium dark ADTC-style browser UI.
- Extract and chunk document text.
- Embed chunks locally with Sentence Transformers.
- Cache a local vector index in `indexes/`.
- Retrieve top 3 chunks for each question.
- Generate grounded answers with evidence citations.
- Abstain when the answer is not supported:
  `I do not know based on the provided documents.`
- Run a small product benchmark for latency, memory, and output-format checks.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Model Setup

Place a small quantized GGUF model at:

```text
models/model.gguf
```

Recommended first candidates:

- Qwen2.5-1.5B-Instruct GGUF Q4
- Llama-3.2-1B-Instruct GGUF Q4
- SmolLM2-1.7B-Instruct GGUF Q4

You can also set:

```bash
export MODEL_PATH=/absolute/path/to/model.gguf
export LLM_THREADS=4
export LLM_CTX=2048
```

For a fully offline run, the embedding model must also be present in the local Sentence Transformers cache before disconnecting from the network. The default is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Override it with `EMBEDDING_MODEL_NAME` if you choose another small local embedding model.

By default, the app only uses locally cached embedding files. To pre-cache the default embedding model while online, run once with:

```bash
cd backend
EMBEDDING_LOCAL_FILES_ONLY=false uvicorn main:app --host 127.0.0.1 --port 8000
```

## Run The Web App

Backend:

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`.

For a production-style local run, build the frontend and let FastAPI serve it:

```bash
cd frontend
npm run build
cd ../backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open `http://localhost:8000`.

## Run Tests

```bash
cd backend
python -m compileall app
pytest ../tests -q
cd ../frontend
npm run build
```

## Run Product Benchmark

```bash
cd backend
python -m app.benchmark
```

The benchmark writes `reports/product_smoke_test.json`. It is a local smoke test, not the official ADTC profiler.

## API Endpoints

- `GET /health`: backend/model/index status
- `POST /upload`: upload TXT/PDF files, extract, chunk, embed, and cache the vector index
- `GET /documents`: list indexed documents
- `POST /chat`: ask a question and receive Answer / Evidence plus retrieved chunks
- `POST /tools/calculate`: deterministic profit, margin, discount, and invoice-total calculations

## Repository Layout

```text
backend/             FastAPI backend
frontend/            React + Vite + Tailwind frontend
src/                 Legacy/shared v1 utility modules
data/sample_docs/    Small sample SME documents
models/              Place model.gguf here
indexes/             Cached vector indexes
reports/             Benchmark outputs or notes
tests/               Unit tests
```
