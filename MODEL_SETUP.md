# Model Setup

This project runs offline against a small local GGUF model through
`llama-cpp-python`. No model is downloaded automatically — you place the file
yourself.

## 1. Place the model

Put the selected GGUF model at:

```text
models/model.gguf
```

You can also point at a different location without renaming:

```bash
export MODEL_PATH=/absolute/path/to/your-model.gguf
```

## 2. Which model to start with

Start small and quantized. Measure before moving up.

- **Recommended first test model:** Qwen2.5-1.5B-Instruct GGUF Q4
- **Alternative smaller model:** Llama-3.2-1B-Instruct GGUF Q4
- **Alternative on-device model:** SmolLM2-1.7B-Instruct GGUF Q4

Rules of thumb:

- **Do not start with a 7B model.**
- **Do not use fp16 weights.** They are far too large and slow for this target.
- **Prefer Q4 quantization first.**
- **Only try a 3B model** (e.g. Llama-3.2-3B-Instruct GGUF Q4) if the ADTC
  profiler shows enough RAM, speed, and thermal headroom. The RAM ceiling is
  7 GB, and the safe product peak target is 5.5–6 GB.

## 3. Run the benchmarks

Once the model is in place, run the internal benchmarks:

```bash
cd backend
python -m app.model_benchmark
python -m app.benchmark
```

- `model_benchmark` loads the GGUF and records load time, latency, RSS, and
  tokens/sec (when `llama-cpp-python` exposes them) into
  `reports/model_benchmark.json`.
- `benchmark` runs the full product smoke test into
  `reports/product_smoke_test.json`.

## 4. Run the official ADTC profiler

From the repository root:

```bash
./scripts/run_adtc_profiler_participant.sh
```

Audit mode and comparison are also available:

```bash
./scripts/run_adtc_profiler_audit.sh
./scripts/compare_adtc_reports.sh
```

The profiler produces `reports/submission.json` (and `audit.json`/`verdict.json`),
which are the authoritative competition measurements. The `model_benchmark.json`
and `product_smoke_test.json` files are internal development artifacts.

## 5. Do not commit model files

GGUF/bin model files are large and are gitignored (`models/*.gguf`,
`models/*.bin`). Only `models/.gitkeep` is tracked. Never commit a model file.
Use `scripts/check_model_file.sh` to check the file size before running.
