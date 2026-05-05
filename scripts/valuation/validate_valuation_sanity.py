#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from config_loader import valuation_default


def validate_valuation_sanity(valuation: dict[str, Any]) -> dict[str, Any]:
    checks = []
    ddm = valuation.get("valuation", {}).get("ddm", {})
    ke = (ddm.get("inputs") or {}).get("ke")
    g = (ddm.get("inputs") or {}).get("g")
    spread = (ke - g) if ke is not None and g is not None else None
    if ke is not None and g is not None and ke <= g:
        checks.append({"check": "ddm_ke_vs_g", "status": "invalid", "message": "DDM invalido: Ke <= g."})
    elif spread is not None and spread < valuation_default("min_ke_minus_g_spread", 0.04):
        checks.append({"check": "ddm_ke_vs_g", "status": "warning", "message": "DDM com spread Ke-g muito apertado."})
    for key in ("dcf_fcfe", "dcf_fcff"):
        details = (valuation.get("valuation", {}).get(key, {}) or {}).get("details") or {}
        share = details.get("terminal_value_share")
        if share is not None and share > valuation_default("max_terminal_value_share_without_warning", 0.75):
            checks.append({"check": f"{key}_terminal_value_share", "status": "warning", "message": f"{key} tem {share:.0%} do valor vindo da perpetuidade."})
    bazin = valuation.get("valuation", {}).get("bazin", {})
    if bazin.get("reliability") == "low":
        checks.append({"check": "bazin_source_quality", "status": "invalid", "message": "Bazin invalido para peso principal: dividendos fracos ou de baixa confianca."})
    graham = valuation.get("valuation", {}).get("graham", {})
    if not graham.get("applicable"):
        checks.append({"check": "graham_applicability", "status": "warning", "message": "Graham nao aplicavel para o caso atual."})
    recommended = (valuation.get("ceiling_prices") or {}).get("recommended") or {}
    fair = valuation.get("fair_value_base")
    if fair and recommended.get("price") and recommended["price"] > fair:
        checks.append({"check": "recommended_ceiling_vs_fair_value", "status": "warning", "message": "Preco teto recomendado acima do valor justo base."})
    if valuation.get("calculation_metadata", {}).get("valuation_status") == "complete" and valuation.get("confidence") == "low":
        checks.append({"check": "complete_with_low_confidence", "status": "warning", "message": "Valuation completo marcado com baixa confianca."})
    return {"sanity_checks": checks}
