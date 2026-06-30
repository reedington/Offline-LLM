"""Safe local model planning/config helper.

This module only describes candidate small GGUF models we may test manually
later. It never downloads anything and does not require any of these files to
exist. The actual runtime model path is still controlled by ``MODEL_PATH`` in
``app.config`` (default ``models/model.gguf``).
"""

from __future__ import annotations

from pathlib import Path

from app.config import MODEL_PATH, PROJECT_ROOT

# Candidate small models, ordered roughly from smallest/fastest to largest.
# These are planning entries only. Place a GGUF file manually under ``models/``
# and point ``MODEL_PATH`` (or ``models/model.gguf``) at it to actually use one.
MODEL_PROFILES: list[dict] = [
    {
        "id": "llama3_2_1b_q4",
        "display_name": "Llama-3.2 1B Instruct Q4",
        "expected_path": "models/llama-3.2-1b-instruct-q4.gguf",
        "recommended_n_ctx": 2048,
        "recommended_top_k": 3,
        "notes": "Smallest candidate. Fast and light; good speed/thermal baseline.",
    },
    {
        "id": "qwen2_5_1_5b_q4",
        "display_name": "Qwen2.5 1.5B Instruct Q4",
        "expected_path": "models/qwen2.5-1.5b-instruct-q4.gguf",
        "recommended_n_ctx": 2048,
        "recommended_top_k": 3,
        "notes": "Strong small model candidate.",
    },
    {
        "id": "smollm2_1_7b_q4",
        "display_name": "SmolLM2 1.7B Instruct Q4",
        "expected_path": "models/smollm2-1.7b-instruct-q4.gguf",
        "recommended_n_ctx": 2048,
        "recommended_top_k": 3,
        "notes": "Compact instruct model; useful comparison point.",
    },
    {
        "id": "gemma2_2b_it_q4",
        "display_name": "Gemma-2 2B IT Q4",
        "expected_path": "models/gemma-2-2b-it-q4.gguf",
        "recommended_n_ctx": 2048,
        "recommended_top_k": 3,
        "notes": "Slightly larger 2B candidate; watch memory and speed headroom.",
    },
    {
        "id": "llama3_2_3b_q4",
        "display_name": "Llama-3.2 3B Instruct Q4",
        "expected_path": "models/llama-3.2-3b-instruct-q4.gguf",
        "recommended_n_ctx": 2048,
        "recommended_top_k": 3,
        "notes": "Only test if RAM and speed headroom allow. 3B is the upper bound.",
    },
]


def get_profile(profile_id: str) -> dict | None:
    """Return a profile by id, or ``None`` if it is not defined."""
    for profile in MODEL_PROFILES:
        if profile["id"] == profile_id:
            return profile
    return None


def resolve_expected_path(profile: dict) -> Path:
    """Resolve a profile's ``expected_path`` against the project root."""
    return (PROJECT_ROOT / profile["expected_path"]).resolve()


def profiles_with_status() -> list[dict]:
    """Return profiles annotated with whether the expected file exists.

    This never requires the files to exist; it only reports presence so the
    benchmark planning output is honest.
    """
    annotated: list[dict] = []
    for profile in MODEL_PROFILES:
        expected = resolve_expected_path(profile)
        annotated.append({**profile, "exists": expected.exists()})
    return annotated


def default_model_path() -> Path:
    """The runtime model path used by the app (default ``models/model.gguf``)."""
    return MODEL_PATH


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            {
                "default_model_path": str(default_model_path()),
                "default_model_exists": default_model_path().exists(),
                "profiles": profiles_with_status(),
            },
            indent=2,
        )
    )
