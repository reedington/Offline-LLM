import pytest

from src.tools import (
    calculate_discount,
    calculate_invoice_total,
    calculate_margin,
    calculate_profit,
)


def test_calculate_profit():
    assert calculate_profit(cost=7500, revenue=10000) == 2500


def test_calculate_margin():
    assert calculate_margin(cost=7500, revenue=10000) == 25


def test_calculate_margin_rejects_zero_revenue():
    with pytest.raises(ValueError):
        calculate_margin(cost=10, revenue=0)


def test_calculate_discount():
    assert calculate_discount(original_price=12000, discount_percent=5) == 11400


def test_calculate_invoice_total():
    items = [{"unit_price": 12000, "quantity": 2}, {"unit_price": 4500, "quantity": 1}]
    assert calculate_invoice_total(items) == 28500
