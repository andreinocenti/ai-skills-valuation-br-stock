#!/usr/bin/env python3
import json
import sys


REQUIRED_HEADINGS = [
    "## 1. Resumo executivo",
    "## 2. Dados da empresa",
    "## 3. Fontes utilizadas",
    "## 4. Cotacao atual e visao geral",
    "## 5. Diagnostico fundamentalista",
    "## 6. Qualidade do lucro",
    "## 7. Dividendos e payout",
    "## 8. Endividamento",
    "## 9. Projecoes ano a ano",
    "## 10. Metodos de valuation",
    "## 11. Analise de sensibilidade",
    "## 12. Preco teto",
    "## 13. Preco teto projetivo",
    "## 14. Reverse DCF",
    "## 15. Comparacao com pares",
    "## 16. Riscos",
    "## 17. Score final",
    "## 18. Veredito",
    "## 19. Limitacoes da analise",
]

REQUIRED_JSON_KEYS = [
    "ticker",
    "company_name",
    "current_price",
    "fair_value_base",
    "fair_value_conservative",
    "fair_value_optimistic",
    "suggested_ceiling_price",
    "base_ceiling_price",
    "risk_adjusted_ceiling_price",
    "projected_ceiling_price",
    "projected_ceiling_prices",
    "margin_of_safety",
    "dividend_safe_yield",
    "projected_yield_on_cost_year_5",
    "quality_score",
    "opportunity_score",
    "risk_level",
    "verdict",
    "confidence",
    "calculation_metadata",
    "data_quality",
    "financial_diagnosis",
    "valuation",
    "scenarios",
    "risks",
    "scores",
    "limitations",
]

REQUIRED_METHODS = [
    "graham",
    "bazin",
    "peter_lynch",
    "ddm",
    "dcf_fcfe",
    "dcf_fcff",
    "multiples",
    "normalized_ev_ebitda",
    "reverse_dcf",
    "residual_income",
    "sotp",
    "nav",
    "sector_weights",
]


def main():
    if len(sys.argv) != 2:
        print("usage: validate_output.py <report.json>", file=sys.stderr)
        sys.exit(1)
    report = json.load(open(sys.argv[1], encoding="utf-8"))
    markdown = report.get("markdown", "")
    payload = report.get("json", {})
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in markdown]
    missing += [key for key in REQUIRED_JSON_KEYS if key not in payload]
    valuation = payload.get("valuation", {})
    missing += [f"valuation.{method}" for method in REQUIRED_METHODS if method not in valuation]
    if not payload.get("risks"):
        missing.append("risks")
    if not payload.get("limitations"):
        missing.append("limitations")
    if payload.get("verdict") not in ["Evitar", "Cara", "Justa", "Interessante", "Atrativa com margem de seguranca"]:
        missing.append("valid_verdict")
    ok = not missing
    print(json.dumps({"ok": ok, "missing": missing}, ensure_ascii=True, indent=2))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
