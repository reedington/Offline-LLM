#!/usr/bin/env bash
# Target-hardware memory gate for the ADTC 7 GB RAM ceiling.
#
# Runs the test suite, the internal model benchmark, and the product
# benchmark, then reads the recorded RSS values from the report JSONs and
# fails loudly if they exceed the configured thresholds.
#
# Thresholds (override via environment):
#   PRODUCT_PEAK_THRESHOLD_MB  default 6000  -> gate fails above this
#   DANGER_THRESHOLD_MB        default 7000  -> ADTC disqualification line
#
# Intended to run inside docker/Dockerfile.ubuntu22 with --memory=7g, but it
# also works directly on any host with the project venv installed.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

PRODUCT_PEAK_THRESHOLD_MB="${PRODUCT_PEAK_THRESHOLD_MB:-6000}"
DANGER_THRESHOLD_MB="${DANGER_THRESHOLD_MB:-7000}"

if [ -x "${PROJECT_ROOT}/.venv/bin/python" ]; then
  PYTHON="${PROJECT_ROOT}/.venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

echo "[gate] Python: ${PYTHON}"
echo "[gate] Product peak threshold: ${PRODUCT_PEAK_THRESHOLD_MB} MB"
echo "[gate] Danger (disqualification) threshold: ${DANGER_THRESHOLD_MB} MB"

if [ ! -f "${PROJECT_ROOT}/models/model.gguf" ] && [ -z "${MODEL_PATH:-}" ]; then
  echo "[gate] WARNING: models/model.gguf not found. Benchmarks will record the"
  echo "[gate]          model as missing; mount the GGUF for a full validation run."
fi

failures=0

echo
echo "[gate] Step 1/4: test suite"
if ! (cd backend && "${PYTHON}" -m pytest ../tests -q); then
  echo "[gate] FAIL: test suite failed."
  failures=$((failures + 1))
fi

echo
echo "[gate] Step 2/4: internal model benchmark (reports/model_benchmark.json)"
if ! (cd backend && "${PYTHON}" -m app.model_benchmark); then
  echo "[gate] FAIL: model benchmark did not complete."
  failures=$((failures + 1))
fi

echo
echo "[gate] Step 3/4: product benchmark (reports/product_smoke_test.json)"
if ! (cd backend && "${PYTHON}" -m app.benchmark); then
  echo "[gate] FAIL: product benchmark did not complete."
  failures=$((failures + 1))
fi

echo
echo "[gate] Step 4/4: RSS memory gate"
"${PYTHON}" - "$PRODUCT_PEAK_THRESHOLD_MB" "$DANGER_THRESHOLD_MB" <<'PYCODE'
import json
import sys
from pathlib import Path

product_threshold = float(sys.argv[1])
danger_threshold = float(sys.argv[2])
reports = Path("reports")
exit_code = 0


def read(path: Path) -> dict | None:
    if not path.exists():
        print(f"[gate] MISSING report: {path}")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def check(label: str, value: float | None) -> None:
    global exit_code
    if value is None:
        print(f"[gate] {label}: not recorded")
        return
    status = "OK"
    if value > danger_threshold:
        status = f"FAIL (over {danger_threshold:.0f} MB ADTC danger line)"
        exit_code = 1
    elif value > product_threshold:
        status = f"FAIL (over {product_threshold:.0f} MB gate threshold)"
        exit_code = 1
    print(f"[gate] {label}: {value:.1f} MB -> {status}")


product = read(reports / "product_smoke_test.json")
if product is None:
    exit_code = 1
else:
    peaks = [
        product.get("rss_start_mb"),
        product.get("rss_after_index_mb"),
        product.get("rss_after_generation_mb"),
        product.get("rss_mb"),
    ]
    peaks = [float(v) for v in peaks if v is not None]
    check("Product peak RSS", max(peaks) if peaks else None)

model = read(reports / "model_benchmark.json")
if model is None:
    exit_code = 1
else:
    model_peaks = []
    for entry in model.get("results", []):
        for key in ("rss_after_load_mb", "rss_after_generation_mb"):
            if entry.get(key) is not None:
                model_peaks.append(float(entry[key]))
    check("Model benchmark peak RSS", max(model_peaks) if model_peaks else None)

sys.exit(exit_code)
PYCODE
gate_status=$?
if [ "${gate_status}" -ne 0 ]; then
  failures=$((failures + 1))
fi

echo
if [ "${failures}" -ne 0 ]; then
  echo "[gate] RESULT: FAIL (${failures} failing step(s))."
  echo "[gate] Memory above ${DANGER_THRESHOLD_MB} MB would mean disqualification on the"
  echo "[gate] ADTC 7 GB target; above ${PRODUCT_PEAK_THRESHOLD_MB} MB leaves no safe headroom."
  exit 1
fi
echo "[gate] RESULT: PASS. All steps completed within the memory thresholds."
