#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from config_loader import valuation_default


def build_discount_rate(macro_data: dict[str, Any], sector_key: str, latest_indicators: dict[str, Any], data_quality: dict[str, Any], manual_override: float | None = None) -> dict[str, Any]:
    selic = macro_data.get("selic")
    ipca_12m = macro_data.get("ipca_12m_estimated")
    risk_free_nominal = (float(selic) / 100.0) if selic is not None else 0.10
    inflation_expectation = (float(ipca_12m) / 100.0) if ipca_12m is not None else 0.045
    real_rate = max(risk_free_nominal - inflation_expectation, 0.03)
    equity_risk_premium = 0.05
    sector_premium = {
        "banks": 0.01,
        "insurance": 0.01,
        "utilities": 0.005,
        "commodities": 0.02,
        "pulp_paper": 0.015,
        "retail": 0.02,
        "holding": 0.015,
    }.get(sector_key, 0.01)
    company_specific_premium = 0.01 if data_quality.get("confidence") in ("medium_low", "low") else 0.0
    leverage_premium = 0.015 if (latest_indicators.get("net_debt_ebitda") or 0) > 3 else 0.0
    ke_normalized = real_rate + inflation_expectation + equity_risk_premium + sector_premium + company_specific_premium + leverage_premium
    ke_spot = risk_free_nominal + equity_risk_premium + sector_premium + company_specific_premium + leverage_premium
    terminal_growth_guard = inflation_expectation + 0.04
    ke_normalized = max(ke_normalized, terminal_growth_guard)
    ke_spot = max(ke_spot, terminal_growth_guard)
    ke_conservative = max(ke_normalized, ke_spot) + 0.01
    wacc = ke_normalized
    if manual_override is not None:
        wacc = float(manual_override)
    return {
        "ke_spot": ke_spot,
        "ke_normalized": ke_normalized,
        "ke_conservative": ke_conservative,
        "wacc": wacc,
        "components": {
            "risk_free_nominal": risk_free_nominal,
            "inflation_expectation": inflation_expectation,
            "real_rate": real_rate,
            "equity_risk_premium": equity_risk_premium,
            "sector_premium": sector_premium,
            "company_specific_premium": company_specific_premium,
            "leverage_premium": leverage_premium,
        },
        "constraints": {
            "min_ke_minus_g_spread": valuation_default("min_ke_minus_g_spread", 0.04),
        },
    }
