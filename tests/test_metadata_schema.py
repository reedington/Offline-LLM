import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = PROJECT_ROOT / "metadata.json"


def load_submission_schema():
    jsonschema = pytest.importorskip("jsonschema")
    adtc_profiler = pytest.importorskip("adtc_profiler")
    schema_path = Path(adtc_profiler.__file__).parent / "schema" / "adtc-profiler.schema.json"
    if not schema_path.exists():
        pytest.skip("adtc-profiler schema file not found")
    full_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return jsonschema, full_schema["properties"]["submission"]


def test_metadata_validates_against_installed_profiler_schema():
    jsonschema, submission_schema = load_submission_schema()
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    submission = {key: value for key, value in metadata.items() if not key.startswith("_")}
    jsonschema.validate(instance=submission, schema=submission_schema)


def test_metadata_has_no_placeholder_values():
    text = METADATA_PATH.read_text(encoding="utf-8")
    assert "TODO" not in text, "metadata.json still contains TODO placeholders"


def test_metadata_cross_disciplinary_pairing_is_load_bearing():
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    pairing = metadata["cross_disciplinary_pairing"]
    assert pairing["load_bearing"] is True
    assert "finance" in pairing["discipline"].lower()
