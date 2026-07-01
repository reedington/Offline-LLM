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
| Qwen2.5-1.5B-Instruct | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | First candidate | TBD |
| Llama-3.2-1B-Instruct | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Smaller alternative | TBD |
| SmolLM2-1.7B-Instruct | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | On-device alternative | TBD |
| Gemma-2-2B-it | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Larger 2B; watch RAM/speed | TBD |
| Llama-3.2-3B-Instruct | Q4 | models/model.gguf | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Only if headroom allows | TBD |

## Decision policy

- Choose the **smallest** model that clears the accuracy bar.
- Move to a larger model **only** if the measured accuracy gain justifies the
  memory, speed, and thermal cost.
- RAM ceiling: 7 GB. Safe product peak target: 5.5–6 GB.
- A profiler pass is never claimed unless the profiler has actually been run.
