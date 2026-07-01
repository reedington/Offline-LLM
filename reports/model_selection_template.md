# Model Selection Comparison

Fill this table with **real measured values only**. Leave `TBD` until a value
has actually been produced by a benchmark or the ADTC profiler. Do not invent
numbers.

Sources:
- Load success / load time / peak RSS / tokens/sec → `reports/model_benchmark.json`
- Product RSS / product benchmark result → `reports/product_smoke_test.json`
- ADTC profiler report path → `reports/submission.json` (participant mode)

| Model | Quantization | Load success | Load time | Official profiler TPS | First-token latency (profiler) | Model-only RSS (profiler) | Product RSS (full app) | Behavior correctness | Thermal / throttle | ADTC profiler report path | Notes | Decision |
|-------|--------------|--------------|-----------|-----------------------|--------------------------------|---------------------------|------------------------|----------------------|--------------------|---------------------------|-------|----------|
| Qwen2.5-1.5B-Instruct | Q4_K_M | Yes | 11.7 s | 106.9 tok/s | 388 ms | 1209 MB peak | 2046 MB peak | 10/10 behaviors correct (6/6 answerable, 2/2 abstention, 2/2 calculator) | CPU p99 15.2%, throttled=false | reports/submission.json (participant, --skip-accuracy) | Profiler run 2026-07-01 on Apple M4 Pro; params_match=true | leading candidate |
| Llama-3.2-1B-Instruct | Q4_K_M | Yes | 1.2 s | 140.8 tok/s | 287 ms | 930 MB peak | 1839 MB peak | 5/10 behaviors correct (1 format break, 3 false abstentions, 1 hallucinated answer; 2/2 unanswerable, 2/2 calculator OK) | CPU p99 16.7%, throttled=false | reports/submission.llama-3.2-1b.json (participant, --skip-accuracy) | Profiler run 2026-07-02 on Apple M4 Pro; params_match=true. Faster/lighter but quality gap is large | rejected — keep Qwen |
| SmolLM2-1.7B-Instruct | Q4 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | On-device alternative | TBD |
| Gemma-2-2B-it | Q4 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Larger 2B; watch RAM/speed | TBD |
| Llama-3.2-3B-Instruct | Q4 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Do not test until Ubuntu 7 GB validation passes | TBD |

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

### Qwen2.5-1.5B vs Llama-3.2-1B decision rule

The comparison question was: **is Qwen 1.5B worth the extra size versus a
faster 1B baseline?** Answered on 2026-07-02 with measured values (procedure
in `docs/model_comparison.md`):

**Decision: keep Qwen2.5-1.5B-Instruct Q4_K_M.** Llama-3.2-1B is measurably
faster (140.8 vs 101–107 tok/s) and lighter (930 vs ~1210 MB model-only RSS),
but its product behavior is far worse: 5/10 vs 10/10 — it broke the
Answer/Evidence format on one answerable question, falsely abstained on three
others, and hallucinated a wrong "yes" on the opened-hygiene-returns question
(the policy says returns are not allowed unless defective). Accuracy is 50% of
the ADTC score and both models are comfortably inside the RAM/speed budget, so
Qwen's quality advantage is decisive, per the rule below.

- **Keep Qwen2.5-1.5B** if its accuracy/behavior is clearly better (product
  benchmark behaviors, Answer/Evidence discipline, abstention correctness) and
  its RAM and tokens/sec remain safely inside budget.
- **Switch to Llama-3.2-1B** only if Qwen's quality advantage is small **and**
  the 1B is meaningfully faster and/or lighter (speed is 30% of the ADTC
  score, scored relative to the fastest submission).
- **Do not test 3B-class models** until the Ubuntu 22.04 / 7 GB validation
  gate (`docs/ubuntu_7gb_validation.md`) has actually passed.
