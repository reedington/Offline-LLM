from __future__ import annotations

from typing import Iterable, Mapping


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
