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

## Validation status and architecture

Two levels of proof, recorded separately in `REPORT.md`:

- **arm64 container run — PASS (2026-07-03).** Docker on Apple Silicon runs
  arm64 Ubuntu. This validates Linux/container/memory discipline: the Ubuntu
  22.04 environment, CPU-only llama.cpp built from source, the full test
  suite, both benchmarks, and RSS peaks (product 1312 MB, model 1242 MB)
  under a hard 7 GB cap with swap disabled — no OOM, no crash. Do not
  overwrite or re-record this result when adding x86 numbers.
- **x86_64 run — TBD.** The ADTC Standard Laptop is x86 (Intel i5 / AMD
  Ryzen 5), so the final hardware-alignment proof must come from one of the
  x86 paths below.

## 4. x86 validation

### Option A: real x86 Ubuntu 22.04 machine (preferred)

On an actual i5/Ryzen-class laptop — this is the only path that also produces
meaningful speed/thermal signals:

```bash
git clone https://github.com/reedington/Offline-LLM.git && cd Offline-LLM
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# place the GGUF at models/model.gguf, then:
./scripts/run_ubuntu_memory_gate.sh
```

To reproduce the hard 7 GB ceiling on bare metal (cgroup cap, swap denied,
same OOM-kill semantics as the container run):

```bash
systemd-run --scope -p MemoryMax=7G -p MemorySwapMax=0 \
  ./scripts/run_ubuntu_memory_gate.sh
```

### Option B: Docker linux/amd64 emulation fallback

From the Apple Silicon dev machine, force an x86 image (QEMU/Rosetta
emulation):

```bash
docker build --platform linux/amd64 \
  -f docker/Dockerfile.ubuntu22 -t adtc-ubuntu22-validation-amd64 .

docker run --rm --platform linux/amd64 \
  --memory=7g --memory-swap=7g --cpus=4 \
  -v "$PWD/models:/app/models:ro" \
  -v "$PWD/reports:/app/reports" \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface:ro" \
  adtc-ubuntu22-validation-amd64
```

Caveats for Option B:

- The build is much slower (llama-cpp-python compiles under emulation) and
  the run may take tens of minutes.
- **Memory and correctness results are valid; speed numbers are not.**
  Emulated tokens/sec says nothing about a real i5/Ryzen — never record
  emulated throughput as a performance claim.
- If the emulated run passes the memory gate, record it as
  "x86 (emulated) PASS" and still seek an Option A run before final
  submission.

## Honesty rules

- Do not claim a validation level passed until that gate has actually been
  run under the memory cap; `REPORT.md` records each level (arm64, x86) as
  TBD until then.
- arm64 PASS validates Linux/container/memory discipline; x86 is the final
  hardware-alignment proof. Neither substitutes for the other.
