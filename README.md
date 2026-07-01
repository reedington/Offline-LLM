# Offline SME AI Assistant

An English-only, offline document RAG assistant for SMEs. It runs as a polished local web app with a React + Vite + Tailwind frontend and a FastAPI backend. It loads PDF/TXT business documents, builds a cached local vector index, retrieves evidence, and answers using a small GGUF model through `llama-cpp-python`.

Current phase: English RAG backend integration with product-level benchmarking and live metrics. The app is intentionally v1-simple: no NLLB, no fine-tuning, no LightRAG, no agents, and no cloud APIs in the product path.

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

Run backend commands inside the active project virtual environment. Activate it first:

```bash
source .venv/bin/activate
```

```bash
cd backend
python -m compileall app
python -m pytest ../tests -q
cd ../frontend
npm run build
```

Optional backend shortcuts:

```bash
cd backend
make test
make benchmark
make run
```

## Run Product Benchmark

```bash
cd backend
python -m app.benchmark
```

The benchmark writes `reports/product_smoke_test.json`. It is a local smoke test, not the official ADTC profiler.

## Phase 4: Real GGUF Model Testing

Phase 4 prepares the project to test real local GGUF models and compare them before choosing the final competition model. It does **not** add NLLB, African-language mode, fine-tuning, LightRAG, cloud APIs, Streamlit, or Gradio. No model is auto-downloaded — place GGUF files under `models/` yourself.

Recommended first models to test manually:

- Qwen2.5-1.5B-Instruct GGUF Q4
- Llama-3.2-1B-Instruct GGUF Q4
- SmolLM2-1.7B-Instruct GGUF Q4
- Gemma-2-2B-it GGUF Q4
- Llama-3.2-3B-Instruct GGUF Q4 (only if RAM and speed headroom allow)

Workflow:

1. Place the model:

   ```text
   models/model.gguf
   ```

2. Run the backend:

   ```bash
   cd backend
   uvicorn main:app --host 127.0.0.1 --port 8000
   ```

3. Run the frontend:

   ```bash
   cd frontend
   npm run dev
   ```

4. Run the product benchmark:

   ```bash
   cd backend
   python -m app.benchmark
   ```

5. Run the model benchmark:

   ```bash
   cd backend
   python -m app.model_benchmark
   ```

   This detects `.gguf` files under `models/`, loads each through `llama-cpp-python`, runs three short prompts, and writes `reports/model_benchmark.json`. With no models present it writes a valid report saying none were found and prints setup instructions. Token-per-second values are `null` when `llama-cpp-python` does not expose token counts cleanly — they are never faked.

6. Run the ADTC profiler in participant mode:

   ```bash
   ./scripts/run_adtc_profiler_participant.sh
   ```

   Audit mode and comparison are also available:

   ```bash
   ./scripts/run_adtc_profiler_audit.sh
   ./scripts/compare_adtc_reports.sh
   ```

   These scripts check that `adtc-profiler`, `metadata.json`, and `models/model.gguf` are present, and print a friendly message instead of crashing if anything is missing.

### Reports: internal vs official

- `reports/model_benchmark.json` and `reports/product_smoke_test.json` are **internal development reports** produced by this repo.
- `reports/submission.json` (and `audit.json` / `verdict.json`) come from the **official ADTC profiler**. Do not claim a profiler pass unless it has actually been run.

Model configuration profiles for candidate models live in `backend/app/model_profiles.py`. See `reports/adtc_profiler_notes.md` for how the measurements relate and the RAM budget (7 GB ceiling, 5.5–6 GB safe product peak).

## Phase 5: Testing a real GGUF model

Phase 5 is about running the existing Phase 4 tooling against a real model. See `MODEL_SETUP.md` for the full setup guide and `reports/model_selection_template.md` for the comparison table to fill in.

- The reports generated **without** a model are expected — `model_benchmark.json` reports "No .gguf models found" and `product_smoke_test.json` reports `generation_status: model_missing`. That is the correct safe behavior.
- Once you place a model at `models/model.gguf`, the **same commands** produce real model numbers (load time, latency, RSS, tokens/sec):

  ```bash
  cd backend
  python -m app.model_benchmark
  python -m app.benchmark
  ```

  and from the repo root:

  ```bash
  ./scripts/check_model_file.sh          # sanity-check the model file size
  ./scripts/run_adtc_profiler_participant.sh
  ```

- `reports/model_benchmark.json` and `reports/product_smoke_test.json` are **gitignored internal artifacts** — do not commit them.
- **Do not commit large GGUF model files.** `models/` stays gitignored except `models/.gitkeep` (`models/*.gguf` and `models/*.bin` are ignored).

Start with Qwen2.5-1.5B-Instruct Q4. Do not start with 7B, do not use fp16, and only try a 3B model if the profiler shows enough RAM, speed, and thermal headroom.

## API Endpoints

- `GET /health`: backend/model/index status
- `GET /metrics`: product-level RSS memory, model/index status, document/chunk counts, last query latency
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
