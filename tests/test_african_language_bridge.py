import json
import sys
from pathlib import Path

import pytest

from app.config import FEATURE_AFRICAN_LANG
from app.language_bridge import SUPPORTED_LANGUAGES, LanguageBridge, detect_language

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = PROJECT_ROOT / "data" / "eval" / "african_language_questions.json"


def load_eval_questions():
    return json.loads(EVAL_PATH.read_text(encoding="utf-8"))["questions"]


class StubTranslator:
    """Deterministic stand-in for the local NLLB model."""

    def __init__(self, to_english: dict, from_english: dict | None = None):
        self.to_english = to_english
        self.from_english = from_english or {}
        self.calls = []

    def available(self) -> bool:
        return True

    def translate(self, text, source_language, target_language):
        self.calls.append((text, source_language, target_language))
        if target_language == "en":
            return self.to_english[text]
        return self.from_english.get(text, text)


class UnavailableTranslator:
    def available(self) -> bool:
        return False

    def translate(self, *args, **kwargs):
        raise AssertionError("translate must not be called when unavailable")


def test_feature_flag_is_disabled_by_default():
    assert FEATURE_AFRICAN_LANG is False


def test_bridge_module_does_not_import_heavy_deps_at_import_time():
    # ctranslate2/transformers must load lazily so the default English product
    # never pays their memory cost.
    assert "ctranslate2" not in sys.modules


def test_eval_set_exists_and_covers_all_three_languages():
    questions = load_eval_questions()
    assert {item["language"] for item in questions} == {"yo", "ha", "sw"}
    for item in questions:
        assert item["question"].strip()
        assert item["english_reference"].strip()


def test_language_detection_on_eval_set():
    for item in load_eval_questions():
        assert detect_language(item["question"]) == item["language"], item["id"]


def test_language_detection_keeps_english_stable():
    english_questions = [
        "What is the payment period in the supplier agreement?",
        "How long do customers have to return unopened retail items?",
        "What is my profit if cost is 7500 and revenue is 10000?",
    ]
    for question in english_questions:
        assert detect_language(question) == "en"


def test_supported_languages():
    assert SUPPORTED_LANGUAGES == {"yo", "ha", "sw"}


def test_bridge_translates_query_and_answer_and_stays_grounded():
    question = "Je, muda wa malipo katika mkataba wa msambazaji ni nini?"
    english = "What is the payment period in the supplier agreement?"
    translator = StubTranslator(
        to_english={question: english},
        from_english={"Payment is due within 30 days.": "Malipo yanapaswa kulipwa ndani ya siku 30."},
    )
    bridge = LanguageBridge(translator=translator)

    seen = {}

    def answer_fn(english_question):
        seen["question"] = english_question
        return {
            "answer": "Payment is due within 30 days.",
            "evidence": [{"source_document": "supplier_agreement.txt", "chunk_id": "c1", "quote": "net 30", "confidence": "high"}],
            "retrieved_chunks": [],
        }

    result = bridge.process(question, answer_fn)

    assert result is not None
    assert seen["question"] == english  # retrieval ran on the English translation
    assert result["answer"] == "Malipo yanapaswa kulipwa ndani ya siku 30."
    assert result["bridge"]["detected_language"] == "sw"
    assert result["bridge"]["english_question"] == english
    assert result["bridge"]["english_answer"] == "Payment is due within 30 days."
    assert result["bridge"]["experimental"] is True
    # Grounding is preserved: evidence still comes from the document store.
    assert result["evidence"][0]["source_document"] == "supplier_agreement.txt"


def test_bridge_returns_none_for_english_questions():
    bridge = LanguageBridge(translator=StubTranslator(to_english={}))
    assert bridge.process("What are the payment terms?", lambda q: {"answer": "x"}) is None


def test_bridge_returns_none_when_translator_unavailable():
    bridge = LanguageBridge(translator=UnavailableTranslator())
    question = "Je, muda wa malipo katika mkataba wa msambazaji ni nini?"
    assert bridge.process(question, lambda q: {"answer": "x"}) is None


def test_chat_disabled_path_never_touches_bridge(monkeypatch):
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    monkeypatch.setattr(backend_main, "FEATURE_AFRICAN_LANG", False)

    def forbidden_bridge():
        raise AssertionError("Bridge must not be constructed when the flag is off")

    monkeypatch.setattr(backend_main, "get_bridge", forbidden_bridge)

    response = TestClient(backend_main.app).post(
        "/chat",
        json={"question": "What is my profit if cost is 7500 and revenue is 10000?"},
    )

    assert response.status_code == 200
    assert "2,500.00" in response.json()["answer"]


def test_chat_enabled_path_bridges_swahili_question(monkeypatch):
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    question = "Je, faida ni nini ikiwa gharama ni 7500 na mapato ni 10000?"
    english = "What is the profit if cost is 7500 and revenue is 10000?"
    translator = StubTranslator(to_english={question: english})

    monkeypatch.setattr(backend_main, "FEATURE_AFRICAN_LANG", True)
    monkeypatch.setattr(backend_main, "get_bridge", lambda: LanguageBridge(translator=translator))

    response = TestClient(backend_main.app).post("/chat", json={"question": question})

    assert response.status_code == 200
    payload = response.json()
    # The English pipeline answered deterministically through the calculator.
    assert payload["bridge"]["detected_language"] == "sw"
    assert payload["answer_source"] == "deterministic_calculator"
    assert "2,500.00" in payload["bridge"]["english_answer"]
