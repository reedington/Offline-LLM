#!/usr/bin/env bash
# Run the official ADTC profiler in audit mode (full run, including accuracy).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_adtc_common.sh
source "${SCRIPT_DIR}/_adtc_common.sh"

if ! adtc_preflight; then
  exit 1
fi

cd "${ADTC_PROJECT_ROOT}"

echo "[adtc] Running audit-mode profiler..."
adtc-profiler run \
  --submission . \
  --mode audit \
  --output reports/audit.json

echo "[adtc] Done. Wrote reports/audit.json"
