from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Iterable, Mapping

DEFAULT_VAT_RATE_PERCENT = float(os.getenv("DEFAULT_VAT_RATE_PERCENT", "7.5"))


def calculate_profit(cost: float, revenue: float) -> float:
    return round(float(revenue) - float(cost), 2)


def calculate_margin(cost: float, revenue: float) -> float:
    revenue = float(revenue)
    if revenue == 0:
        raise ValueError("revenue must be non-zero.")
    return round(((revenue - float(cost)) / revenue) * 100, 2)


def calculate_discount(original_price: float, discount_percent: float) -> float:
    original_price = float(original_price)
    discount_percent = float(discount_percent)
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("discount_percent must be between 0 and 100.")
    return round(original_price * (1 - discount_percent / 100), 2)


def calculate_invoice_total(items: Iterable[Mapping[str, float]]) -> float:
    total = 0.0
    for item in items:
        quantity = float(item.get("quantity", 1))
        unit_price = float(item["unit_price"])
        total += quantity * unit_price
    return round(total, 2)


def calculate_vat(amount: float, vat_rate_percent: float | None = None) -> dict:
    """Placeholder VAT/tax calculation with a configurable rate (default 7.5%)."""
    amount = float(amount)
    rate = DEFAULT_VAT_RATE_PERCENT if vat_rate_percent is None else float(vat_rate_percent)
    if rate < 0 or rate > 100:
        raise ValueError("vat_rate_percent must be between 0 and 100.")
    vat_amount = round(amount * rate / 100, 2)
    return {
        "net_amount": round(amount, 2),
        "vat_rate_percent": rate,
        "vat_amount": vat_amount,
        "gross_amount": round(amount + vat_amount, 2),
    }


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def calculate_payment_due_date(invoice_date: str | date, net_days: int) -> date:
    """Payment-term calculator: invoice date + net payment days (e.g. Net 30)."""
    net_days = int(net_days)
    if net_days < 0:
        raise ValueError("net_days must be zero or positive.")
    return _parse_date(invoice_date) + timedelta(days=net_days)


def calculate_days_until_due(due_date: str | date, as_of: str | date) -> int:
    """Payment-term day counter: positive = days remaining, negative = days overdue."""
    return (_parse_date(due_date) - _parse_date(as_of)).days


def calculate_late_payment(due_date: str | date, as_of: str | date) -> dict:
    """Late-payment calculator: whether a payment is late as of a date, and by how many days."""
    remaining = calculate_days_until_due(due_date, as_of)
    return {
        "due_date": _parse_date(due_date).isoformat(),
        "as_of": _parse_date(as_of).isoformat(),
        "is_late": remaining < 0,
        "days_overdue": max(0, -remaining),
        "days_remaining": max(0, remaining),
    }
