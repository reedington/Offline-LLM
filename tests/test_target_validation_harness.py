import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = PROJECT_ROOT / "docker" / "Dockerfile.ubuntu22"
GATE_SCRIPT = PROJECT_ROOT / "scripts" / "run_ubuntu_memory_gate.sh"
DOCS = PROJECT_ROOT / "docs" / "ubuntu_7gb_validation.md"
REPORT = PROJECT_ROOT / "REPORT.md"
DOCKERIGNORE = PROJECT_ROOT / ".dockerignore"


def test_ubuntu_dockerfile_exists_and_targets_ubuntu_22():
    assert DOCKERFILE.exists()
    content = DOCKERFILE.read_text(encoding="utf-8")
    assert "FROM ubuntu:22.04" in content
    assert "models/model.gguf" in content


def test_dockerignore_excludes_model_weights():
    assert DOCKERIGNORE.exists()
    content = DOCKERIGNORE.read_text(encoding="utf-8")
    assert "models/" in content
    assert "*.gguf" in content


def test_memory_gate_script_exists_and_is_executable():
    assert GATE_SCRIPT.exists()
    assert os.access(GATE_SCRIPT, os.X_OK), "run_ubuntu_memory_gate.sh must be executable"


def test_memory_gate_script_has_expected_thresholds():
    content = GATE_SCRIPT.read_text(encoding="utf-8")
    assert "PRODUCT_PEAK_THRESHOLD_MB:-6000" in content
    assert "DANGER_THRESHOLD_MB:-7000" in content
    assert "pytest" in content
    assert "app.model_benchmark" in content
    assert "app.benchmark" in content


def test_validation_docs_exist_and_reference_docker_commands():
    assert DOCS.exists()
    content = DOCS.read_text(encoding="utf-8")
    assert "docker build" in content
    assert "--memory=7g" in content
    assert "Dockerfile.ubuntu22" in content
    assert "run_ubuntu_memory_gate.sh" in content


def test_report_documents_target_hardware_validation():
    content = REPORT.read_text(encoding="utf-8")
    assert "Target Hardware Validation" in content
    assert "TBD" in content
