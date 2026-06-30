#!/usr/bin/env bash
# Compare a participant submission report against an audit report.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_adtc_common.sh
source "${SCRIPT_DIR}/_adtc_common.sh"

if ! command -v adtc-profiler >/dev/null 2>&1; then
  echo "[adtc] adtc-profiler is not installed or not on PATH."
  echo "       Install it from: https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler"
  exit 1
fi

cd "${ADTC_PROJECT_ROOT}"

missing=0
if [ ! -f "reports/submission.json" ]; then
  echo "[adtc] reports/submission.json not found. Run scripts/run_adtc_profiler_participant.sh first."
  missing=1
fi
if [ ! -f "reports/audit.json" ]; then
  echo "[adtc] reports/audit.json not found. Run scripts/run_adtc_profiler_audit.sh first."
  missing=1
fi
if [ "${missing}" -ne 0 ]; then
  exit 1
fi

echo "[adtc] Comparing participant vs audit reports..."
adtc-profiler compare reports/submission.json reports/audit.json \
  --output reports/verdict.json

echo "[adtc] Done. Wrote reports/verdict.json"
