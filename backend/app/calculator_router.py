"""Deterministic routing for SME finance/business calculator questions.

Calculator-style questions must never be answered by the language model.
`try_calculate` inspects a natural-language question and, when it can parse
the operation and all required inputs with confidence, returns a fully
deterministic Answer/Evidence payload. It returns None for anything it
cannot parse unambiguously, so the question falls through to document RAG.
"""

from __future__ import annotations

import re

from app.tools import (
    calculate_days_until_due,
    calculate_discount,
    calculate_invoice_total,
    calculate_late_payment,
    calculate_margin,
    calculate_payment_due_date,
    calculate_profit,
    calculate_vat,
)

CALCULATOR_SOURCE = "Deterministic business calculator"

_NUMBER = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_CURRENCY = r"(?:₦|\$|€|£|ngn|usd|kes|ghs|zar)?\s*"
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_PERCENT_RE = re.compile(rf"({_NUMBER})\s*(?:%|percent\b)", re.I)
_NET_DAYS_RE = re.compile(rf"\bnet[\s-]*(\d+)\b|\bwithin\s+(\d+)\s+days\b|\b(\d+)[\s-]*day(?:s)?\s+(?:terms?|credit)\b", re.I)
_ITEM_RE = re.compile(
    rf"(\d+)\s*(?:x|×|units?|items?|pcs|pieces)\s*(?:of\s+[\w\s-]{{0,30}}?)?(?:at|@|for|of)\s*{_CURRENCY}({_NUMBER})",
    re.I,
)


def _to_float(raw: str) -> float:
    return float(raw.replace(",", ""))


def _money(value: float) -> str:
    return f"{value:,.2f}"


def _labeled_number(question: str, labels: list[str]) -> float | None:
    for label in labels:
        match = re.search(
            rf"\b{label}\b[\w\s]{{0,20}}?(?:is|are|was|were|of|=|:|at)?\s*{_CURRENCY}({_NUMBER})\b",
            question,
            re.I,
        )
        if match:
            return _to_float(match.group(1))
    return None


def _result(answer: str, operation: str, calculation: str, formula: str, inputs: dict) -> dict:
    inputs_text = ", ".join(f"{key}={value}" for key, value in inputs.items())
    return {
        "answer": answer,
        "evidence": [
            {"source_document": CALCULATOR_SOURCE, "chunk_id": f"{operation}-calculation", "quote": f"Calculation: {calculation}", "confidence": "high"},
            {"source_document": CALCULATOR_SOURCE, "chunk_id": f"{operation}-formula", "quote": f"Formula: {formula}", "confidence": "high"},
            {"source_document": CALCULATOR_SOURCE, "chunk_id": f"{operation}-inputs", "quote": f"Inputs: {inputs_text}", "confidence": "high"},
        ],
        "retrieved_chunks": [],
        "calculation": {"operation": operation, "formula": formula, "inputs": inputs, "calculation": calculation},
        "answer_source": "deterministic_calculator",
    }


def _try_profit_or_margin(question: str) -> dict | None:
    wants_margin = re.search(r"\bmargin\b", question, re.I) is not None
    wants_profit = re.search(r"\bprofit\b", question, re.I) is not None
    if not wants_margin and not wants_profit:
        return None
    cost = _labeled_number(question, ["cost", "costs", "expenses", "spent", "buy", "bought"])
    revenue = _labeled_number(question, ["revenue", "sales", "sell", "sold", "income", "price"])
    if cost is None or revenue is None:
        return None
    if wants_margin:
        margin = calculate_margin(cost=cost, revenue=revenue)
        return _result(
            f"The profit margin is {margin}%.",
            "margin",
            f"(({_money(revenue)} - {_money(cost)}) / {_money(revenue)}) × 100 = {margin}%",
            "margin_percent = ((revenue - cost) / revenue) × 100",
            {"cost": cost, "revenue": revenue},
        )
    profit = calculate_profit(cost=cost, revenue=revenue)
    return _result(
        f"The profit is {_money(profit)}.",
        "profit",
        f"{_money(revenue)} - {_money(cost)} = {_money(profit)}",
        "profit = revenue - cost",
        {"cost": cost, "revenue": revenue},
    )


def _try_discount(question: str) -> dict | None:
    if not re.search(r"\bdiscount(?:ed)?\b", question, re.I):
        return None
    percent_match = _PERCENT_RE.search(question)
    if not percent_match:
        return None
    percent = _to_float(percent_match.group(1))
    remainder = question[: percent_match.start()] + question[percent_match.end() :]
    prices = [_to_float(raw) for raw in re.findall(rf"({_NUMBER})", remainder)]
    prices = [price for price in prices if price != percent]
    if len(prices) != 1:
        return None
    price = prices[0]
    discounted = calculate_discount(original_price=price, discount_percent=percent)
    return _result(
        f"The discounted price is {_money(discounted)}.",
        "discount",
        f"{_money(price)} × (1 - {percent}/100) = {_money(discounted)}",
        "discounted_price = original_price × (1 - discount_percent / 100)",
        {"original_price": price, "discount_percent": percent},
    )


