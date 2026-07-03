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

## Phase 5: Model Selection

Phase 5 runs the Phase 4 tooling against a real model placed manually at `models/model.gguf`. See `MODEL_SETUP.md` for setup and `reports/model_selection_template.md` for the comparison table.

- **Selected model:** Qwen2.5-1.5B-Instruct Q4_K_M — confirmed on 2026-07-02 after a measured head-to-head against Llama-3.2-1B-Instruct Q4_K_M (see "Model speed comparison" below)
- **First candidate:** Qwen2.5-1.5B-Instruct GGUF Q4_K_M (`qwen2.5-1.5b-instruct-q4_k_m.gguf`, ~1.0 GB)
- **Reason:** small, strong, RAM-safe candidate that fits well under the 7 GB ceiling
- **Larger models:** only considered after measurement (Gemma-2-2B-it Q4, then Llama-3.2-3B-Instruct Q4 only if the profiler shows RAM/speed/thermal headroom)

### Measured internal benchmark (Qwen2.5-1.5B-Instruct Q4_K_M, 2026-07-01)

Local run on Apple Silicon (`llama-cpp-python` 0.3.32). Internal artifacts only — the official ADTC profiler has **not** been run yet.

- **Load success:** yes; **load time:** ~11.7 s (`reports/model_benchmark.json`)
- **Peak RSS:** ~2046 MB after generation — well under the 7 GB ceiling and the 5.5–6 GB safe target
- **Tokens/sec:** ~18–56 (per-prompt average across the three benchmark prompts; not official steady-state throughput)
- **First-token latency:** not measured (the internal benchmark records full prompt latency, not time-to-first-token; use the profiler for this)
- **Product benchmark:** 10/10 behaviors correct — 6/6 answerable answered with Answer/Evidence, 2/2 unanswerable returned the exact abstention phrase, 2/2 calculator handled deterministically (`reports/product_smoke_test.json`)

### Official ADTC profiler (participant mode, Qwen2.5-1.5B-Instruct Q4_K_M, 2026-07-01)

Run via `./scripts/run_adtc_profiler_participant.sh` (`adtc-profiler 0.1.0`, schema 1.0.0) on Apple M4 Pro / 24 GB / macOS, `--skip-accuracy`. Report: `reports/submission.json` (gitignored internal artifact).

- **Tokens/sec (generation):** 106.9
- **First-token latency:** 388 ms
- **Peak RSS (model/runtime only):** 1209 MB; steady-state 1172 MB
- **CPU p99:** 15.2%; **throttled:** false
- **Model info:** architecture `qwen2`, `params_match: true` (GGUF fraud check passed)
- **Accuracy:** `[]` (skipped in participant mode)
- **Re-run after Phase 6A metadata fixes (same day, same machine):** 103.6 tok/s, 398 ms first-token latency, 1150 MB peak RSS, throttled false — confirming the profiler accepts the finalized `metadata.json` (github_handle and cross-disciplinary pairing filled).

### Model speed comparison: Qwen2.5-1.5B vs Llama-3.2-1B (2026-07-02)

Measured head-to-head on the same machine (Apple M4 Pro, participant-mode profiler with `--skip-accuracy`, plus the internal benchmarks), following `docs/model_comparison.md`. Question: is Qwen 1.5B worth the extra size versus a faster 1B model?

| Metric | Qwen2.5-1.5B Q4_K_M | Llama-3.2-1B Q4_K_M |
|---|---|---|
| Official profiler TPS | 101–107 tok/s | 140.8 tok/s |
| First-token latency | 366–398 ms | 287 ms |
| Model-only peak RSS | ~1210 MB | 930 MB |
| Product peak RSS | ~2095 MB | 1839 MB |
| Behavior correctness | **10/10** | **5/10** |
| Thermal | throttled=false | throttled=false |

