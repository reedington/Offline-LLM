#!/usr/bin/env bash
set -euo pipefail

mkdir -p models

cat <<'MSG'
No model is downloaded automatically in v1.

Place a small quantized GGUF model at:
  models/model.gguf

Recommended first candidates:
  - Qwen2.5-1.5B-Instruct GGUF Q4
  - Llama-3.2-1B-Instruct GGUF Q4
  - SmolLM2-1.7B-Instruct GGUF Q4

After placing the model, run:
  cd backend
  uvicorn main:app --host 127.0.0.1 --port 8000
MSG
