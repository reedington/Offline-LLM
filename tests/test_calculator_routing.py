import pytest

from app.calculator_router import CALCULATOR_SOURCE, try_calculate


class ForbiddenLLM:
    """Fails the test if the chat path ever asks the model to generate."""

    def generate(self, prompt, max_tokens=512):
        raise AssertionError("Calculator questions must not reach the language model.")


def evidence_quotes(result):
    return [item["quote"] for item in result["evidence"]]


def assert_calculator_shape(result):
    assert result["answer_source"] == "deterministic_calculator"
    quotes = evidence_quotes(result)
    assert any(quote.startswith("Calculation:") for quote in quotes)
    assert any(quote.startswith("Formula:") for quote in quotes)
    assert any(quote.startswith("Inputs:") for quote in quotes)
    assert all(item["source_document"] == CALCULATOR_SOURCE for item in result["evidence"])
    assert result["retrieved_chunks"] == []


def test_routes_profit_question():
    result = try_calculate("What is my profit if the cost is 7,500 and the revenue is 10,000?")
    assert result is not None
    assert "2,500.00" in result["answer"]
    assert_calculator_shape(result)


def test_routes_margin_question():
    result = try_calculate("What margin do I make when cost is 7500 and revenue is 10000?")
    assert result is not None
    assert "25" in result["answer"]
    assert_calculator_shape(result)


def test_routes_discount_question():
    result = try_calculate("What is the price after a 5% discount on 12000?")
    assert result is not None
    assert "11,400.00" in result["answer"]
    assert_calculator_shape(result)


def test_routes_invoice_total_question():
    result = try_calculate("What is the invoice total for 2 units at 12000 and 1 item at 4500?")
    assert result is not None
    assert "28,500.00" in result["answer"]
    assert_calculator_shape(result)


def test_routes_vat_question():
    result = try_calculate("How much VAT at 7.5% do I add on 20000?")
    assert result is not None
    assert "1,500.00" in result["answer"]
    assert "21,500.00" in result["answer"]
    assert_calculator_shape(result)


def test_routes_payment_due_date_question():
    result = try_calculate("An invoice dated 2026-07-01 has net 30 terms. When is payment due?")
    assert result is not None
    assert "2026-07-31" in result["answer"]
    assert_calculator_shape(result)


def test_routes_late_payment_question():
    result = try_calculate("The payment was due 2026-06-01 and today is 2026-07-01. Is it late?")
    assert result is not None
    assert "30 day(s) overdue" in result["answer"]
    assert_calculator_shape(result)


def test_document_questions_fall_through_to_rag():
    assert try_calculate("What is the payment period in the supplier agreement?") is None
    assert try_calculate("How long do customers have to return unopened retail items?") is None
    assert try_calculate("Summarize the supplier agreement.") is None


def test_ambiguous_numeric_question_falls_through():
    assert try_calculate("What is the profit outlook for 2026?") is None


def test_chat_endpoint_answers_calculator_without_model_or_index(monkeypatch):
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    monkeypatch.setattr(backend_main, "active_store", None)
    monkeypatch.setattr(backend_main, "load_cached_store", lambda: None)
    monkeypatch.setattr(backend_main, "get_llm", lambda: ForbiddenLLM())

    response = TestClient(backend_main.app).post(
        "/chat",
        json={"question": "What is my profit if cost is 7500 and revenue is 10000?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "2,500.00" in payload["answer"]
    assert payload["answer_source"] == "deterministic_calculator"
    assert isinstance(payload["latency_ms"], int)


def test_calculate_endpoint_supports_new_operations():
    pytest.importorskip("fastapi.testclient")
    from fastapi.testclient import TestClient
    from app import main as backend_main

    client = TestClient(backend_main.app)

    vat = client.post("/tools/calculate", json={"operation": "vat", "amount": 20000, "vat_rate_percent": 7.5})
    assert vat.status_code == 200
    assert vat.json()["result"]["gross_amount"] == 21500

    due = client.post(
        "/tools/calculate",
        json={"operation": "payment_due_date", "invoice_date": "2026-07-01", "net_days": 30},
    )
    assert due.status_code == 200
    assert due.json()["result"] == "2026-07-31"

    late = client.post(
        "/tools/calculate",
        json={"operation": "late_payment", "due_date": "2026-06-01", "as_of": "2026-07-01"},
    )
    assert late.status_code == 200
    assert late.json()["result"]["days_overdue"] == 30
