# Model Comparison Workflow

How to benchmark a candidate GGUF against the current selection **without
changing the selected model**. The active model path stays
`models/model.gguf`; candidates are swapped in and out of that path only for
the duration of a measurement run.

Current question: **is Qwen2.5-1.5B-Instruct Q4_K_M worth the extra size
versus a faster Llama-3.2-1B-Instruct Q4_K_M baseline?**

## Rules

- `models/model.gguf` remains the single active model path used by the app,
  the benchmarks, and the profiler. Do not add per-model config.
- **Never commit GGUF files.** They stay under `models/` (gitignored) only.
- Record **measured values only** in
  `reports/model_selection_template.md` — `TBD` until a number exists.
- The selected model does not change until the decision rule in the template
  says so.

## Swapping a candidate in safely

```bash
cd /path/to/ADTC

# 1. Keep the current selection safe.
mv models/model.gguf models/qwen2.5-1.5b-instruct-q4_k_m.gguf.bak

# 2. Place the candidate at the active path (example: Llama-3.2-1B Q4_K_M).
cp /path/to/Llama-3.2-1B-Instruct-Q4_K_M.gguf models/model.gguf
```

## Measurement run (same commands for every candidate)

```bash
cd backend
../.venv/bin/python -m app.model_benchmark
../.venv/bin/python -m app.benchmark
cd ..
./scripts/run_adtc_profiler_participant.sh
```

Outputs to collect per candidate:

| Value | Source |
|---|---|
| Official profiler TPS, first-token latency | `reports/submission.json` (`throughput`) |
| Model-only RSS, thermal/throttle | `reports/submission.json` (`memory`, `cpu_thermal`) |
| Load success / load time | `reports/model_benchmark.json` |
| Product RSS (full app) | `reports/product_smoke_test.json` |
| Behavior correctness (answerable / abstention / calculator) | `reports/product_smoke_test.json` |

Copy each candidate's `reports/submission.json` aside before the next run
(e.g. `reports/submission.llama-3.2-1b.json`) so results are not overwritten.

## Restoring the selected model

```bash
mv models/qwen2.5-1.5b-instruct-q4_k_m.gguf.bak models/model.gguf
```

Re-run the three commands above once after restoring so the `reports/*.json`
artifacts again describe the selected model.

## Recording the result

Fill the candidate's row in `reports/model_selection_template.md` and apply
the decision rule written there:

- Keep Qwen2.5-1.5B if accuracy/behavior is clearly better and RAM/TPS remain
  safe.
- Pick the 1B only if Qwen's quality advantage is small and the 1B is
  meaningfully faster or lighter.
- Do not test 3B-class models until the Ubuntu 22.04 / 7 GB validation gate
  has passed (`docs/ubuntu_7gb_validation.md`).
