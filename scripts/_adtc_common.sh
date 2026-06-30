#!/usr/bin/env bash
# Shared preflight checks for the ADTC profiler helper scripts.
# Sourced by the other scripts; not meant to be run directly.

# Resolve the project root (parent of this scripts/ directory).
ADTC_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADTC_PROJECT_ROOT="$(cd "${ADTC_SCRIPT_DIR}/.." && pwd)"

adtc_preflight() {
  local ok=0

  if ! command -v adtc-profiler >/dev/null 2>&1; then
    echo "[adtc] adtc-profiler is not installed or not on PATH."
    echo "       Install it from: https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler"
    ok=1
  fi

  if [ ! -f "${ADTC_PROJECT_ROOT}/metadata.json" ]; then
    echo "[adtc] metadata.json not found at ${ADTC_PROJECT_ROOT}/metadata.json"
    ok=1
  fi

  if [ ! -f "${ADTC_PROJECT_ROOT}/models/model.gguf" ]; then
    echo "[adtc] models/model.gguf not found."
    echo "       Place a small quantized GGUF model at models/model.gguf first."
    echo "       Recommended first size: 1B-2B Q4."
    ok=1
  fi

  mkdir -p "${ADTC_PROJECT_ROOT}/reports"

  if [ "${ok}" -ne 0 ]; then
    echo "[adtc] Preflight checks failed. Fix the items above, then re-run."
    return 1
  fi

  echo "[adtc] Preflight checks passed."
  return 0
}
