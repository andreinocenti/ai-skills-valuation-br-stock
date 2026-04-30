#!/usr/bin/env python3
"""Shared deterministic engine for valuation-br-stock scripts."""

from __future__ import annotations

import csv
import json
import math
import re
import statistics
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_OFFICIAL = "oficial"
SOURCE_AUXILIARY = "auxiliar"
SOURCE_ESTIMATED = "estimado"
SOURCE_INFERRED = "inferido"
SOURCE_NOT_FOUND = "nao_encontrado"
SKILL_VERSION = "valuation-br-stock"
CALCULATION_ENGINE_VERSION = "valuation-br-stock-2026-04-30-ceiling-v3"

VERDICTS = [
    "Evitar",
    "Cara",
    "Justa",
    "Interessante",
    "Atrativa com margem de seguranca",
]

NON_RECURRING_PATTERNS = [
    "nao recorrente",
    "extraordinario",
    "venda de ativo",
    "impairment",
    "reversao",
    "credito tributario",
    "efeito cambial",
    "provisao",
    "acordo judicial",
    "evento nao caixa",
]

CVM_ACCOUNT_MAP = {
    "revenue": ["3.01", "3.01.01"],
    "gross_profit": ["3.03"],
    "ebit": ["3.05", "3.05.01"],
    "net_income": ["3.11", "3.13", "3.99"],
    "cash": ["1.01.01"],
    "equity": ["2.03"],
    "gross_debt_short": ["2.01.04", "2.01.04.01", "2.01.04.02"],
    "gross_debt_long": ["2.02.01", "2.02.01.01", "2.02.01.02"],
    "operating_cash_flow": ["6.01"],
    "depreciation_amortization": ["6.01.01.01"],
    "capex": ["6.02.01", "6.02.02"],
}

KNOWN_B3_COMPANIES = {
    "CMIG3": {"name": "CEMIG", "cvm_code": "2453", "sector": "Energia eletrica", "share_class": "ON"},
    "CMIG4": {"name": "CEMIG", "cvm_code": "2453", "sector": "Energia eletrica", "share_class": "PN"},
    "BBAS3": {"name": "BANCO DO BRASIL", "cvm_code": "1023", "sector": "Bancos", "share_class": "ON"},
    "VALE3": {"name": "VALE", "cvm_code": "4170", "sector": "Mineracao e commodities", "share_class": "ON"},
    "PETR3": {"name": "PETROBRAS", "cvm_code": "9512", "sector": "Petroleo e gas", "share_class": "ON"},
    "PETR4": {"name": "PETROBRAS", "cvm_code": "9512", "sector": "Petroleo e gas", "share_class": "PN"},
    "ITUB4": {"name": "ITAU UNIBANCO", "cvm_code": "19348", "sector": "Bancos", "share_class": "PN"},
    "BBDC4": {"name": "BRADESCO", "cvm_code": "906", "sector": "Bancos", "share_class": "PN"},
    "TAEE11": {"name": "TAESA", "cvm_code": "20257", "sector": "Energia eletrica", "share_class": "UNIT"},
    "BBSE3": {"name": "BB SEGURIDADE", "cvm_code": "23159", "sector": "Seguradoras", "share_class": "ON"},
    "LREN3": {"name": "LOJAS RENNER", "cvm_code": "8133", "sector": "Varejo", "share_class": "ON"},
    "MGLU3": {"name": "MAGAZINE LUIZA", "cvm_code": "22470", "sector": "Varejo", "share_class": "ON"},
    "SAPR11": {"name": "SANEPAR", "cvm_code": "18627", "sector": "Saneamento", "share_class": "UNIT"},
    "SBSP3": {"name": "SABESP", "cvm_code": "14443", "sector": "Saneamento", "share_class": "ON"},
    "ITSA4": {"name": "ITAUSA", "cvm_code": "7617", "sector": "Holding", "share_class": "PN"},
    "BRAP4": {"name": "BRADESPAR", "cvm_code": "18724", "sector": "Holding", "share_class": "PN"},
}

SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, indent=2)


def load_reference_json(name: str, default: Any) -> Any:
    path = SKILL_ROOT / "references" / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def ticker_registry() -> dict[str, dict[str, Any]]:
    rows = load_reference_json("ticker_registry.json", [])
    return {row["ticker"].upper(): row for row in rows}