Llama-3.2-1B is ~35% faster and ~280 MB lighter, but its product behavior collapses: it broke the Answer/Evidence format on one answerable question, falsely abstained on three others, and **hallucinated a wrong answer** on the opened-hygiene-returns question (claimed returns are allowed; the policy says they are not unless defective). Accuracy is 50% of the ADTC score while speed is 30% (relative), and both models sit far below the RAM ceiling — so **Qwen2.5-1.5B stays the selected model**. Candidate artifacts: `reports/submission.llama-3.2-1b.json`, `reports/product_smoke_test.llama-3.2-1b.json` (gitignored, kept locally).

### Pending

- **Audit-mode / accuracy run:** TBD — run `./scripts/run_adtc_profiler_audit.sh` (needs `lm_eval`) and `./scripts/compare_adtc_reports.sh`.
- ~~**metadata.json identity fields**~~ — resolved in Phase 6A: `submitter.github_handle` and `cross_disciplinary_pairing` are filled in and `metadata.json` validates against the installed `adtc-profiler` schema (see `tests/test_metadata_schema.py`).

Constraints for this phase: do not start with 7B, do not use fp16, prefer Q4 first. We choose the smallest model that clears the accuracy bar and only move larger if the measured accuracy gain justifies the memory, speed, and thermal cost. No values are invented; internal and profiler numbers above are measured. **Honesty note:** `african_alpha_claim` is set to `false` because the app is currently English-only. African-language support is in the design pipeline (future NLLB work) and the claim should only flip to `true` once that capability actually exists. `model.packaging` is `binary_bundle` (no Dockerfile in the repo).

## Target Hardware Validation (Phase 6B)

All numbers recorded so far — including the official profiler run above — were measured on an Apple M4 Pro with 24 GB RAM. Those are useful signals but **not** final proof for the ADTC target (Ubuntu 22.04, CPU-only i5/Ryzen 5, hard 7 GB RAM ceiling where exceeding it means disqualification).

Phase 6B adds a reproducible target-like validation harness:

- `docker/Dockerfile.ubuntu22` — validation-only Ubuntu 22.04 image; CPU-only `llama-cpp-python` built from source, no Metal assumptions, no model weights baked in (GGUF is mounted at runtime).
- `scripts/run_ubuntu_memory_gate.sh` — runs the test suite, the internal model benchmark, and the product benchmark, then reads the recorded RSS values and fails clearly if any peak exceeds the thresholds: 6000 MB product-peak gate (configurable via `PRODUCT_PEAK_THRESHOLD_MB`) and the 7000 MB ADTC danger line (`DANGER_THRESHOLD_MB`).
- `docs/ubuntu_7gb_validation.md` — how to build and run under a hard cap with `docker build -f docker/Dockerfile.ubuntu22 ...` and `docker run --memory=7g --memory-swap=7g ...`.

**Ubuntu validation result: PASS (2026-07-03, arm64).** The gate ran inside the Ubuntu 22.04 container under a hard cap (`docker run --memory=7g --memory-swap=7g --cpus=4`, swap disabled so a breach OOM-kills, CPU-only llama.cpp compiled from source, models and HF cache mounted read-only):

- Test suite: 74 passed, 1 skipped (profiler schema test — profiler not installed in the image)
- Product benchmark: 10/10 behaviors correct in-container; peak RSS **1312 MB**
- Model benchmark: completed; peak RSS **1242 MB**
- No OOM kill, no crash; both peaks far under the 6000 MB gate threshold and 7000 MB danger line

Caveat: Docker on Apple Silicon runs arm64 Ubuntu, so this validates the memory ceiling, Linux environment, and CPU-only inference path — final proof on x86 still requires a real i5/Ryzen laptop or an `--platform linux/amd64` run. In-container generation speed (~8–28 tok/s across the benchmark prompts on 4 CPUs) is not comparable to the official profiler numbers and is recorded only as evidence the app works on target-like resources.

**x86 Ubuntu validation: TBD.** The arm64 PASS above validates Linux/container/memory discipline; the x86 run is the final hardware-alignment proof since the ADTC Standard Laptop is Intel i5 / AMD Ryzen 5. Commands for both paths (real x86 Ubuntu machine, preferred; `--platform linux/amd64` emulation fallback, memory-valid but speed-meaningless) are in `docs/ubuntu_7gb_validation.md`. The arm64 result stands on its own and is not superseded by the x86 run.

