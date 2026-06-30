# ADTC Profiler Notes

Two different kinds of measurement are involved in this project. They are
complementary, and **both are needed** before choosing a final model.

## 1. Official ADTC profiler (model/runtime)

- Run via `scripts/run_adtc_profiler_participant.sh` (participant mode) or
  `scripts/run_adtc_profiler_audit.sh` (audit mode).
- Measures the **model and runtime**: load behavior, throughput, latency, and
  resource use as seen by the official tooling.
- Produces `reports/submission.json` (participant) and `reports/audit.json`
  (audit). `scripts/compare_adtc_reports.sh` produces `reports/verdict.json`.
- This is the authoritative measurement for the competition.

## 2. Product benchmark (full app behavior)

- Run via `cd backend && python -m app.benchmark`.
- Measures the **full application**: document loading, chunking, retrieval,
  Answer/Evidence formatting, abstention behavior, per-question latency, and
  process RSS.
- Produces `reports/product_smoke_test.json`.
- This is an internal development report, not an official profiler result.

## 3. Internal model benchmark (candidate comparison)

- Run via `cd backend && python -m app.model_benchmark`.
- Loads any GGUF files under `models/` and runs three short prompts to compare
  candidates before choosing one.
- Produces `reports/model_benchmark.json`.
- Internal only. Token-per-second values are `null` when llama-cpp-python does
  not expose token usage cleanly — they are never fabricated.

## Honesty rules

- Do **not** claim the profiler passed unless it has actually been run and the
  report exists.
- Do **not** invent tokens/sec, latency, RSS, or accuracy values.
- Use `TBD`/`null` placeholders until real measurements exist.

## Resource budget

- RAM ceiling: **7 GB**.
- Safe target: **5.5-6 GB** product peak RSS.
- Prefer the smallest model that clears the accuracy bar. Only move to a larger
  model if the measured accuracy gain justifies the memory, speed, and thermal
  cost.
