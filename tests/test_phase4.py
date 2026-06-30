from __future__ import annotations

import json
import os
import stat
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_model_profiles_module_lists_candidates():
    from app import model_profiles

    assert model_profiles.MODEL_PROFILES
    ids = {profile["id"] for profile in model_profiles.MODEL_PROFILES}
    assert "qwen2_5_1_5b_q4" in ids
    for profile in model_profiles.MODEL_PROFILES:
        assert profile["expected_path"].startswith("models/")
        assert profile["recommended_n_ctx"] > 0
        assert profile["recommended_top_k"] > 0
    # Status reporting must never require the files to exist.
    annotated = model_profiles.profiles_with_status()
    assert all("exists" in profile for profile in annotated)


def test_model_benchmark_handles_no_gguf_files(tmp_path, monkeypatch):
    from app import model_benchmark

    output = tmp_path / "model_benchmark.json"
    monkeypatch.setattr(model_benchmark, "OUTPUT_PATH", output)
    monkeypatch.setattr(model_benchmark, "discover_gguf_files", lambda: [])

    model_benchmark.main()

    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["benchmark"] == "model_benchmark"
    assert payload["models_found"] == []
    assert payload["results"] == []
    assert payload["message"] == "No .gguf models found."
    assert payload["setup_instructions"]


def test_model_benchmark_reports_missing_llama_cpp(tmp_path, monkeypatch):
    from app import model_benchmark

    output = tmp_path / "model_benchmark.json"
    fake_model = tmp_path / "fake.gguf"
    fake_model.write_bytes(b"not-a-real-model")

    monkeypatch.setattr(model_benchmark, "OUTPUT_PATH", output)
    monkeypatch.setattr(model_benchmark, "discover_gguf_files", lambda: [fake_model])
    monkeypatch.setattr(model_benchmark, "llama_cpp_available", lambda: False)

    model_benchmark.main()

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["llama_cpp_available"] is False
    assert payload["results"]
    assert payload["results"][0]["load_success"] is False


def test_adtc_scripts_exist_and_are_executable():
    scripts = [
        "run_adtc_profiler_participant.sh",
        "run_adtc_profiler_audit.sh",
        "compare_adtc_reports.sh",
    ]
    for name in scripts:
        path = PROJECT_ROOT / "scripts" / name
        assert path.exists(), f"missing script: {name}"
        mode = path.stat().st_mode
        assert mode & stat.S_IXUSR, f"script not executable: {name}"


def test_metadata_contains_model_path():
    metadata = json.loads((PROJECT_ROOT / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["model_path"] == "models/model.gguf"
    assert metadata["model_format"] == "GGUF"


def test_benchmark_template_is_valid_json():
    template = PROJECT_ROOT / "reports" / "model_benchmark.template.json"
    payload = json.loads(template.read_text(encoding="utf-8"))
    assert payload["benchmark"] == "model_benchmark"
    assert payload["ram_ceiling_gb"] == 7


def test_no_forbidden_dependencies():
    """Phase 4 must not introduce NLLB, fine-tuning, LightRAG, cloud, or web UIs."""
    requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for forbidden in ("nllb", "lightrag", "streamlit", "gradio", "openai", "anthropic"):
        assert forbidden not in requirements, f"forbidden dependency present: {forbidden}"
