#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def build_quality_of_earnings(financials: list[dict[str, Any]], releases_context: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    latest = financials[-1] if financials else {}
    release_adjustments = []
    for item in releases_context or []:
        for adj in item.get("non_recurring_items") or []:
            release_adjustments.append({
                "type": adj.get("type", "other"),
                "impact": float(adj.get("impact") or adj.get("estimated_impact") or 0.0),
                "source": item.get("source") or "release",
                "confidence": adj.get("confidence", "medium"),
            })
    row_adjustments = []
    for adj in latest.get("non_recurring_items") or []:
        row_adjustments.append({
            "type": adj.get("type", "other"),
            "impact": float(adj.get("impact") or adj.get("estimated_impact") or 0.0),
            "source": adj.get("source") or f"{latest.get('year')}",
            "confidence": adj.get("confidence", "medium"),
        })
    adjustments = row_adjustments + release_adjustments
    total_adjustment = sum(float(item.get("impact") or 0.0) for item in adjustments)
    reported_net_income = float(latest.get("net_income", 0.0) or 0.0)
    reported_ebitda = float(latest.get("ebitda", 0.0) or 0.0)
    reported_fcf = float(latest.get("free_cash_flow", 0.0) or 0.0)
    return {
        "reported_net_income": reported_net_income,
        "adjusted_net_income": reported_net_income - total_adjustment,
        "reported_ebitda": reported_ebitda,
        "adjusted_ebitda": reported_ebitda - max(total_adjustment, 0.0),
        "reported_fcf": reported_fcf,
        "normalized_fcf": reported_fcf - max(total_adjustment, 0.0),
        "adjustments": adjustments,
    }