def peer_groups() -> dict[str, list[str]]:
    return load_reference_json("peer_groups.json", {})


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_div(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if denominator in (None, 0):
        return None
    if numerator is None:
        return None
    return float(numerator) / float(denominator)


def average(values: list[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return sum(clean) / len(clean) if clean else None


def median(values: list[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return statistics.median(clean) if clean else None


def cagr(start: float | None, end: float | None, periods: int) -> float:
    if not start or not end or start <= 0 or end <= 0 or periods <= 0:
        return 0.0
    return (end / start) ** (1 / periods) - 1


def latest(financials: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(financials, key=lambda row: row["year"])[-1]


def order_years(financials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(financials, key=lambda row: row["year"])


def per_share(value: float | int | None, shares: float | int | None) -> float | None:
    return safe_div(value, shares)


def source_entry(name: str, kind: str, status: str = "confirmed", url: str | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "type": kind,
        "status": status,
        "url": url,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def normalize_financials(input_data: dict[str, Any]) -> dict[str, Any]:
    data = json.loads(json.dumps(input_data))
    normalized = []
    for row in order_years(data.get("financials", [])):
        copy = dict(row)
        non_recurring = copy.get("non_recurring_items") or []
        impact = sum(float(item.get("impact", 0)) for item in non_recurring)
        copy["net_income_reported"] = copy.get("net_income")
        copy["net_income_adjusted"] = copy.get("net_income", 0) - impact
        copy["dividends_reported"] = copy.get("dividends_paid", 0)
        extraordinary_dividends = float(copy.get("extraordinary_dividends", 0))
        copy["dividends_recurring"] = max(copy.get("dividends_paid", 0) - extraordinary_dividends, 0)
        copy["free_cash_flow_reported"] = copy.get("free_cash_flow", 0)
        copy["free_cash_flow_adjusted"] = copy.get("free_cash_flow", 0) - max(impact, 0)
        copy["net_debt"] = copy.get("gross_debt", 0) - copy.get("cash", 0)
        copy["basis"] = copy.get("basis", "consolidado")
        normalized.append(copy)
    data["financials"] = normalized
    data.setdefault("sources", [])
    data.setdefault("limitations", [])
    if not data["sources"]:
        data["sources"].append(source_entry("input estruturado", SOURCE_INFERRED, "provided"))
    return data


def detect_non_recurring_from_text(text: str) -> list[dict[str, Any]]:
    lower = text.lower()
    items = []
    for pattern in NON_RECURRING_PATTERNS:
        if pattern in lower:
            items.append({
                "description": pattern,
                "estimated_impact": None,
                "confidence": "medium",
            })
    return items


def classify_dividend_event(amount: float, median_amount: float | None = None, description: str = "") -> dict[str, Any]:
    text = description.lower()
    event_type = "jcp" if "jcp" in text or "juros" in text else "dividendo"
    if any(term in text for term in ("extra", "extraordin", "capital", "amortiza", "restitui")):
        event_type = "extraordinario"
    if median_amount and median_amount > 0 and amount > median_amount * 3:
        event_type = "extraordinario"
    return {
        "amount_per_share": amount,
        "event_type": event_type,
        "is_recurring": event_type in ("dividendo", "jcp"),
    }


def normalize_dividend_events(raw_amounts: list[Any]) -> list[dict[str, Any]]:
    amounts = [
        float(item.get("amount_per_share", item.get("amount", 0))) if isinstance(item, dict) else float(item)
        for item in raw_amounts
        if (item.get("amount_per_share", item.get("amount")) if isinstance(item, dict) else item) is not None
    ]
    med = median(amounts)
    events = []
    for index, raw in enumerate(raw_amounts):
        if isinstance(raw, dict):
            amount = raw.get("amount_per_share", raw.get("amount"))
            if amount is None:
                continue
            item = classify_dividend_event(float(amount), med, raw.get("description", ""))
            item.update({
                "date": raw.get("date") or str(index + 1),
                "year": raw.get("year"),
                "source_status": raw.get("source_status", SOURCE_AUXILIARY),
            })
        else:
            item = classify_dividend_event(float(raw), med)
            item.update({"date": str(index + 1), "year": None, "source_status": SOURCE_AUXILIARY})
        events.append(item)
    return events


def calculate_indicators(input_data: dict[str, Any]) -> dict[str, Any]:
    data = normalize_financials(input_data)
    financials = order_years(data["financials"])
    current_price = data.get("market_data", {}).get("current_price")
    yearly = []
    for row in financials:
        shares = row.get("shares_outstanding")
        net_income = row.get("net_income_adjusted", row.get("net_income"))
        dividends = row.get("dividends_recurring", row.get("dividends_paid"))
        fcf = row.get("free_cash_flow_adjusted", row.get("free_cash_flow"))
        ebit = row.get("ebit", row.get("ebitda", 0) - row.get("depreciation_amortization", 0))
        nopat = ebit * (1 - row.get("tax_rate", 0.34))
        invested_capital = row.get("equity", 0) + row.get("net_debt", 0)
        enterprise_value = None
        if current_price and shares:
            enterprise_value = current_price * shares + row.get("net_debt", 0)
        item = {
            "year": row["year"],
            "lpa": per_share(net_income, shares),
            "vpa": per_share(row.get("equity"), shares),
            "dpa": per_share(dividends, shares),
            "fcf_per_share": per_share(fcf, shares),
            "revenue_per_share": per_share(row.get("revenue"), shares),
            "p_l": safe_div(current_price, per_share(net_income, shares)) if current_price else None,
            "p_vp": safe_div(current_price, per_share(row.get("equity"), shares)) if current_price else None,
            "dividend_yield": safe_div(per_share(dividends, shares), current_price) if current_price else None,
            "p_fcf": safe_div(current_price, per_share(fcf, shares)) if current_price else None,
            "ev_ebitda": safe_div(enterprise_value, row.get("ebitda")),
            "roe": safe_div(net_income, row.get("equity")),
            "roic": safe_div(nopat, invested_capital),
            "net_margin": safe_div(net_income, row.get("revenue")),
            "ebitda_margin": safe_div(row.get("ebitda"), row.get("revenue")),
            "fcf_margin": safe_div(fcf, row.get("revenue")),
            "net_debt": row.get("net_debt"),
            "net_debt_ebitda": safe_div(row.get("net_debt"), row.get("ebitda")),
            "net_debt_equity": safe_div(row.get("net_debt"), row.get("equity")),
            "interest_coverage": safe_div(ebit, abs(row.get("financial_expense", 0))) if row.get("financial_expense") else None,
            "payout": safe_div(row.get("dividends_paid"), row.get("net_income")),
            "payout_adjusted": safe_div(dividends, net_income),
        }
        yearly.append(item)
    latest_indicators = yearly[-1] if yearly else {}
    dividend_yields = [row.get("dividend_yield") for row in yearly]
    dpas = [row.get("dpa") for row in yearly if row.get("dpa") is not None]
    dividend_events = data.get("dividend_events") or normalize_dividend_events(data.get("market_data", {}).get("dividend_history") or [])
    quality = assess_data_quality(data, yearly)
    output = {
        "ticker": data.get("ticker"),
        "yearly": yearly,
        "latest": latest_indicators,
        "dividends": {
            "yield_mean": average(dividend_yields),
            "yield_median": median(dividend_yields),
            "dpa_mean": average(dpas),
            "dpa_median": median(dpas),
            "dpa_growth": cagr(dpas[0], dpas[-1], len(dpas) - 1) if len(dpas) > 1 else 0.0,
            "years_paid": len([value for value in dpas if value and value > 0]),
            "stability": dividend_stability(dpas),
            "events": dividend_events,
        },
        "data_quality": quality,
    }
    output["dividends"]["policy"] = dividend_policy(output, current_price)
    return output


def dividend_stability(values: list[float]) -> str:
    if not values:
        return "none"
    positive = [value for value in values if value > 0]
    if len(positive) < len(values) * 0.6:
        return "low"
    mean = average(positive) or 0
    if mean <= 0:
        return "low"
    dispersion = statistics.pstdev(positive) / mean if len(positive) > 1 else 0
    if dispersion < 0.25:
        return "high"
    if dispersion < 0.55:
        return "medium"
    return "low"


def dividend_policy(indicators: dict[str, Any], current_price: float | None = None) -> dict[str, Any]:
    yearly = indicators.get("yearly", [])
    dpas = [row.get("dpa") for row in yearly if row.get("dpa") is not None]
    positive_dpas = [value for value in dpas if value and value > 0]
    latest_ind = indicators.get("latest", {})
    divs = indicators.get("dividends", {})
    stability = divs.get("stability", "none")
    coverage = safe_div(len(positive_dpas), len(dpas)) or 0.0
    average_dpa = average(positive_dpas) or 0.0
    median_dpa = median(positive_dpas) or 0.0
    latest_dpa = latest_ind.get("dpa") or 0.0
    candidates = [value for value in (median_dpa, average_dpa, latest_dpa) if value > 0]
    if not candidates:
        selected = 0.0
    elif stability == "high":
        selected = min(latest_dpa or max(candidates), average_dpa or max(candidates), median_dpa or max(candidates)) * 0.95
    elif stability == "medium":
        selected = min(median_dpa or max(candidates), average_dpa or max(candidates)) * 0.90
    else:
        selected = min(median_dpa or max(candidates), average_dpa or max(candidates)) * 0.70

    sustainable_caps = []
    if latest_ind.get("lpa") and latest_ind["lpa"] > 0:
        sustainable_caps.append(latest_ind["lpa"] * 0.75)
    if latest_ind.get("fcf_per_share") and latest_ind["fcf_per_share"] > 0:
        sustainable_caps.append(latest_ind["fcf_per_share"] * 0.75)
    if sustainable_caps:
        selected = min(selected, min(sustainable_caps))

    payout = latest_ind.get("payout_adjusted")
    suitable = stability in ("high", "medium") and coverage >= 0.6 and selected > 0 and (payout is None or payout <= 1.0)
    if stability == "low" or coverage < 0.6 or (payout and payout > 1.0):
        reliability = "low"
        method_action = "calculate_but_exclude_from_weighted_fair_value"
        suitable = False
    elif stability == "medium":
        reliability = "medium"
        method_action = "include_with_caution"
    else:
        reliability = "high"
        method_action = "include"

    return {
        "stability": stability,
        "coverage": coverage,
        "annual_dpa_mean": average_dpa,
        "annual_dpa_median": median_dpa,
        "latest_dpa": latest_dpa,
        "safe_dividend_per_share": selected,
        "safe_yield_on_current_price": safe_div(selected, current_price) or 0.0,
        "yield_mean_on_current_price": safe_div(average_dpa, current_price) or 0.0,
        "yield_median_on_current_price": safe_div(median_dpa, current_price) or 0.0,
        "suitable_for_bazin_ddm_weight": suitable,
        "income_method_reliability": reliability,
        "method_action": method_action,
    }


def assess_data_quality(data: dict[str, Any], yearly: list[dict[str, Any]]) -> dict[str, Any]:
    financials = data.get("financials", [])
    issues = []
    score = 85
    if len(financials) < 5:
        issues.append("historico_menor_que_5_anos")
        score -= 12
    years = [row.get("year") for row in financials]
    if years and len(years) != len(set(years)):
        issues.append("anos_duplicados")
        score -= 8
    if years and sorted(years) != list(range(min(years), max(years) + 1)):
        issues.append("anos_faltantes")
        score -= 8
    last = latest(financials) if financials else {}
    if last.get("equity", 0) <= 0:
        issues.append("patrimonio_nao_positivo")
        score -= 20
    if last.get("net_income_adjusted", last.get("net_income", 0)) <= 0:
        issues.append("lucro_nao_positivo")
        score -= 15
    if last.get("operating_cash_flow", 0) < last.get("net_income_adjusted", last.get("net_income", 0)):
        issues.append("caixa_operacional_abaixo_do_lucro")
        score -= 8
    latest_ind = yearly[-1] if yearly else {}
    if latest_ind.get("payout_adjusted") and latest_ind["payout_adjusted"] > 1:
        issues.append("payout_acima_de_100")
        score -= 10
    if latest_ind.get("net_debt_ebitda") and latest_ind["net_debt_ebitda"] > 3:
        issues.append("alavancagem_elevada")
        score -= 12
    if any(row.get("non_recurring_items") for row in financials):
        issues.append("itens_nao_recorrentes_detectados")
        score -= 6
    confidence = "high"
    if score < 80:
        confidence = "medium_high"
    if score < 68:
        confidence = "medium"
    if score < 55:
        confidence = "medium_low"
    if score < 40:
        confidence = "low"
    return {"score": int(clamp(score, 0, 100)), "issues": issues, "confidence": confidence, "years": len(financials)}


def sector_key(company: dict[str, Any]) -> str:
    text = " ".join(str(company.get(key, "")) for key in ("sector", "subsector", "segment")).lower()
    if any(word in text for word in ("banco", "finance", "intermediacao")):
        return "banks"
    if any(word in text for word in ("segur", "previd")):
        return "insurance"
    if any(word in text for word in ("energia", "eletric", "utilidade", "saneamento")):
        return "utilities"
    if any(word in text for word in ("petroleo", "miner", "sider", "commodity", "papel", "celulose")):
        return "commodities"
    if any(word in text for word in ("varejo", "comercio")):
        return "retail"
    if any(word in text for word in ("holding", "particip")):
        return "holding"
    return "general"


def dynamic_margin_of_safety(data: dict[str, Any], indicators: dict[str, Any]) -> float:
    return risk_adjustments(data, indicators)["final_margin"]


def risk_adjustments(data: dict[str, Any], indicators: dict[str, Any]) -> dict[str, Any]:
    requested = data.get("margin_of_safety", 0.20)
    sector = sector_key(data.get("company", {}))
    adjustments = []
    base = requested
    if sector in ("commodities", "retail"):
        sector_floor = 0.30
        if base < sector_floor:
            adjustments.append({"name": "piso_setorial_ciclico", "impact": sector_floor - base, "reason": "setor ciclico exige margem minima maior"})
            base = sector_floor
    if sector == "holding":
        sector_floor = 0.25
        if base < sector_floor:
            adjustments.append({"name": "piso_holding", "impact": sector_floor - base, "reason": "holding exige desconto por estrutura e NAV"})
            base = sector_floor
    if sector == "utilities":
        sector_floor = 0.15
        if base < sector_floor:
            adjustments.append({"name": "piso_utilities", "impact": sector_floor - base, "reason": "receita regulada permite margem minima menor"})
            base = sector_floor
    latest_ind = indicators.get("latest", {})
    if (latest_ind.get("net_debt_ebitda") or 0) > 3:
        adjustments.append({"name": "alavancagem_elevada", "impact": 0.07, "reason": "divida liquida/EBITDA acima de 3x"})
        base += 0.07
    if (latest_ind.get("payout_adjusted") or 0) > 1:
        adjustments.append({"name": "payout_acima_de_100", "impact": 0.05, "reason": "dividendos acima do lucro ajustado"})
        base += 0.05
    if "caixa_operacional_abaixo_do_lucro" in indicators.get("data_quality", {}).get("issues", []):
        adjustments.append({"name": "qualidade_do_lucro", "impact": 0.07, "reason": "caixa operacional abaixo do lucro"})
        base += 0.07
    final_margin = clamp(base, 0.10, 0.50)
    return {
        "base_margin": requested,
        "adjustments": adjustments,
        "final_margin": final_margin,
        "capped": final_margin != base,
    }


def normalize_cyclical_financials(financials: list[dict[str, Any]], sector: str) -> list[dict[str, Any]]:
    if sector != "commodities" or len(financials) < 5:
        return financials
    margins = [safe_div(row.get("net_income_adjusted", row.get("net_income")), row.get("revenue")) for row in financials]
    normal_margin = median(margins) or average(margins) or 0
    rows = []
    for row in financials:
        copy = dict(row)
        if row.get("revenue") and normal_margin:
            copy["net_income_adjusted"] = row["revenue"] * normal_margin
            copy["free_cash_flow_adjusted"] = min(row.get("free_cash_flow_adjusted", row.get("free_cash_flow", 0)), row["revenue"] * max(normal_margin, 0))
        rows.append(copy)
    return rows


def build_scenarios(data: dict[str, Any], indicators: dict[str, Any]) -> dict[str, dict[str, Any]]:
    financials = order_years(data["financials"])
    years = data.get("investment_horizon_years", 5)
    required_return = data.get("required_return", 0.12)
    sector = sector_key(data.get("company", {}))
    terminal_policy = terminal_growth_policy(data, sector)
    normalized_rows = normalize_cyclical_financials(financials, sector)
    revenue_growth = cagr(normalized_rows[0].get("revenue"), normalized_rows[-1].get("revenue"), len(normalized_rows) - 1)
    income_growth = cagr(
        normalized_rows[0].get("net_income_adjusted", normalized_rows[0].get("net_income")),
        normalized_rows[-1].get("net_income_adjusted", normalized_rows[-1].get("net_income")),
        len(normalized_rows) - 1,
    )
    margins = [safe_div(row.get("net_income_adjusted", row.get("net_income")), row.get("revenue")) for row in normalized_rows]
    payouts = [row.get("dividends_recurring", row.get("dividends_paid", 0)) / row.get("net_income_adjusted", row.get("net_income", 1)) for row in financials if row.get("net_income_adjusted", row.get("net_income", 0)) > 0]
    margin = average(margins) or 0.08
    payout = average(payouts) or 0.35
    operating = historical_operating_profile(normalized_rows)
    return {
        "conservative": {
            "revenue_growth": clamp(revenue_growth - 0.02, -0.03, 0.18),
            "net_income_growth": clamp(income_growth - 0.03, -0.05, 0.18),
            "margin": clamp(margin - 0.015, 0.01, 0.45),
            "ebitda_margin": clamp(operating["ebitda_margin"] - 0.015, 0.01, 0.70),
            "ebit_margin": clamp(operating["ebit_margin"] - 0.015, 0.0, 0.60),
            "payout": clamp(payout - 0.08, 0.0, 0.85),
            "discount_rate": required_return + 0.015,
            "terminal_growth": max(terminal_policy["terminal_growth_base"] - 0.01, 0.015),
            "years": years,
        },
        "base": {
            "revenue_growth": clamp(revenue_growth, -0.01, 0.22),
            "net_income_growth": clamp(income_growth, -0.02, 0.22),
            "margin": clamp(margin, 0.01, 0.50),
            "ebitda_margin": clamp(operating["ebitda_margin"], 0.01, 0.70),
            "ebit_margin": clamp(operating["ebit_margin"], 0.0, 0.60),
            "payout": clamp(payout, 0.0, 0.90),
            "discount_rate": required_return,
            "terminal_growth": terminal_policy["terminal_growth_base"],
            "years": years,
        },
        "optimistic": {
            "revenue_growth": clamp(revenue_growth + 0.02, 0.0, 0.28),
            "net_income_growth": clamp(income_growth + 0.02, 0.0, 0.28),
            "margin": clamp(margin + 0.015, 0.01, 0.55),
            "ebitda_margin": clamp(operating["ebitda_margin"] + 0.015, 0.01, 0.70),
            "ebit_margin": clamp(operating["ebit_margin"] + 0.015, 0.0, 0.60),
            "payout": clamp(payout + 0.04, 0.0, 0.95),
            "discount_rate": max(required_return - 0.01, 0.08),
            "terminal_growth": min(terminal_policy["terminal_growth_base"] + 0.01, 0.05),
            "years": years,
        },
    }


def historical_operating_profile(financials: list[dict[str, Any]]) -> dict[str, float]:
    ebitda_margins = [safe_div(row.get("ebitda"), row.get("revenue")) for row in financials]
    ebit_margins = [safe_div(row.get("ebit"), row.get("revenue")) for row in financials]
    net_margins = [safe_div(row.get("net_income_adjusted", row.get("net_income")), row.get("revenue")) for row in financials]
    net_margin = median(net_margins) or average(net_margins) or 0.08
    return {
        "ebitda_margin": median(ebitda_margins) or average(ebitda_margins) or min(net_margin + 0.08, 0.70),
        "ebit_margin": median(ebit_margins) or average(ebit_margins) or min(net_margin + 0.04, 0.60),
    }


def project_years(base_row: dict[str, Any], scenario: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    revenue = base_row.get("revenue", 0)
    equity = base_row.get("equity", 0)
    shares = base_row.get("shares_outstanding", 1)
    net_debt = base_row.get("net_debt", base_row.get("gross_debt", 0) - base_row.get("cash", 0))
    da_ratio = safe_div(base_row.get("depreciation_amortization", 0), base_row.get("revenue")) or 0
    capex_ratio = safe_div(base_row.get("capex", 0), base_row.get("revenue")) or 0
    wc_ratio = safe_div(base_row.get("working_capital_change", 0), base_row.get("revenue")) or 0
    tax_rate = base_row.get("tax_rate", 0.34)
    for offset in range(1, scenario["years"] + 1):
        revenue *= 1 + scenario["revenue_growth"]
        net_income = revenue * scenario["margin"]
        ebitda_margin = scenario.get("ebitda_margin")
        ebit_margin = scenario.get("ebit_margin")
        if ebitda_margin is None:
            ebitda_margin = safe_div(base_row.get("ebitda"), base_row.get("revenue")) or min(scenario["margin"] + 0.08, 0.70)
        if ebit_margin is None:
            ebit_margin = safe_div(base_row.get("ebit"), base_row.get("revenue")) or min(scenario["margin"] + 0.04, 0.60)
        ebitda = revenue * clamp(ebitda_margin, 0.01, 0.70)
        ebit = revenue * clamp(ebit_margin, 0.0, 0.60)
        dividends = net_income * scenario["payout"]
        da = revenue * da_ratio
        capex = revenue * capex_ratio
        wc_change = revenue * wc_ratio
        fcfe = net_income + da - capex - wc_change + base_row.get("net_debt_issuance", 0)
        fcff = ebit * (1 - tax_rate) + da - capex - wc_change
        equity = max(equity + net_income - dividends, 1)
        net_debt = max(net_debt * 0.99, 0)
        rows.append({
            "year_offset": offset,
            "revenue": revenue,
            "revenue_growth": scenario["revenue_growth"],
            "ebitda": ebitda,
            "ebitda_margin": safe_div(ebitda, revenue),
            "ebit": ebit,
            "ebit_margin": safe_div(ebit, revenue),
            "net_income": net_income,
            "net_margin": scenario["margin"],
            "lpa": per_share(net_income, shares),
            "dividends": dividends,
            "dividend_per_share": per_share(dividends, shares),
            "payout": scenario["payout"],
            "fcfe": fcfe,
            "fcff": fcff,
            "net_debt": net_debt,
            "net_debt_ebitda": safe_div(net_debt, ebitda),
            "roe": safe_div(net_income, equity),
            "roic": safe_div(ebit * (1 - tax_rate), equity + net_debt),
            "shares_outstanding": shares,
        })
    return rows


def discount_cash_flows(cash_flows: list[float], rate: float, terminal_growth: float) -> float | None:
    details = discount_cash_flow_details(cash_flows, rate, terminal_growth)
    return details.get("enterprise_value") if details else None


def discount_cash_flow_details(cash_flows: list[float], rate: float, terminal_growth: float) -> dict[str, Any] | None:
    if not cash_flows or rate <= terminal_growth:
        return None
    discounted_flows = [value / ((1 + rate) ** index) for index, value in enumerate(cash_flows, start=1)]
    pv = sum(discounted_flows)
    terminal = cash_flows[-1] * (1 + terminal_growth) / (rate - terminal_growth)
    discounted_terminal = terminal / ((1 + rate) ** len(cash_flows))
    value = pv + discounted_terminal
    return {
        "explicit_pv": pv,
        "terminal_value": terminal,
        "discounted_terminal_value": discounted_terminal,
        "enterprise_value": value,
        "terminal_value_share": safe_div(discounted_terminal, value) or 0.0,
        "discounted_flows": discounted_flows,
    }


def method_reliability(method: str, data: dict[str, Any], indicators: dict[str, Any]) -> str:
    sector = sector_key(data.get("company", {}))
    latest_ind = indicators.get("latest", {})
    if method in ("graham", "p_l") and ((latest_ind.get("lpa") or 0) <= 0 or (latest_ind.get("vpa") or 0) <= 0):
        return "not_applicable"
    if method == "ev_ebitda" and sector in ("banks", "insurance"):
        return "low"
    if method in ("residual_income", "p_vp") and sector == "banks":
        return "high"
    if method in ("p_vp", "ddm") and sector == "insurance":
        return "high"
    if method in ("sotp", "nav") and sector == "holding":
        if sum_sotp(data) or data.get("asset_values"):
            return "high"
        return "not_available"
    if method in ("bazin", "ddm"):
        return indicators.get("dividends", {}).get("policy", {}).get("income_method_reliability", "low")
    return "medium"


def sector_method_weights(sector: str) -> dict[str, float]:
    if sector == "banks":
        return {"residual_income": 0.35, "p_vp": 0.30, "ddm": 0.20, "graham": 0.15}
    if sector == "insurance":
        return {"p_vp": 0.30, "ddm": 0.25, "residual_income": 0.20, "graham": 0.15, "multiples": 0.10}
    if sector == "utilities":
        return {"ddm": 0.20, "bazin": 0.10, "dcf_fcfe": 0.25, "dcf_fcff": 0.25, "multiples": 0.10, "graham": 0.10}
    if sector == "commodities":
        return {"normalized_ev_ebitda": 0.35, "dcf_fcff": 0.30, "multiples": 0.20, "dcf_fcfe": 0.10, "graham": 0.05}
    if sector == "retail":
        return {"dcf_fcff": 0.35, "dcf_fcfe": 0.25, "multiples": 0.25, "graham": 0.15}
    if sector == "holding":
        return {"sotp": 0.45, "nav": 0.25, "ddm": 0.15, "graham": 0.15}
    return {"dcf_fcfe": 0.25, "dcf_fcff": 0.25, "graham": 0.15, "ddm": 0.15, "multiples": 0.20}


def weighted_fair_value(method_values: dict[str, float | None], weights: dict[str, float]) -> float:
    available = {key: value for key, value in method_values.items() if value is not None}
    total_weight = sum(weight for key, weight in weights.items() if key in available)
    if not available:
        return 0.0
    if total_weight <= 0:
        return average(list(available.values())) or 0.0
    return sum(available[key] * weights[key] for key in weights if key in available) / total_weight


def bazin_value_for_fair_value(bazin: dict[str, float]) -> float | None:
    return bazin.get("0.08") or bazin.get("0.1") or average(list(bazin.values()))


def income_method_weight_value(value: float | None, policy: dict[str, Any], sector: str) -> float | None:
    if value is None:
        return None
    if not policy.get("suitable_for_bazin_ddm_weight", False):
        return None
    if sector == "commodities" and policy.get("income_method_reliability") != "high":
        return None
    return value


def method_record(fair_value: float | None, applicable: bool, reliability: str, weight: float, reason: str, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "fair_value": fair_value,
        "applicable": applicable,
        "reliability": reliability,
        "weight": weight if applicable and fair_value is not None else 0.0,
        "reason": reason,
        "inputs": inputs or {},
    }


def multiple_implied_value(data: dict[str, Any], latest_ind: dict[str, Any]) -> float | None:
    peers = data.get("peers") or []
    if not peers:
        return None
    peer_pl = average([peer.get("p_l") for peer in peers])
    if peer_pl and latest_ind.get("lpa"):
        return peer_pl * latest_ind["lpa"]
    peer_pvp = average([peer.get("p_vp") for peer in peers])
    if peer_pvp and latest_ind.get("vpa"):
        return peer_pvp * latest_ind["vpa"]
    return None


def normalized_ev_ebitda_value(data: dict[str, Any], shares: float) -> float | None:
    if shares <= 0:
        return None
    financials = order_years(data.get("financials", []))
    if not financials:
        return None
    ebitdas = [row.get("ebitda") for row in financials if row.get("ebitda") and row.get("ebitda") > 0]
    normalized_ebitda = median(ebitdas) or average(ebitdas)
    if not normalized_ebitda:
        return None
    sector = sector_key(data.get("company", {}))
    default_multiple = 5.5 if sector == "commodities" else 6.5
    peer_multiple = average([peer.get("ev_ebitda") for peer in data.get("peers", [])])
    multiple = peer_multiple or data.get("normalized_ev_ebitda_multiple") or default_multiple
    net_debt = latest(financials).get("net_debt", latest(financials).get("gross_debt", 0) - latest(financials).get("cash", 0))
    equity_value = normalized_ebitda * multiple - net_debt
    return safe_div(equity_value, shares)


def discount_rate_policy(data: dict[str, Any], sector: str, indicators: dict[str, Any]) -> dict[str, Any]:
    macro = data.get("macro_data", {}) or {}
    selic = macro.get("selic")
    risk_free_spot = float(selic) / 100 if selic is not None else None
    normalized_risk_free = 0.10
    market_premium = 0.04
    sector_premiums = {
        "banks": 0.01,
        "insurance": 0.005,
        "utilities": 0.005,
        "commodities": 0.02,
        "retail": 0.02,
        "holding": 0.015,
        "general": 0.01,
    }
    sector_premium = sector_premiums.get(sector, 0.01)
    latest_ind = indicators.get("latest", {})
    specific_premium = 0.0
    if (latest_ind.get("net_debt_ebitda") or 0) > 3:
        specific_premium += 0.01
    if indicators.get("data_quality", {}).get("confidence") in ("low", "medium_low"):
        specific_premium += 0.01
    ke_normalized = clamp(normalized_risk_free + market_premium + sector_premium + specific_premium, 0.10, 0.24)
    ke_spot = clamp((risk_free_spot if risk_free_spot is not None else normalized_risk_free) + market_premium + sector_premium + specific_premium, 0.10, 0.24)
    ke_used = data.get("required_return")
    if ke_used is None:
        ke_used = ke_normalized
    return {
        "risk_free_rate_spot": risk_free_spot,
        "normalized_risk_free_rate": normalized_risk_free,
        "market_risk_premium": market_premium,
        "sector_risk_premium": sector_premium,
        "company_specific_premium": specific_premium,
        "ke_spot": ke_spot,
        "ke_normalized": ke_normalized,
        "ke_used": clamp(float(ke_used), 0.10, 0.24),
        "policy": "user_or_pipeline_required_return_with_normalized_and_spot_disclosure",
    }


def terminal_growth_policy(data: dict[str, Any], sector: str) -> dict[str, Any]:
    macro = data.get("macro_data", {}) or {}
    ipca_12m = macro.get("ipca_12m_estimated")
    normalized_inflation = 0.04
    real_growth = 0.005 if sector in ("commodities", "retail") else 0.01
    if sector in ("banks", "insurance"):
        real_growth = 0.005
    g_base = min(normalized_inflation + real_growth, 0.045)
    return {
        "ipca_monthly_latest": macro.get("ipca_monthly_latest", macro.get("ipca")),
        "ipca_12m_estimated": ipca_12m,
        "normalized_inflation": normalized_inflation,
        "real_growth": real_growth,
        "terminal_growth_base": g_base,
        "reason": "usa inflacao normalizada e crescimento real conservador; IPCA mensal nao e usado diretamente",
    }


def holding_methods_available(data: dict[str, Any]) -> bool:
    return bool(data.get("sotp_parts") or data.get("asset_values"))


def calculate_valuation(data: dict[str, Any]) -> dict[str, Any]:
    data = normalize_financials(data)
    indicators = calculate_indicators(data)
    financials = order_years(data["financials"])
    last = latest(financials)
    latest_ind = indicators["latest"]
    current_price = data.get("market_data", {}).get("current_price", 0)
    shares = last.get("shares_outstanding", 1)
    sector = sector_key(data.get("company", {}))
    discount_policy = discount_rate_policy(data, sector, indicators)
    data["required_return"] = discount_policy["ke_used"]
    required_return = discount_policy["ke_used"]
    scenarios = build_scenarios(data, indicators)
    risk_policy = risk_adjustments(data, indicators)
    dynamic_mos = risk_policy["final_margin"]
    requested_mos = data.get("margin_of_safety", 0.20)
    div_policy = indicators.get("dividends", {}).get("policy", {})
    safe_dividend = div_policy.get("safe_dividend_per_share", 0.0)
    graham = None
    if (latest_ind.get("lpa") or 0) > 0 and (latest_ind.get("vpa") or 0) > 0:
        graham = math.sqrt(22.5 * latest_ind["lpa"] * latest_ind["vpa"])
    desired_yields = data.get("desired_dividend_yields", [0.06, 0.08, 0.10, 0.12])
    bazin_ceiling = build_bazin_ceiling(div_policy, desired_yields, data.get("macro_data", {}))
    bazin = bazin_ceiling["conservative"]
    growth = scenarios["base"]["net_income_growth"]
    p_l = latest_ind.get("p_l")
    dividend_yield = safe_div(safe_dividend, current_price) if current_price else 0
    lynch = (((growth * 100) + ((dividend_yield or 0) * 100)) / p_l) if p_l and p_l > 0 else None
    ddm_expected_dividend = safe_dividend * (1 + growth)
    ddm = ddm_value(ddm_expected_dividend, required_return, scenarios["base"]["terminal_growth"])
    ddm_applicable = ddm is not None and div_policy.get("suitable_for_bazin_ddm_weight", False)
    scenario_results = {}
    fair_values = {}
    scenario_method_maps = {}
    for name, scenario in scenarios.items():
        projections = project_years(last, scenario)
        fcfe_details = discount_cash_flow_details([row["fcfe"] for row in projections], scenario["discount_rate"], scenario["terminal_growth"])
        fcff_details = discount_cash_flow_details([row["fcff"] for row in projections], scenario["discount_rate"], scenario["terminal_growth"])
        fcfe_value = fcfe_details["enterprise_value"] if fcfe_details else None
        fcff_value = fcff_details["enterprise_value"] if fcff_details else None
        fcfe_price = safe_div(fcfe_value, shares)
        fcff_price = safe_div((fcff_value or 0) - last.get("net_debt", 0), shares) if fcff_value is not None else None
        residual_price = residual_income_value(last, required_return, scenario["net_income_growth"], shares)
        method_map = {
            "graham": graham,
            "ddm": income_method_weight_value(ddm, div_policy, sector),
            "bazin": income_method_weight_value(bazin_value_for_fair_value(bazin), div_policy, sector),
            "dcf_fcfe": fcfe_price,
            "dcf_fcff": fcff_price,
            "residual_income": residual_price,
            "p_vp": latest_ind.get("vpa"),
            "multiples": multiple_implied_value(data, latest_ind),
            "normalized_ev_ebitda": normalized_ev_ebitda_value(data, shares) if sector == "commodities" else None,
            "sotp": safe_div(sum_sotp(data), shares) if sum_sotp(data) else None,
            "nav": net_asset_value(data, shares),
        }
        method_values = list(method_map.values())
        if sector == "banks":
            method_values = [graham, ddm, method_map["residual_income"], latest_ind.get("vpa")]
        if sector == "insurance":
            method_values = [graham, ddm, method_map["residual_income"], latest_ind.get("vpa"), method_map["multiples"]]
        if sector == "holding" and not holding_methods_available(data):
            method_values = [value for key, value in method_map.items() if key not in ("sotp", "nav")]
        fair = weighted_fair_value(method_map, sector_method_weights(sector)) or average(method_values) or 0.0
        fair_values[name] = fair
        scenario_method_maps[name] = method_map
        scenario_results[name] = {
            "assumptions": scenario,
            "projections": projections,
            "dcf_fcfe_price": fcfe_price,
            "dcf_fcff_price": fcff_price,
            "dcf_fcfe_details": fcfe_details,
            "dcf_fcff_details": fcff_details,
            "residual_income_price": residual_price,
            "fair_value": fair,
        }
    fair_base = fair_values["base"]
    projected_ceiling_prices = calculate_projected_ceiling_prices(
        scenario_results["conservative"]["fair_value"],
        scenarios["conservative"]["net_income_growth"],
        scenarios["conservative"]["discount_rate"],
        requested_mos,
        data.get("investment_horizon_years", 5),
    )
    ceiling_prices = build_ceiling_prices(
        data,
        sector,
        data.get("analysis_focus", "full"),
        fair_base,
        requested_mos,
        dynamic_mos,
        bazin_ceiling,
        projected_ceiling_prices,
        scenario_method_maps["base"],
    )
    recommended_ceiling = ceiling_prices["recommended"]["price"]
    base_ceiling = ceiling_prices["intrinsic_margin"]["ceiling_price"]
    risk_adjusted_ceiling = ceiling_prices["risk_adjusted"]["ceiling_price"]
    projected_ceiling = ceiling_prices["projected"]["year_5"]["ceiling_price"] if ceiling_prices["projected"]["year_5"] else None
    residual_income = last.get("net_income_adjusted", last.get("net_income", 0)) - required_return * last.get("equity", 0)
    residual_value = scenario_results["base"]["residual_income_price"]
    multiples = compare_peers(data, latest_ind)
    reverse_growth = reverse_dcf_growth(current_price, safe_dividend, required_return)
    quality_score = score_quality(indicators, sector)
    opportunity_score = score_opportunity(current_price, fair_base, quality_score, indicators)
    risk_level = risk_level_from(indicators, sector)
    verdict = classify_verdict(current_price, fair_base, opportunity_score, risk_level)
    output = {
        "ticker": data.get("ticker"),
        "skill_version": SKILL_VERSION,
        "company_name": data.get("company", {}).get("name", data.get("ticker")),
        "current_price": current_price,
        "fair_value_base": fair_base,
        "fair_value_conservative": fair_values["conservative"],
        "fair_value_optimistic": fair_values["optimistic"],
        "suggested_ceiling_price": recommended_ceiling,
        "base_ceiling_price": base_ceiling,
        "risk_adjusted_ceiling_price": risk_adjusted_ceiling,
        "projected_ceiling_price": projected_ceiling,
        "projected_ceiling_prices": projected_ceiling_prices,
        "ceiling_prices": ceiling_prices,
        "margin_of_safety": safe_div(fair_base - current_price, fair_base) or 0.0,
        "required_margin_of_safety": dynamic_mos,
        "base_margin_of_safety": requested_mos,
        "dividend_safe_yield": safe_div(safe_dividend, current_price) or 0.0,
        "projected_yield_on_cost_year_5": safe_div(scenario_results["base"]["projections"][-1]["dividend_per_share"], current_price) or 0.0,
        "quality_score": quality_score,
        "opportunity_score": opportunity_score,
        "risk_level": risk_level,
        "verdict": verdict,
        "confidence": indicators["data_quality"]["confidence"],
        "calculation_metadata": {
            "skill_version": SKILL_VERSION,
            "engine_version": CALCULATION_ENGINE_VERSION,
            "sector_key": sector,
            "sector_weights": sector_method_weights(sector),
            "required_return": required_return,
            "discount_rate_policy": discount_policy,
            "terminal_growth_policy": terminal_growth_policy(data, sector),
            "risk_adjustments": risk_policy,
            "base_margin_of_safety": requested_mos,
            "risk_adjusted_margin_of_safety": dynamic_mos,
        },
        "company": data.get("company", {}),
        "sources": data.get("sources", []),
        "ttm": data.get("ttm"),
        "dividend_events": indicators.get("dividends", {}).get("events", []),
        "data_quality": indicators["data_quality"],
        "financial_diagnosis": indicators,
        "diagnosis": {
            "multiples": latest_ind,
            "safe_dividend_per_share": safe_dividend,
            "dividend_policy": div_policy,
            "residual_income": residual_income,
            "sector": sector,
        },
        "valuation": {
            "graham": method_record(graham, graham is not None, method_reliability("graham", data, indicators), sector_method_weights(sector).get("graham", 0), "Graham aplicavel apenas com LPA e VPA positivos", {"lpa": latest_ind.get("lpa"), "vpa": latest_ind.get("vpa")}),
            "bazin": {**method_record(bazin_value_for_fair_value(bazin), income_method_weight_value(bazin_value_for_fair_value(bazin), div_policy, sector) is not None, method_reliability("bazin", data, indicators), sector_method_weights(sector).get("bazin", 0), "Bazin entra no peso apenas se dividendos forem adequados ao setor", {"selected_yield": bazin_ceiling.get("selected_yield")}), "safe_dividend_per_share": safe_dividend, "ceiling_prices": bazin, "classic_ceiling_prices": bazin_ceiling["classic"], "policy": div_policy},
            "peter_lynch": {"score": lynch, "applicable": p_l is not None and p_l > 0, "reliability": method_reliability("lynch", data, indicators), "weight": 0.0, "reason": "Peter Lynch e score relativo; influencia oportunidade, nao preco justo"},
            "ddm": {**method_record(ddm, ddm_applicable, method_reliability("ddm", data, indicators), sector_method_weights(sector).get("ddm", 0), "DDM exige Ke > g e dividendos previsiveis", {"d1": ddm_expected_dividend, "ke": required_return, "g": scenarios["base"]["terminal_growth"], "ke_minus_g": required_return - scenarios["base"]["terminal_growth"]}), "required_return": required_return, "growth": growth, "policy": div_policy},
            "dcf_fcfe": {**method_record(scenario_results["base"]["dcf_fcfe_price"], scenario_results["base"]["dcf_fcfe_price"] is not None, method_reliability("fcfe", data, indicators), sector_method_weights(sector).get("dcf_fcfe", 0), "DCF FCFE baseado em fluxos projetados ao acionista", {"discount_rate": scenarios["base"]["discount_rate"], "terminal_growth": scenarios["base"]["terminal_growth"], "terminal_value_share": (scenario_results["base"]["dcf_fcfe_details"] or {}).get("terminal_value_share")}), "details": scenario_results["base"]["dcf_fcfe_details"]},
            "dcf_fcff": {**method_record(scenario_results["base"]["dcf_fcff_price"], scenario_results["base"]["dcf_fcff_price"] is not None, method_reliability("fcff", data, indicators), sector_method_weights(sector).get("dcf_fcff", 0), "DCF FCFF baseado em fluxo da firma menos divida liquida", {"discount_rate": scenarios["base"]["discount_rate"], "terminal_growth": scenarios["base"]["terminal_growth"], "terminal_value_share": (scenario_results["base"]["dcf_fcff_details"] or {}).get("terminal_value_share")}), "details": scenario_results["base"]["dcf_fcff_details"]},
            "multiples": multiples,
            "normalized_ev_ebitda": method_record(normalized_ev_ebitda_value(data, shares), normalized_ev_ebitda_value(data, shares) is not None and sector == "commodities", "high" if sector == "commodities" else "conditional", sector_method_weights(sector).get("normalized_ev_ebitda", 0), "EV/EBITDA normalizado e metodo principal para commodities", {}),
            "reverse_dcf": {"implied_growth": reverse_growth},
            "residual_income": {**method_record(residual_value, residual_value is not None, method_reliability("residual_income", data, indicators), sector_method_weights(sector).get("residual_income", 0), "Lucro residual e central para bancos/seguradoras", {"residual_income": residual_income}), "value": residual_income},
            "sotp": method_record(sum_sotp(data), sum_sotp(data) is not None, method_reliability("sotp", data, indicators), sector_method_weights(sector).get("sotp", 0), "SOTP e principal para holdings quando partes sao informadas"),
            "nav": method_record(net_asset_value(data, shares), net_asset_value(data, shares) is not None, method_reliability("nav", data, indicators), sector_method_weights(sector).get("nav", 0), "NAV e principal para holdings quando ativos sao informados"),
            "sector_weights": sector_method_weights(sector),
        },
        "scenarios": scenario_results,
        "sensitivity": {},
        "risks": build_risks(data, indicators),
        "scores": {
            "business_quality": quality_score,
            "opportunity": opportunity_score,
            "dividends": score_dividends(indicators),
            "debt": score_debt(indicators),
        },
        "limitations": build_limitations(data, indicators),
    }
    return output


def residual_income_value(last: dict[str, Any], required_return: float, growth: float, shares: float) -> float | None:
    equity = last.get("equity", 0)
    net_income = last.get("net_income_adjusted", last.get("net_income", 0))
    residual = net_income - required_return * equity
    if shares <= 0 or required_return <= growth:
        return None
    return (equity + residual * (1 + growth) / (required_return - growth)) / shares


def sum_sotp(data: dict[str, Any]) -> float | None:
    parts = data.get("sotp_parts") or []
    if not parts:
        return None
    return sum(float(part.get("value", 0)) for part in parts)


def net_asset_value(data: dict[str, Any], shares: float) -> float | None:
    assets = data.get("asset_values")
    if not assets or shares <= 0:
        return None
    gross = sum(float(item.get("value", 0)) for item in assets)
    debt = latest(data.get("financials", [{}])).get("net_debt", 0)
    return (gross - debt) / shares


def compare_peers(data: dict[str, Any], latest_ind: dict[str, Any]) -> dict[str, Any]:
    peers = data.get("peers") or []
    mapped_group = data.get("peer_group") or []
    if not peers:
        group = mapped_group or peer_groups().get(str(data.get("ticker", "")).upper(), [])
        if group:
            return {"available": False, "message": "pares mapeados, mas multiplos ainda nao coletados", "peers": group}
        return {"available": False, "message": "pares nao informados"}
    keys = ["p_l", "p_vp", "ev_ebitda", "dividend_yield", "roe", "roic", "ebitda_margin", "net_debt_ebitda"]
    result = {"available": True, "company": {}, "peer_average": {}, "relative_discount": {}}
    for key in keys:
        company_value = latest_ind.get(key)
        peer_avg = average([peer.get(key) for peer in peers])
        result["company"][key] = company_value
        result["peer_average"][key] = peer_avg
        result["relative_discount"][key] = safe_div((peer_avg or 0) - company_value, peer_avg) if company_value is not None and peer_avg else None
    return result


def calculate_projected_ceiling_prices(fair_value: float, growth: float, discount_rate: float, margin_of_safety: float, years: int) -> list[dict[str, Any]]:
    rows = []
    for year in range(1, int(years) + 1):
        future_fair_value = fair_value * ((1 + growth) ** year)
        present_value = future_fair_value / ((1 + discount_rate) ** year) if discount_rate > -1 else None
        ceiling_price = present_value * (1 - margin_of_safety) if present_value is not None else None
        rows.append({
            "year": year,
            "future_fair_value": future_fair_value,
            "present_value": present_value,
            "margin_of_safety": margin_of_safety,
            "ceiling_price": ceiling_price,
        })
    return rows


def select_bazin_yield(macro_data: dict[str, Any], desired_yields: list[float]) -> tuple[float, str]:
    available = sorted(float(value) for value in desired_yields if value)
    if not available:
        return 0.08, "yield padrao por ausencia de lista"
    selic = macro_data.get("selic")
    if selic is None:
        preferred = 0.08
        reason = "Selic indisponivel; usa referencia moderada de 8%"
    else:
        selic_decimal = float(selic) / 100
        if selic_decimal <= 0.08:
            preferred = 0.08 if 0.08 in available else 0.06
            reason = "Selic <= 8%; yield historico/moderado"
        elif selic_decimal <= 0.12:
            preferred = 0.10 if 0.10 in available else 0.08
            reason = "Selic entre 8% e 12%; yield moderado/conservador"
        else:
            preferred = 0.12 if 0.12 in available else 0.10
            reason = "Selic > 12%; yield conservador"
    selected = min(available, key=lambda value: abs(value - preferred))
    return selected, reason


def build_bazin_ceiling(policy: dict[str, Any], desired_yields: list[float], macro_data: dict[str, Any]) -> dict[str, Any]:
    classic_dpa = policy.get("annual_dpa_median") or policy.get("annual_dpa_mean") or 0.0
    conservative_dpa = policy.get("safe_dividend_per_share") or 0.0
    classic = {str(yield_rate): classic_dpa / yield_rate for yield_rate in desired_yields if yield_rate > 0}
    conservative = {str(yield_rate): conservative_dpa / yield_rate for yield_rate in desired_yields if yield_rate > 0}
    selected_yield, reason = select_bazin_yield(macro_data, desired_yields)
    selected_key = str(selected_yield)
    classic_price = classic.get(selected_key)
    conservative_price = conservative.get(selected_key)
    haircut = safe_div(classic_dpa - conservative_dpa, classic_dpa) if classic_dpa else None
    return {
        "classic": classic,
        "conservative": conservative,
        "classic_dpa": classic_dpa,
        "conservative_dpa": conservative_dpa,
        "selected_yield": selected_yield,
        "selected_price": conservative_price,
        "selected_classic_price": classic_price,
        "haircut": haircut,
        "selection_reason": reason,
        "conservatism_reason": policy.get("method_action"),
    }


def build_ceiling_prices(
    data: dict[str, Any],
    sector: str,
    focus: str,
    fair_value: float,
    base_margin: float,
    risk_margin: float,
    bazin_ceiling: dict[str, Any],
    projected_rows: list[dict[str, Any]],
    method_map: dict[str, float | None],
) -> dict[str, Any]:
    intrinsic = {
        "fair_value_base": fair_value,
        "required_margin": base_margin,
        "ceiling_price": fair_value * (1 - base_margin),
    }
    risk_adjusted = {
        "fair_value_base": fair_value,
        "required_margin": risk_margin,
        "ceiling_price": fair_value * (1 - risk_margin),
    }
    projected = {
        "years": projected_rows,
        "year_5": projected_rows[-1] if projected_rows else None,
    }
    candidates = []
    def add_candidate(method: str, price: float | None, reason: str):
        if price is not None:
            candidates.append({"method": method, "price": price, "reason": reason})

    projected_price = projected["year_5"]["ceiling_price"] if projected["year_5"] else None
    if focus == "dividends":
        add_candidate("bazin_conservative", bazin_ceiling.get("selected_price"), "foco em dividendos usa Bazin conservador no yield selecionado")
        add_candidate("intrinsic_margin", intrinsic["ceiling_price"], "teto por valor justo com margem de seguranca")
        add_candidate("projected", projected_price, "teto projetivo descontado")
    elif sector == "banks":
        add_candidate("residual_income", method_map.get("residual_income"), "banco prioriza lucro residual")
        add_candidate("p_vp", method_map.get("p_vp"), "banco prioriza P/VP ajustado por ROE")
        add_candidate("intrinsic_margin", intrinsic["ceiling_price"], "teto por valor justo com margem")
    elif sector == "commodities":
        add_candidate("normalized_ev_ebitda", method_map.get("normalized_ev_ebitda"), "commodity prioriza EV/EBITDA normalizado")
        add_candidate("dcf_fcff", method_map.get("dcf_fcff"), "commodity prioriza DCF conservador de ciclo")
        add_candidate("risk_adjusted", risk_adjusted["ceiling_price"], "setor ciclico usa margem ajustada ao risco")
    elif sector == "holding":
        add_candidate("sotp", method_map.get("sotp"), "holding prioriza soma das partes")
        add_candidate("nav", method_map.get("nav"), "holding prioriza NAV")
        add_candidate("intrinsic_margin", intrinsic["ceiling_price"], "fallback por margem de seguranca")
    else:
        add_candidate("intrinsic_margin", intrinsic["ceiling_price"], "teto por valor justo com margem")
        add_candidate("projected", projected_price, "teto projetivo descontado")

    recommended = min(candidates, key=lambda item: item["price"]) if candidates else {
        "method": "not_available",
        "price": None,
        "reason": "nenhum teto aplicavel calculado",
    }
    return {
        "bazin": bazin_ceiling,
        "intrinsic_margin": intrinsic,
        "risk_adjusted": risk_adjusted,
        "projected": projected,
        "recommended": recommended,
        "candidates": candidates,
    }


def calculate_ttm(financials: list[dict[str, Any]], itr_rows: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    if not financials:
        return None
    latest_annual = latest(financials)
    if not itr_rows:
        ttm = dict(latest_annual)
        ttm["period"] = "TTM_fallback_annual"
        return ttm
    latest_itr = latest(itr_rows)
    ttm = dict(latest_itr)
    ttm["period"] = "TTM"
    for key in ("revenue", "ebitda", "ebit", "net_income", "operating_cash_flow", "capex", "free_cash_flow", "dividends_paid"):
        ttm[key] = latest_itr.get(key, 0) + max(latest_annual.get(key, 0) * 0.25, 0)
    return ttm


def reverse_dcf_growth(price: float, dividend: float, required_return: float) -> float | None:
    if not price or price <= 0:
        return None
    return clamp(required_return - safe_div(dividend, price), -0.10, required_return - 0.005)


def ddm_value(dividend_expected: float, required_return: float, growth: float) -> float | None:
    if required_return <= growth:
        return None
    return dividend_expected / (required_return - growth)


def score_quality(indicators: dict[str, Any], sector: str) -> int:
    latest_ind = indicators.get("latest", {})
    score = indicators.get("data_quality", {}).get("score", 70)
    if (latest_ind.get("roe") or 0) > 0.15:
        score += 5
    if (latest_ind.get("roic") or 0) > 0.12 and sector not in ("banks", "insurance"):
        score += 5
    if (latest_ind.get("net_debt_ebitda") or 0) > 3:
        score -= 10
    return int(clamp(score, 0, 100))


def score_dividends(indicators: dict[str, Any]) -> int:
    divs = indicators.get("dividends", {})
    score = 40
    if divs.get("stability") == "high":
        score += 25
    elif divs.get("stability") == "medium":
        score += 15
    if (divs.get("yield_median") or 0) > 0.06:
        score += 20
    if (divs.get("dpa_growth") or 0) > 0:
        score += 10
    return int(clamp(score, 0, 100))


def score_debt(indicators: dict[str, Any]) -> int:
    leverage = indicators.get("latest", {}).get("net_debt_ebitda")
    if leverage is None:
        return 60
    if leverage < 1:
        return 90
    if leverage < 2:
        return 75
    if leverage < 3:
        return 55
    return 30


def score_opportunity(price: float, fair_value: float, quality_score: int, indicators: dict[str, Any]) -> int:
    if not fair_value:
        return 0
    discount = safe_div(fair_value - price, fair_value) or 0
    score = 50 + discount * 80 + (quality_score - 70) * 0.35
    if indicators.get("data_quality", {}).get("confidence") in ("low", "medium_low"):
        score -= 10
    return int(clamp(score, 0, 100))


def risk_level_from(indicators: dict[str, Any], sector: str) -> str:
    issues = indicators.get("data_quality", {}).get("issues", [])
    leverage = indicators.get("latest", {}).get("net_debt_ebitda") or 0
    if leverage > 3 or "patrimonio_nao_positivo" in issues:
        return "high"
    if leverage > 2 or sector in ("commodities", "retail") or len(issues) >= 2:
        return "medium"
    return "low"


def classify_verdict(price: float, fair_value: float, opportunity_score: int, risk_level: str) -> str:
    if risk_level == "high" and opportunity_score < 55:
        return "Evitar"
    if not fair_value or fair_value <= price * 0.95:
        return "Cara"
    if fair_value >= price * 1.35 and opportunity_score >= 70:
        return "Atrativa com margem de seguranca"
    if fair_value >= price * 1.15:
        return "Interessante"
    return "Justa"


def build_risks(data: dict[str, Any], indicators: dict[str, Any]) -> list[dict[str, Any]]:
    sector = sector_key(data.get("company", {}))
    risks = []
    if sector == "utilities":
        risks.append(risk("Regulatorio/concessoes", "medium", "high", "reduz crescimento terminal ou aumenta Ke"))
    if sector == "commodities":
        risks.append(risk("Ciclo de commodity", "high", "high", "exige normalizacao de lucro e margem maior"))
    if sector == "retail":
        risks.append(risk("Juros e capital de giro", "medium", "high", "pressiona margem, caixa e custo de capital"))
    if sector in ("banks", "insurance"):
        risks.append(risk("Credito e capital regulatorio", "medium", "high", "afeta payout, ROE e P/VP justo"))
    leverage = indicators.get("latest", {}).get("net_debt_ebitda") or 0
    risks.append(risk("Alavancagem", "low" if leverage < 1.5 else "medium", "low" if leverage < 1.5 else "medium", "altera margem de seguranca e custo de capital"))
    if "caixa_operacional_abaixo_do_lucro" in indicators.get("data_quality", {}).get("issues", []):
        risks.append(risk("Qualidade do lucro", "medium", "high", "reduz confianca dos fluxos projetados"))
    return risks


def risk(name: str, probability: str, impact: str, effect: str) -> dict[str, str]:
    severity_order = {"low": 1, "medium": 2, "high": 3}
    severity = "high" if severity_order[impact] + severity_order[probability] >= 5 else "medium" if severity_order[impact] + severity_order[probability] >= 3 else "low"
    return {"name": name, "probability": probability, "impact": impact, "severity": severity, "effect_on_valuation": effect}


def build_limitations(data: dict[str, Any], indicators: dict[str, Any]) -> list[str]:
    limitations = list(data.get("limitations", []))
    if not data.get("peers") and not data.get("peer_group"):
        limitations.append("Comparacao com pares depende de dados de pares no input ou coleta setorial.")
    if sector_key(data.get("company", {})) == "holding" and not holding_methods_available(data):
        limitations.append("Holding sem SOTP/NAV estruturado; valuation por metodos genericos tem baixa confiabilidade.")
    if any(row.get("ebitda_estimated") for row in data.get("financials", [])):
        limitations.append("EBITDA estimado em pelo menos um periodo por ausencia de D&A estruturado na DFC.")
    if not any(source.get("type") == SOURCE_OFFICIAL for source in data.get("sources", [])):
        limitations.append("Dados ainda nao confirmados em fonte oficial dentro deste payload.")
    if indicators.get("data_quality", {}).get("issues"):
        limitations.append("Existem alertas de qualidade que reduzem a confianca do valuation.")
    return list(dict.fromkeys(limitations))


def calculate_sensitivity(valuation: dict[str, Any]) -> dict[str, Any]:
    ddm = valuation["valuation"]["ddm"]
    base_rate = ddm["required_return"]
    base_growth = ddm["growth"]
    dividend = valuation["diagnosis"]["safe_dividend_per_share"]
    rates = [base_rate - 0.01, base_rate, base_rate + 0.01]
    growths = [max(base_growth - 0.01, 0.0), base_growth, base_growth + 0.01]
    matrix = []
    for rate in rates:
        row = []
        for growth in growths:
            row.append(dividend * (1 + growth) / (rate - growth) if rate > growth else None)
        matrix.append(row)
    base_fair = valuation.get("fair_value_base")
    margin_values = [0.20, valuation.get("required_margin_of_safety", 0.25), 0.35]
    return {
        "base_rate": base_rate,
        "base_growth": base_growth,
        "rates": rates,
        "growths": growths,
        "ddm_matrix": matrix,
        "bazin_ceiling_prices": valuation["valuation"]["bazin"]["ceiling_prices"],
        "ceiling_by_margin": {str(margin): base_fair * (1 - margin) for margin in margin_values if base_fair is not None},
        "payout_sensitivity": sensitivity_projection(valuation, "payout"),
        "growth_sensitivity": sensitivity_projection(valuation, "growth"),
        "margin_sensitivity": sensitivity_projection(valuation, "margin"),
    }


def sensitivity_projection(valuation: dict[str, Any], variable: str) -> dict[str, float | None]:
    base = valuation.get("fair_value_base")
    if base is None:
        return {"down": None, "base": None, "up": None}
    factor = {"payout": 0.06, "growth": 0.10, "margin": 0.08}[variable]
    return {"down": base * (1 - factor), "base": base, "up": base * (1 + factor)}


def brl(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def fetch_url(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "valuation-br-stock/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def read_csv_from_zip(zip_path: Path, member_pattern: str | None = None, delimiter: str = ";", encoding: str = "latin1") -> list[dict[str, str]]:
    rows = []
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        selected = next((name for name in names if member_pattern is None or re.search(member_pattern, name)), None)
        if not selected:
            return []
        content = archive.read(selected).decode(encoding, errors="replace").splitlines()
        reader = csv.DictReader(content, delimiter=delimiter)
        rows.extend(dict(row) for row in reader)
    return rows


def csv_rows_from_zip_members(zip_path: Path, member_patterns: list[str]) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            for pattern in member_patterns:
                if re.search(pattern, member, flags=re.IGNORECASE):
                    content = archive.read(member).decode("latin1", errors="replace").splitlines()
                    output[member] = [dict(row) for row in csv.DictReader(content, delimiter=";")]
                    break
    return output


def parse_cvm_number(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def cvm_row_year(row: dict[str, str]) -> int | None:
    date_value = row.get("DT_FIM_EXERC") or row.get("DT_REFER")
    if not date_value:
        return None
    match = re.match(r"(\d{4})", date_value)
    return int(match.group(1)) if match else None


def cvm_scale(row: dict[str, str]) -> float:
    scale = (row.get("ESCALA_MOEDA") or "").upper()
    if "MIL" in scale:
        return 1000.0
    return 1.0


def cvm_find_account(rows: list[dict[str, str]], codes: list[str]) -> float | None:
    preferred = [
        row for row in rows
        if (row.get("ORDEM_EXERC") or "").upper() in ("ULTIMO", "PENULTIMO")
    ] or rows
    for code in codes:
        exact = [row for row in preferred if row.get("CD_CONTA") == code]
        if exact:
            row = exact[-1]
            return parse_cvm_number(row.get("VL_CONTA")) * cvm_scale(row)
    for code in codes:
        prefix = [row for row in preferred if (row.get("CD_CONTA") or "").startswith(code)]
        if prefix:
            row = prefix[-1]
            return parse_cvm_number(row.get("VL_CONTA")) * cvm_scale(row)
    return None


def parse_cvm_dfp_zip(zip_path: str | Path, cvm_code: str | int | None = None) -> list[dict[str, Any]]:
    """Parse one CVM DFP zip into annual financial rows.

    Uses consolidated statements when present. Values are best-effort because CVM
    account layouts vary by sector, especially banks and insurers.
    """
    members = csv_rows_from_zip_members(
        Path(zip_path),
        [
            r"DRE_con",
            r"BPA_con",
            r"BPP_con",
            r"DFC_MI_con",
            r"DFC_MD_con",
            r"composicao_capital",
        ],
    )
    grouped: dict[int, dict[str, list[dict[str, str]]]] = {}
    wanted_code = str(cvm_code).strip() if cvm_code not in (None, "") else None
    for member, rows in members.items():
        statement = "unknown"
        name = member.lower()
        if "dre_con" in name:
            statement = "dre"
        elif "bpa_con" in name:
            statement = "bpa"
        elif "bpp_con" in name:
            statement = "bpp"
        elif "dfc" in name:
            statement = "dfc"
        elif "composicao_capital" in name:
            statement = "capital"
        for row in rows:
            row_code_raw = str(row.get("CD_CVM", "")).strip()
            row_code = row_code_raw.lstrip("0")
            if wanted_code and row_code_raw and row_code != wanted_code.lstrip("0"):
                continue
            year = cvm_row_year(row)
            if year is None:
                continue
            grouped.setdefault(year, {}).setdefault(statement, []).append(row)
    financials = []
    for year, statements in sorted(grouped.items()):
        dre = statements.get("dre", [])
        bpa = statements.get("bpa", [])
        bpp = statements.get("bpp", [])
        dfc = statements.get("dfc", [])
        capital = statements.get("capital", [])
        identity_row = (dre or bpa or bpp or dfc or [{}])[-1]
        cnpj = identity_row.get("CNPJ_CIA")
        denom = identity_row.get("DENOM_CIA")
        revenue = cvm_find_account(dre, CVM_ACCOUNT_MAP["revenue"]) or 0.0
        net_income = cvm_find_account(dre, CVM_ACCOUNT_MAP["net_income"]) or 0.0
        ebit = cvm_find_account(dre, CVM_ACCOUNT_MAP["ebit"]) or net_income
        cash = cvm_find_account(bpa, CVM_ACCOUNT_MAP["cash"]) or 0.0
        equity = cvm_find_account(bpp, CVM_ACCOUNT_MAP["equity"]) or 0.0
        debt_short = cvm_find_account(bpp, CVM_ACCOUNT_MAP["gross_debt_short"]) or 0.0
        debt_long = cvm_find_account(bpp, CVM_ACCOUNT_MAP["gross_debt_long"]) or 0.0
        ocf = cvm_find_account(dfc, CVM_ACCOUNT_MAP["operating_cash_flow"]) or 0.0
        da = abs(cvm_find_account(dfc, CVM_ACCOUNT_MAP["depreciation_amortization"]) or 0.0)
        capex_raw = cvm_find_account(dfc, CVM_ACCOUNT_MAP["capex"]) or 0.0
        capex = abs(capex_raw)
        gross_debt = max(debt_short + debt_long, 0.0)
        ebitda_estimated = da <= 0
        ebitda = ebit + da if da > 0 else max(ebit, net_income, 0.0)
        free_cash_flow = ocf - capex
        shares = cvm_find_share_count(capital, cnpj, denom, revenue)
        row = {
            "year": year,
            "basis": "consolidado",
            "revenue": revenue,
            "ebitda": ebitda,
            "ebit": ebit,
            "net_income": net_income,
            "equity": equity,
            "operating_cash_flow": ocf,
            "capex": capex,
            "free_cash_flow": free_cash_flow,
            "dividends_paid": 0.0,
            "shares_outstanding": shares or 1.0,
            "gross_debt": gross_debt,
            "cash": cash,
            "depreciation_amortization": da,
            "ebitda_estimated": ebitda_estimated,
            "working_capital_change": 0.0,
            "net_debt_issuance": 0.0,
            "tax_rate": 0.34,
            "source_status": SOURCE_OFFICIAL,
        }
        if any(value not in (None, 0, 0.0) for value in (revenue, net_income, equity, ocf)):
            financials.append(row)
    return financials


def cvm_find_share_count(rows: list[dict[str, str]], cnpj: str | None, denom: str | None, revenue: float) -> float | None:
    if not rows:
        return None
    candidates = []
    if cnpj:
        candidates = [row for row in rows if row.get("CNPJ_CIA") == cnpj]
    if not candidates and denom:
        denom_norm = normalize_text(denom)
        candidates = [row for row in rows if normalize_text(row.get("DENOM_CIA", "")) == denom_norm]
    if not candidates:
        return None
    row = candidates[-1]
    total = parse_cvm_number(row.get("QT_ACAO_TOTAL_CAP_INTEGR")) - parse_cvm_number(row.get("QT_ACAO_TOTAL_TESOURO"))
    if total <= 0:
        return None
    if total < 100_000_000 and revenue > total * 10_000:
        total *= 1000
    return total


def normalize_text(value: str) -> str:
    text = value.upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def merge_financial_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_year: dict[int, dict[str, Any]] = {}
    for row in rows:
        year = int(row["year"])
        current = by_year.setdefault(year, dict(row))
        for key, value in row.items():
            if key == "year":
                continue
            if current.get(key) in (None, 0, 0.0, "") and value not in (None, "", 0, 0.0):
                current[key] = value
    return [by_year[year] for year in sorted(by_year)]


def enrich_financials_with_market_data(financials: list[dict[str, Any]], market_data: dict[str, Any], company: dict[str, Any]) -> list[dict[str, Any]]:
    shares = company.get("shares_outstanding")
    if not shares or shares <= 1:
        shares = infer_shares_from_market(market_data, financials)
    dividend_events = normalize_dividend_events(market_data.get("dividend_events") or [])
    dividends_by_year = aggregate_recurring_dividends_by_year(dividend_events)
    dividend_history = market_data.get("dividend_history") or []
    fallback_annual_dpa = recent_average_annual_dividend(dividends_by_year)
    for index, row in enumerate(financials):
        row["shares_outstanding"] = shares or row.get("shares_outstanding") or 1.0
        if dividends_by_year.get(row.get("year")) is not None:
            dpa = dividends_by_year[row["year"]]
            row["dividends_paid"] = max(float(dpa), 0.0) * row["shares_outstanding"]
            row["dividends_source_status"] = SOURCE_AUXILIARY
        elif fallback_annual_dpa is not None:
            dpa = fallback_annual_dpa
            row["dividends_paid"] = max(float(dpa), 0.0) * row["shares_outstanding"]
            row["dividends_source_status"] = SOURCE_ESTIMATED
        elif dividend_history:
            dpa = sum(float(value) for value in dividend_history[-4:])
            row["dividends_paid"] = max(dpa, 0.0) * row["shares_outstanding"]
            row["dividends_source_status"] = SOURCE_ESTIMATED
        elif not row.get("dividends_paid"):
            row["dividends_paid"] = max(row.get("net_income", 0) * 0.25, 0.0)
            row["dividends_source_status"] = SOURCE_ESTIMATED
    return financials


def aggregate_recurring_dividends_by_year(events: list[dict[str, Any]]) -> dict[int, float]:
    by_year: dict[int, float] = {}
    for event in events:
        if not event.get("is_recurring"):
            continue
        year = event.get("year")
        if year is None and event.get("date"):
            match = re.match(r"(\d{4})", str(event["date"]))
            year = int(match.group(1)) if match else None
        if year is None:
            continue
        by_year[int(year)] = by_year.get(int(year), 0.0) + float(event.get("amount_per_share") or 0.0)
    return by_year


def recent_average_annual_dividend(dividends_by_year: dict[int, float], lookback: int = 5) -> float | None:
    if not dividends_by_year:
        return None
    values = [value for _, value in sorted(dividends_by_year.items())[-lookback:] if value > 0]
    return average(values)


def infer_shares_from_market(market_data: dict[str, Any], financials: list[dict[str, Any]]) -> float | None:
    market_cap = market_data.get("market_cap")
    current_price = market_data.get("current_price")
    if market_cap and current_price:
        return market_cap / current_price
    if financials:
        return financials[-1].get("shares_outstanding") if financials[-1].get("shares_outstanding", 0) > 1 else None
    return None
