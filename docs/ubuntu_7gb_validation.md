# Ubuntu 22.04 / 7 GB Target Validation

ADTC judges run submissions on the "ADTC Standard Laptop": Ubuntu 22.04 LTS,
CPU-only (integrated graphics), with a hard **7 GB RAM ceiling** — exceeding it
means disqualification. Development happens on macOS/Apple Silicon, so Mac
numbers (including the official profiler run recorded in `REPORT.md`) are
useful signals but **not** target proof.

This validation harness reproduces target-like conditions:

- Ubuntu 22.04 base image (`docker/Dockerfile.ubuntu22`)
- CPU-only `llama-cpp-python` built from source (no Metal, no CUDA)
- Hard container memory cap via `docker run --memory=7g`
- No cloud APIs — the gate runs entirely offline once images/caches exist
- A memory gate script that fails clearly when RSS crosses the thresholds

## Thresholds

| Threshold | Default | Meaning |
|---|---|---|
| `PRODUCT_PEAK_THRESHOLD_MB` | 6000 MB | Gate fails above this — no safe headroom left |
| `DANGER_THRESHOLD_MB` | 7000 MB | The ADTC disqualification line |

Both are environment-overridable, e.g. `PRODUCT_PEAK_THRESHOLD_MB=5500`.

## 1. Build the validation image

From the repository root (model weights are excluded via `.dockerignore` and
must be mounted at runtime):

```bash
docker build -f docker/Dockerfile.ubuntu22 -t adtc-ubuntu22-validation .
```

## 2. Run the memory gate under a 7 GB cap

```bash
docker run --rm \
  --memory=7g --memory-swap=7g \
  --cpus=4 \
  -v "$PWD/models:/app/models:ro" \
  -v "$PWD/reports:/app/reports" \
  adtc-ubuntu22-validation
```

Notes:

- `--memory-swap=7g` (equal to `--memory`) disables swap, so exceeding 7 GB
  OOM-kills the process instead of silently swapping — matching the
  disqualification behavior we need to detect.
- `--cpus=4` approximates a budget i5/Ryzen 5 rather than an M4 Pro.
- The product benchmark needs the embedding model in the local
  Sentence Transformers cache. To run it fully offline in the container, also
  mount your Hugging Face cache read-only:
  `-v "$HOME/.cache/huggingface:/root/.cache/huggingface:ro"`.

The gate script (`scripts/run_ubuntu_memory_gate.sh`) then:

1. Runs the test suite.
2. Runs the internal model benchmark (`app.model_benchmark`).
3. Runs the product benchmark (`app.benchmark`).
4. Reads recorded RSS from `reports/model_benchmark.json` and
   `reports/product_smoke_test.json` and fails if any peak exceeds a
   threshold.

Exit code 0 with `RESULT: PASS` is the pass condition; any threshold breach or
step failure exits 1 with `RESULT: FAIL`.

## 3. Run the gate directly on an Ubuntu machine

On a real Ubuntu 22.04 laptop (the most faithful validation), skip Docker:

```bash
./scripts/run_ubuntu_memory_gate.sh
```

The script uses `.venv/bin/python` when present, `python3` otherwise.

## Honesty rules

- Do not claim Ubuntu validation passed until this gate has actually been run
  under the memory cap; `REPORT.md` records the result as TBD until then.
- Docker on Apple Silicon runs arm64 Ubuntu by default. That validates the
  memory ceiling and CPU-only inference path, but final proof should come from
  an x86_64 run (`--platform linux/amd64`, or a real i5/Ryzen laptop) since
  the ADTC target is x86.
