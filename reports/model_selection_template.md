# Model Selection Comparison

Fill this table with **real measured values only**. Leave `TBD` until a value
has actually been produced by a benchmark or the ADTC profiler. Do not invent
numbers.

Sources:
- Load success / load time / peak RSS / tokens/sec → `reports/model_benchmark.json`
- Product RSS / product benchmark result → `reports/product_smoke_test.json`
- ADTC profiler report path → `reports/submission.json` (participant mode)

| Model | Quantization | File path | Load success | Load time | Product RSS | Peak RSS | Tokens/sec | First-token latency | Product benchmark result | ADTC profiler report path | Notes | Decision |
|-------|--------------|-----------|--------------|-----------|-------------|----------|------------|---------------------|--------------------------|---------------------------|-------|----------|
| Qwen2.5-1.5B-Instruct | Q4_K_M | models/model.gguf | Yes | 11.7 s | 2046 MB (full app) | 1209 MB (profiler, model-only) | 106.9 (profiler) | 388 ms (profiler) | 10/10 behaviors correct (6/6 answerable, 2/2 abstention, 2/2 calculator) | reports/submission.json (participant, --skip-accuracy) | Profiler run 2026-07-01 on Apple M4 Pro; params_match=true, throttled=false | leading candidate |
| Llama-3.2-1B-Instruct | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Smaller alternative | TBD |
| SmolLM2-1.7B-Instruct | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | On-device alternative | TBD |
| Gemma-2-2B-it | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Larger 2B; watch RAM/speed | TBD |
| Llama-3.2-3B-Instruct | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Only if headroom allows | TBD |

## Measured notes

- Qwen2.5-1.5B-Instruct Q4_K_M values above come from a local run on
  2026-07-01 (`reports/model_benchmark.json` + `reports/product_smoke_test.json`),
  not the official profiler.
- **Tokens/sec** is a per-prompt average from the internal model benchmark
  (range across the three prompts), not an official steady-state throughput.
- **First-token latency** (388 ms) and **official tokens/sec** (106.9) come from
  the ADTC profiler's `llama-bench` run — the internal benchmark cannot measure
  time-to-first-token.
- **Peak RSS** has two honest readings: ~2046 MB from the full-app product
  benchmark (embeddings + RAG + model) and ~1209 MB from the profiler
  (model/runtime only). Both are under the 7 GB ceiling and the 5.5–6 GB target.
- The ADTC profiler participant run was executed on 2026-07-01 (Apple M4 Pro)
  with `--skip-accuracy`, so `accuracy: []`. GGUF fraud check passed
  (`params_match: true`). Report: `reports/submission.json`.

## Decision policy

- Choose the **smallest** model that clears the accuracy bar.
- Move to a larger model **only** if the measured accuracy gain justifies the
  memory, speed, and thermal cost.
- RAM ceiling: 7 GB. Safe product peak target: 5.5–6 GB.
- A profiler pass is never claimed unless the profiler has actually been run.
