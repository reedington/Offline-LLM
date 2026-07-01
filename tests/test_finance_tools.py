from datetime import date

import pytest

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


def test_profit():
    assert calculate_profit(cost=7500, revenue=10000) == 2500


def test_margin():
    assert calculate_margin(cost=7500, revenue=10000) == 25


def test_discount():
    assert calculate_discount(original_price=12000, discount_percent=5) == 11400


def test_invoice_total():
    items = [{"unit_price": 12000, "quantity": 2}, {"unit_price": 4500}]
    assert calculate_invoice_total(items) == 28500


def test_vat_with_explicit_rate():
    result = calculate_vat(20000, 7.5)
    assert result["vat_amount"] == 1500
    assert result["gross_amount"] == 21500
    assert result["vat_rate_percent"] == 7.5


def test_vat_uses_configurable_default_rate():
    from app import tools

    result = calculate_vat(1000)
    assert result["vat_rate_percent"] == tools.DEFAULT_VAT_RATE_PERCENT
    assert result["gross_amount"] == round(1000 + 1000 * tools.DEFAULT_VAT_RATE_PERCENT / 100, 2)


def test_vat_rejects_invalid_rate():
    with pytest.raises(ValueError):
        calculate_vat(1000, 250)


def test_payment_due_date():
    assert calculate_payment_due_date("2026-07-01", 30) == date(2026, 7, 31)


def test_payment_due_date_rejects_negative_days():
    with pytest.raises(ValueError):
        calculate_payment_due_date("2026-07-01", -5)


def test_days_until_due():
    assert calculate_days_until_due(due_date="2026-07-31", as_of="2026-07-01") == 30
    assert calculate_days_until_due(due_date="2026-06-01", as_of="2026-07-01") == -30


def test_late_payment_overdue():
    status = calculate_late_payment(due_date="2026-06-01", as_of="2026-07-01")
    assert status["is_late"] is True
    assert status["days_overdue"] == 30
    assert status["days_remaining"] == 0


def test_late_payment_not_yet_due():
    status = calculate_late_payment(due_date="2026-07-15", as_of="2026-07-01")
    assert status["is_late"] is False
    assert status["days_overdue"] == 0
    assert status["days_remaining"] == 14
