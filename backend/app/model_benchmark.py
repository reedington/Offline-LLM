"""Local GGUF model benchmark runner.

Run with::

    cd backend
    python -m app.model_benchmark

It detects any ``.gguf`` files under ``models/`` (and ``../models``), tries to
load each one through ``llama-cpp-python``, runs three short prompts, and writes
honest measurements to ``reports/model_benchmark.json``.

Design rules:
- Never download models. The user places GGUF files manually under ``models/``.
- Never crash when no models or no llama-cpp-python are present.
- Never fake numbers. If token counts are not exposed cleanly, report ``null``
  and explain it in the report.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import psutil

from app.config import LLM_CTX, LLM_THREADS, MODEL_DIR, PROJECT_ROOT, REPORTS_DIR

OUTPUT_PATH = REPORTS_DIR / "model_benchmark.json"

# Short, representative prompts. Kept tiny so the benchmark is fast and safe.
PROMPTS: list[dict] = [
    {
        "id": "simple_instruction",
        "kind": "simple instruction",
        "prompt": "List three benefits of keeping business receipts. Answer briefly.",
        "max_tokens": 96,
    },
    {
        "id": "document_grounded",
        "kind": "document-grounded style",
        "prompt": (
            "Context:\n"
            "The supplier agreement states payment is due net 30 days from the invoice date.\n\n"
            "Question: What is the payment period?\n"
            "Answer using only the context above."
        ),
        "max_tokens": 96,
    },
    {
        "id": "abstention",
        "kind": "abstention style",
        "prompt": (
            "Context:\n"
            "The returns policy covers unopened retail items only.\n\n"
            "Question: Who is the company's CFO?\n"
            "If the context does not contain the answer, reply exactly: "
            "I do not know based on the provided documents."
        ),
        "max_tokens": 64,
    },
]

SETUP_INSTRUCTIONS = (
    "No .gguf models were found. Manually download a small quantized GGUF model "
    "(1B-2B Q4 recommended) and place it under the models/ directory, for example "
    "models/model.gguf. Recommended first candidates: Qwen2.5-1.5B-Instruct Q4, "
    "Llama-3.2-1B-Instruct Q4, SmolLM2-1.7B-Instruct Q4, Gemma-2-2B-it Q4, and "
    "Llama-3.2-3B-Instruct Q4 only if RAM and speed headroom allow. Then re-run: "
    "cd backend && python -m app.model_benchmark"
)


def rss_mb(process: psutil.Process) -> float:
    return round(process.memory_info().rss / (1024 * 1024), 1)


def discover_gguf_files() -> list[Path]:
    """Find unique .gguf files under the project ``models/`` directories."""
    search_dirs = [MODEL_DIR, PROJECT_ROOT / "models", Path("models"), Path("../models")]
    seen: dict[str, Path] = {}
    for directory in search_dirs:
        try:
            resolved_dir = directory.resolve()
        except OSError:
            continue
        if not resolved_dir.is_dir():
            continue
        for path in sorted(resolved_dir.glob("*.gguf")):
            seen.setdefault(str(path.resolve()), path.resolve())
    return list(seen.values())


def llama_cpp_available() -> bool:
    try:
        import llama_cpp  # noqa: F401
    except ImportError:
        return False
    return True


def token_count(output: dict, key: str) -> int | None:
    """Best-effort token count from a llama-cpp-python completion result.

    Returns ``None`` (never a fabricated value) when usage is not exposed.
    """
    usage = output.get("usage") if isinstance(output, dict) else None
    if isinstance(usage, dict) and isinstance(usage.get(key), int):
        return usage[key]
    return None


def run_prompt(llm, prompt_spec: dict) -> dict:
    start = time.perf_counter()
    error = None
    text = ""
    completion_tokens = None
    try:
        output = llm(
            prompt_spec["prompt"],
            max_tokens=prompt_spec["max_tokens"],
            temperature=0.1,
        )
        text = output["choices"][0]["text"].strip()
        completion_tokens = token_count(output, "completion_tokens")
    except Exception as exc:  # noqa: BLE001 - benchmark must stay robust
        error = f"{type(exc).__name__}: {exc}"

    latency_ms = int((time.perf_counter() - start) * 1000)
    tokens_per_second = None
    if completion_tokens and latency_ms > 0:
        tokens_per_second = round(completion_tokens / (latency_ms / 1000), 2)

    return {
        "id": prompt_spec["id"],
        "kind": prompt_spec["kind"],
        "prompt_latency_ms": latency_ms,
        "tokens_generated": completion_tokens,
        "approx_tokens_per_second": tokens_per_second,
        "response_preview": text[:300],
        "error": error,
    }


def benchmark_model(path: Path, process: psutil.Process) -> dict:
    rss_before = rss_mb(process)
    entry: dict = {
        "model_file": path.name,
        "model_path": str(path),
        "load_success": False,
        "load_time_ms": None,
        "rss_before_load_mb": rss_before,
        "rss_after_load_mb": None,
        "rss_after_generation_mb": None,
        "total_generation_latency_ms": None,
        "prompts": [],
        "error": None,
        "notes": (
            "tokens_generated/approx_tokens_per_second are null when "
            "llama-cpp-python does not expose usage token counts."
        ),
    }

    load_start = time.perf_counter()
    try:
        from llama_cpp import Llama

        llm = Llama(
            model_path=str(path),
            n_ctx=LLM_CTX,
            n_threads=LLM_THREADS,
            verbose=False,
        )
    except Exception as exc:  # noqa: BLE001 - record the failure, do not crash
        entry["error"] = f"{type(exc).__name__}: {exc}"
        entry["load_time_ms"] = int((time.perf_counter() - load_start) * 1000)
        return entry

    entry["load_success"] = True
    entry["load_time_ms"] = int((time.perf_counter() - load_start) * 1000)
    entry["rss_after_load_mb"] = rss_mb(process)

    gen_start = time.perf_counter()
    for prompt_spec in PROMPTS:
        entry["prompts"].append(run_prompt(llm, prompt_spec))
    entry["total_generation_latency_ms"] = int((time.perf_counter() - gen_start) * 1000)
    entry["rss_after_generation_mb"] = rss_mb(process)

    # Release the model handle promptly so the next model starts from a clean state.
    del llm
    return entry


def build_payload(process: psutil.Process) -> dict:
    gguf_files = discover_gguf_files()
    have_llama = llama_cpp_available()

    payload: dict = {
        "benchmark": "model_benchmark",
        "llama_cpp_available": have_llama,
        "n_ctx": LLM_CTX,
        "n_threads": LLM_THREADS,
        "models_found": [str(path) for path in gguf_files],
        "rss_baseline_mb": rss_mb(process),
        "ram_ceiling_gb": 7,
        "safe_product_peak_gb": "5.5-6",
        "results": [],
        "message": None,
        "setup_instructions": None,
    }

    if not gguf_files:
        payload["message"] = "No .gguf models found."
        payload["setup_instructions"] = SETUP_INSTRUCTIONS
        return payload

    if not have_llama:
        payload["message"] = (
            "Found GGUF files but llama-cpp-python is not installed. "
            "Install it with: pip install llama-cpp-python"
        )
        for path in gguf_files:
            payload["results"].append(
                {
                    "model_file": path.name,
                    "model_path": str(path),
                    "load_success": False,
                    "error": "llama-cpp-python is not installed.",
                }
            )
        return payload

    for path in gguf_files:
        payload["results"].append(benchmark_model(path, process))
    payload["message"] = f"Benchmarked {len(gguf_files)} model file(s)."
    return payload


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    process = psutil.Process()
    payload = build_payload(process)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote {OUTPUT_PATH}")
    print(payload["message"])
    if payload.get("setup_instructions"):
        print()
        print(payload["setup_instructions"])


if __name__ == "__main__":
    main()