## Cross-Disciplinary Integration (Phase 6A)

The submission pairs document AI with **SME finance and business operations**, and the pairing is load-bearing, not decorative:

- **What it does.** Alongside document RAG, the app ships deterministic business tools: profit, margin, discount, invoice total, VAT/tax with a configurable rate (`DEFAULT_VAT_RATE_PERCENT`, default 7.5%), payment-term due-date calculation (e.g. Net 30), a payment-term day counter, and a late-payment calculator (`backend/app/tools.py`).
- **Why it is load-bearing.** SME users do not only need document Q&A; they need reliable business arithmetic — invoice totals, margins, and payment deadlines — and operational decisions that should not be guessed by a 1.5B language model. Without the finance tools the product does not serve its core SME workflow, so the second discipline carries real functionality.
- **The LLM never does arithmetic.** `backend/app/calculator_router.py` inspects each chat question first. When it can deterministically parse a calculator-style question (operation plus all required inputs), it answers from pure Python — the language model is never invoked (verified by `tests/test_calculator_routing.py`, which fails if the model is called). Anything it cannot parse unambiguously falls through to document RAG.
- **Hallucination reduction.** Deterministic calculation removes the main hallucination surface for numeric questions: results come from audited arithmetic, not sampled tokens, and every calculated answer shows its work in the evidence panel as `Calculation:` / `Formula:` / `Inputs:` lines, so a judge or user can re-verify each number by hand.
- **Answer format.** Document questions keep the standard Answer/Evidence format with document quotes; calculator questions keep the same structure but cite the deterministic calculator as the evidence source.

## Experimental African-Language Bridge (Phase 6D)

**Status: experimental and disabled by default.** The stable, submitted product path is English RAG. `metadata.json` keeps `african_alpha_claim: false` and `language_scope: ["en"]`, and neither claim changes until measured tests pass with a real local translation model.

- **Feature flag:** `FEATURE_AFRICAN_LANG` (default `false`). With the flag off, the bridge is never constructed (enforced by `tests/test_african_language_bridge.py`) and the English path is byte-for-byte unchanged.
- **Architecture:** African-language query → heuristic language detection (Yoruba, Hausa, Swahili) → local translation of the query to English → the existing English calculator/RAG pipeline with document evidence → optional translation of the answer back to the user's language. Evidence always comes from the English document store, so grounding and abstention behavior are preserved.
- **Translation:** NLLB running locally through CTranslate2 int8 (`backend/app/language_bridge.py`), loaded lazily so the default product never pays its memory cost. No cloud APIs. If the local NLLB model directories (`NLLB_CT2_DIR`, `NLLB_TOKENIZER_DIR`) are absent, the bridge reports itself unavailable and questions take the standard English path.
- **Eval set:** `data/eval/african_language_questions.json` — Yoruba, Hausa, and Swahili questions mirroring the English SME eval intents.
- **Tested today (without model weights):** language detection on the eval set, query bridging and grounding with a stub translator, and the disabled path. **Not yet measured:** real NLLB translation quality and memory under the 7 GB budget.
- **Claim policy:** set `african_alpha_claim: true` and extend `language_scope` **only after** the bridge passes measured tests with the real local NLLB model, including memory staying below the safe product target on the Ubuntu 7 GB gate.

## Retrieval Strategy

Documents are chunked into approximately 350-token windows with 50-token overlap. Chunks are embedded locally with Sentence Transformers and stored in `indexes/default`. Retrieval uses top-k = 3 by default with FAISS when available and a NumPy similarity fallback otherwise.

## Abstention Strategy

The prompt requires answers only from retrieved context and forbids hidden reasoning. If evidence is missing or retrieval is too weak, the assistant returns exactly:

`I do not know based on the provided documents.`

## Known v1 Limitations

- English only in the stable path (the Phase 6D African-language bridge is experimental and off by default)
- No NLLB in the product path; local NLLB/CTranslate2 is used only by the disabled-by-default bridge when its model files are present
- No fine-tuning
- No LightRAG
- No OCR for scanned PDFs
- No advanced document permissioning
- No multi-user state management