def _try_vat(question: str) -> dict | None:
    if not re.search(r"\bvat\b|\bsales tax\b|\btax\b", question, re.I):
        return None
    percent_match = _PERCENT_RE.search(question)
    rate = _to_float(percent_match.group(1)) if percent_match else None
    remainder = question
    if percent_match:
        remainder = question[: percent_match.start()] + question[percent_match.end() :]
    amounts = [_to_float(raw) for raw in re.findall(rf"({_NUMBER})", remainder)]
    if rate is not None:
        amounts = [amount for amount in amounts if amount != rate]
    if len(amounts) != 1:
        return None
    breakdown = calculate_vat(amounts[0], rate)
    return _result(
        f"VAT at {breakdown['vat_rate_percent']}% on {_money(breakdown['net_amount'])} is "
        f"{_money(breakdown['vat_amount'])}, for a gross total of {_money(breakdown['gross_amount'])}.",
        "vat",
        f"{_money(breakdown['net_amount'])} × {breakdown['vat_rate_percent']}/100 = {_money(breakdown['vat_amount'])}; "
        f"gross = {_money(breakdown['net_amount'])} + {_money(breakdown['vat_amount'])} = {_money(breakdown['gross_amount'])}",
        "vat_amount = net_amount × vat_rate / 100; gross_amount = net_amount + vat_amount",
        {"net_amount": breakdown["net_amount"], "vat_rate_percent": breakdown["vat_rate_percent"]},
    )


def _try_invoice_total(question: str) -> dict | None:
    if not re.search(r"\binvoice\b|\border total\b|\btotal\b", question, re.I):
        return None
    items = [
        {"quantity": int(quantity), "unit_price": _to_float(unit_price)}
        for quantity, unit_price in _ITEM_RE.findall(question)
    ]
    if not items:
        return None
    total = calculate_invoice_total(items)
    lines = " + ".join(f"{item['quantity']} × {_money(item['unit_price'])}" for item in items)
    return _result(
        f"The invoice total is {_money(total)}.",
        "invoice_total",
        f"{lines} = {_money(total)}",
        "invoice_total = Σ(quantity × unit_price)",
        {"items": items},
    )


def _try_payment_terms(question: str) -> dict | None:
    dates = _DATE_RE.findall(question)
    late_intent = re.search(r"\blate\b|\boverdue\b|\bpast due\b", question, re.I)
    due_intent = re.search(r"\bdue\b|\bpay(?:ment)?\b|\bsettle\b", question, re.I)
    if late_intent and len(dates) == 2:
        status = calculate_late_payment(due_date=dates[0], as_of=dates[1])
        if status["is_late"]:
            answer = f"Yes, the payment is late: {status['days_overdue']} day(s) overdue as of {status['as_of']}."
        else:
            answer = f"No, the payment is not late: {status['days_remaining']} day(s) remain until {status['due_date']}."
        return _result(
            answer,
            "late_payment",
            f"{status['as_of']} - {status['due_date']} = {status['days_overdue'] or -status['days_remaining']} day(s) overdue",
            "days_overdue = max(0, as_of_date - due_date)",
            {"due_date": status["due_date"], "as_of": status["as_of"]},
        )
    net_match = _NET_DAYS_RE.search(question)
    if due_intent and net_match and len(dates) == 1:
        net_days = int(next(group for group in net_match.groups() if group))
        due = calculate_payment_due_date(invoice_date=dates[0], net_days=net_days)
        return _result(
            f"The payment is due on {due.isoformat()}.",
            "payment_due_date",
            f"{dates[0]} + {net_days} days = {due.isoformat()}",
            "due_date = invoice_date + net_days",
            {"invoice_date": dates[0], "net_days": net_days},
        )
    if due_intent and len(dates) == 2 and re.search(r"\bdays\b|\bhow long\b", question, re.I):
        remaining = calculate_days_until_due(due_date=dates[1], as_of=dates[0])
        return _result(
            f"There are {remaining} day(s) between {dates[0]} and the due date {dates[1]}."
            if remaining >= 0
            else f"The due date {dates[1]} passed {-remaining} day(s) before {dates[0]}.",
            "days_until_due",
            f"{dates[1]} - {dates[0]} = {remaining} day(s)",
            "days_until_due = due_date - as_of_date",
            {"as_of": dates[0], "due_date": dates[1]},
        )
    return None


_MATCHERS = (_try_payment_terms, _try_invoice_total, _try_discount, _try_vat, _try_profit_or_margin)


def try_calculate(question: str) -> dict | None:
    question = " ".join(question.strip().split())
    if not question:
        return None
    for matcher in _MATCHERS:
        try:
            result = matcher(question)
        except ValueError:
            return None
        if result is not None:
            return result
    return None
