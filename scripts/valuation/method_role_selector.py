#!/usr/bin/env python3
from __future__ import annotations


def select_method_roles(sector_key: str, dividends_reliable: bool = False, has_sotp: bool = False) -> dict[str, object]:
    if sector_key == "banks":
        return {
            "primary_methods": ["residual_income", "p_vp_justified"],
            "secondary_methods": ["dividend_capacity"],
            "sanity_checks": ["graham"],
            "informational_methods": ["peter_lynch", "reverse_dcf"],
            "excluded_methods": [
                {"method": "ev_ebitda", "reason": "bancos nao devem usar EV/EBITDA como metodo principal"},
                {"method": "dcf_fcff", "reason": "bancos nao devem usar FCFF como metodo principal"},
                {"method": "peter_lynch", "reason": "score informativo, nao gera valor justo em R$"},
            ],
        }
    if sector_key == "holding":
        return {
            "primary_methods": ["sotp" if has_sotp else "nav", "nav" if has_sotp else "sotp"],
            "secondary_methods": ["dividend_look_through"],
            "sanity_checks": ["graham"],
            "informational_methods": ["peter_lynch", "reverse_dcf"],
            "excluded_methods": [{"method": "peter_lynch", "reason": "score informativo, nao gera valor justo em R$"}],
        }
    if sector_key == "utilities":
        primary = ["ddm", "dcf_fcfe"] if dividends_reliable else ["dcf_fcfe", "ev_ebitda"]
        return {
            "primary_methods": primary,
            "secondary_methods": ["ev_ebitda"],
            "sanity_checks": ["bazin", "graham"],
            "informational_methods": ["peter_lynch", "reverse_dcf"],
            "excluded_methods": [{"method": "peter_lynch", "reason": "score informativo, nao gera valor justo em R$"}],
        }
    if sector_key in ("commodities", "pulp_paper"):
        return {
            "primary_methods": ["normalized_ev_ebitda", "dcf_fcff" if sector_key == "commodities" else "dcf_fcfe"],
            "secondary_methods": ["multiples"],
            "sanity_checks": ["graham", "bazin"],
            "informational_methods": ["peter_lynch", "reverse_dcf"],
            "excluded_methods": [{"method": "peter_lynch", "reason": "score informativo, nao gera valor justo em R$"}],
        }
    return {
        "primary_methods": ["dcf_fcfe", "dcf_fcff"],
        "secondary_methods": ["multiples"],
        "sanity_checks": ["graham", "bazin"],
        "informational_methods": ["peter_lynch", "reverse_dcf"],
        "excluded_methods": [{"method": "peter_lynch", "reason": "score informativo, nao gera valor justo em R$"}],
    }
