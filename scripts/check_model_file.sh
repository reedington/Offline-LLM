#!/usr/bin/env bash
# Check the local GGUF model file: presence, size, and a friendly warning
# against committing large model files. Always exits cleanly.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODEL_FILE="${PROJECT_ROOT}/models/model.gguf"

if [ ! -f "${MODEL_FILE}" ]; then
  echo "[model] No model found at models/model.gguf."
  echo "[model] Place a small quantized GGUF model there (Q4, 1B-2B recommended)."
  echo "[model] See MODEL_SETUP.md for details."
  exit 0
fi

# Portable byte size (macOS: stat -f%z, Linux: stat -c%s).
if size_bytes="$(stat -f%z "${MODEL_FILE}" 2>/dev/null)"; then
  :
else
  size_bytes="$(stat -c%s "${MODEL_FILE}")"
fi

size_mb=$(( size_bytes / 1024 / 1024 ))
# One decimal place for GB using integer math.
size_gb_x10=$(( size_bytes * 10 / 1024 / 1024 / 1024 ))
size_gb="$(( size_gb_x10 / 10 )).$(( size_gb_x10 % 10 ))"

echo "[model] Found: models/model.gguf"
echo "[model] Size: ${size_mb} MB (${size_gb} GB)"

# Warn above 5 GB (5120 MB).
if [ "${size_mb}" -gt 5120 ]; then
  echo "[model] WARNING: this model is larger than 5 GB."
  echo "[model]          It may exceed the 7 GB RAM ceiling once loaded and running."
  echo "[model]          Prefer a smaller Q4 model (1B-2B) unless the profiler shows headroom."
fi

echo "[model] Reminder: do NOT commit model files. models/*.gguf and models/*.bin are gitignored."
exit 0
