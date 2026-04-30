#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from valuation_core import brl, pct


def lines(items):
    return "\n".join(items) if items else "- n/a"


def render_sources(sources):
    if not sources:
        return "- Dado nao informado"
    return lines([
        f"- {source.get('name')}: {source.get('type')} ({source.get('status', 'unknown')})"
        for source in sources
    ])


def render_projection(rows):
    return lines([
        "- Ano {year}: receita {revenue}, crescimento {growth}, lucro {income}, "
        "LPA {lpa}, dividendos/acao {dpa}, payout {payout}, FCFE {fcfe}, FCFF {fcff}, "
        "divida liquida/EBITDA {leverage}".format(
            year=row["year_offset"],
            revenue=brl(row.get("revenue")),
            growth=pct(row.get("revenue_growth")),
            income=brl(row.get("net_income")),
            lpa=brl(row.get("lpa")),
            dpa=brl(row.get("dividend_per_share")),
            payout=pct(row.get("payout")),
            fcfe=brl(row.get("fcfe")),
            fcff=brl(row.get("fcff")),
            leverage=f"{row.get('net_debt_ebitda'):.2f}x" if row.get("net_debt_ebitda") is not None else "n/a",
        )
        for row in rows
    ])


def render_ttm(ttm):
    if not ttm:
        return "- TTM nao calculado"
    return lines([
        f"- Periodo: {ttm.get('period', 'TTM')}",
        f"- Receita TTM: {brl(ttm.get('revenue'))}",
        f"- EBITDA TTM: {brl(ttm.get('ebitda'))}",
        f"- Lucro liquido TTM: {brl(ttm.get('net_income'))}",
        f"- FCF TTM: {brl(ttm.get('free_cash_flow'))}",
    ])


def render_dividend_events(events):
    if not events:
        return "- Eventos de dividendos nao coletados"
    recurring = [event for event in events if event.get("is_recurring")]
    extraordinary = [event for event in events if event.get("event_type") == "extraordinario"]
    sample = events[-5:]
    rows = [
        f"- Eventos coletados: {len(events)}",
        f"- Recorrentes estimados: {len(recurring)}",
        f"- Extraordinarios/fora da curva estimados: {len(extraordinary)}",
    ]
    rows.extend(
        f"- {event.get('date', 'sem data')}: {brl(event.get('amount_per_share'))} por acao ({event.get('event_type', 'unknown')})"
        for event in sample
    )
    return lines(rows)


def render_dividend_policy(policy):
    if not policy:
        return "- Politica de dividendos nao calculada"
    return lines([
        f"- DPA medio anual recorrente: {brl(policy.get('annual_dpa_mean'))}",
        f"- DPA mediano anual recorrente: {brl(policy.get('annual_dpa_median'))}",
        f"- Dividendo seguro usado: {brl(policy.get('safe_dividend_per_share'))}",
        f"- Yield medio sobre preco atual: {pct(policy.get('yield_mean_on_current_price'))}",
        f"- Yield seguro sobre preco atual: {pct(policy.get('safe_yield_on_current_price'))}",
        f"- Estabilidade: {policy.get('stability')}",
        f"- Cobertura historica de pagamentos: {pct(policy.get('coverage'))}",
        f"- Decisao para Bazin/DDM no valor justo: {policy.get('method_action')}",
    ])


def render_methods(valuation):
    methods = valuation["valuation"]
    bazin = methods["bazin"]["ceiling_prices"]
    rows = [
        f"- Graham: {brl(methods['graham'].get('fair_value'))} | confiabilidade {methods['graham'].get('reliability')}",
        f"- Bazin 6%: {brl(bazin.get('0.06'))}; 8%: {brl(bazin.get('0.08'))}; 10%: {brl(bazin.get('0.1'))}; 12%: {brl(bazin.get('0.12'))}",
        f"- Peter Lynch: {methods['peter_lynch'].get('score')}",
        f"- DDM/Gordon: {brl(methods['ddm'].get('fair_value'))}",
        f"- DCF FCFE: {brl(methods['dcf_fcfe'].get('fair_value'))}",
        f"- DCF FCFF: {brl(methods['dcf_fcff'].get('fair_value'))}",
        f"- EV/EBITDA normalizado: {brl(methods.get('normalized_ev_ebitda', {}).get('fair_value'))}",
        f"- Lucro residual: {brl(methods['residual_income'].get('fair_value'))}",
        f"- SOTP: {brl(methods['sotp'].get('fair_value'))}",
        f"- NAV: {brl(methods['nav'].get('fair_value'))}",
    ]
    weights = methods.get("sector_weights") or {}
    if weights:
        rows.append(f"- Pesos setoriais usados no valor justo: {json.dumps(weights, ensure_ascii=True, sort_keys=True)}")
    return lines(rows)


def render_sensitivity(sensitivity):
    matrix = sensitivity.get("ddm_matrix", [])
    rows = [f"- DDM r/g: {json.dumps(matrix)}"]
    rows.extend(f"- Bazin yield {key}: {brl(value)}" for key, value in sensitivity.get("bazin_ceiling_prices", {}).items())
    rows.extend(f"- Preco teto com margem {key}: {brl(value)}" for key, value in sensitivity.get("ceiling_by_margin", {}).items())
    return lines(rows)


def render_projected_ceiling_prices(rows):
    if not rows:
        return "- Precos teto projetivos ano a ano nao calculados"
    return lines([
        "- Ano {year}: valor justo futuro {future}, valor presente {present}, margem {mos}, preco teto {ceiling}".format(
            year=row.get("year"),
            future=brl(row.get("future_fair_value")),
            present=brl(row.get("present_value")),
            mos=pct(row.get("margin_of_safety")),
            ceiling=brl(row.get("ceiling_price")),
        )
        for row in rows
    ])


def render_peers(valuation):
    multiples = valuation["valuation"]["multiples"]
    if not multiples.get("available"):
        rows = [f"- {multiples.get('message', 'pares nao disponiveis')}"]
        if multiples.get("peers"):
            rows.append(f"- Pares mapeados: {', '.join(multiples['peers'])}")
        return lines(rows)
    rows = []
    for key, value in multiples.get("relative_discount", {}).items():
        rows.append(f"- {key}: empresa {multiples['company'].get(key)}, pares {multiples['peer_average'].get(key)}, desconto relativo {pct(value)}")
    return lines(rows)


def render_risks(risks):
    return lines([
        f"- {risk['name']}: probabilidade {risk['probability']}, impacto {risk['impact']}, severidade {risk['severity']}, efeito {risk['effect_on_valuation']}"
        for risk in risks
    ])


def generate_markdown(valuation, sensitivity):
    latest = valuation["financial_diagnosis"]["latest"]
    divs = valuation["financial_diagnosis"]["dividends"]
    base = valuation["scenarios"]["base"]
    return f"""# Valuation de {valuation['ticker']} - {valuation['company_name']}

## 1. Resumo executivo
{valuation['ticker']} negocia a {brl(valuation['current_price'])}. O valor justo base estimado e {brl(valuation['fair_value_base'])}, com preco teto base de {brl(valuation['suggested_ceiling_price'])}, preco teto ajustado ao risco de {brl(valuation.get('risk_adjusted_ceiling_price'))} e preco teto projetivo de {brl(valuation['projected_ceiling_price'])}. Veredito: {valuation['verdict']}. Confianca: {valuation['confidence']}.

## 2. Dados da empresa
- Nome: {valuation['company_name']}
- Setor: {valuation.get('company', {}).get('sector', 'nao informado')}
- Subsetor: {valuation.get('company', {}).get('subsector', 'nao informado')}
- Classe: {valuation.get('company', {}).get('share_class', 'nao informado')}

## 3. Fontes utilizadas
{render_sources(valuation.get('sources', []))}

## 4. Cotacao atual e visao geral
- Preco atual: {brl(valuation['current_price'])}
- Margem de seguranca atual: {pct(valuation['margin_of_safety'])}
- Margem base informada: {pct(valuation.get('base_margin_of_safety'))}
- Margem exigida ajustada ao risco: {pct(valuation['required_margin_of_safety'])}
- Risco: {valuation['risk_level']}
- Versao do motor: {valuation.get('calculation_metadata', {}).get('engine_version', 'nao informada')}
- Setor classificado: {valuation.get('calculation_metadata', {}).get('sector_key', 'nao informado')}
- Pesos setoriais: {json.dumps(valuation.get('calculation_metadata', {}).get('sector_weights', {}), ensure_ascii=True, sort_keys=True)}

## 5. Diagnostico fundamentalista
- P/L: {latest.get('p_l')}
- P/VP: {latest.get('p_vp')}
- EV/EBITDA: {latest.get('ev_ebitda')}
- ROE: {pct(latest.get('roe'))}
- ROIC: {pct(latest.get('roic'))}
- Margem liquida: {pct(latest.get('net_margin'))}

### TTM
{render_ttm(valuation.get('ttm'))}

## 6. Qualidade do lucro
- Score de qualidade dos dados: {valuation['data_quality']['score']}/100
- Alertas: {', '.join(valuation['data_quality']['issues']) if valuation['data_quality']['issues'] else 'nenhum alerta critico'}

## 7. Dividendos e payout
- Yield seguro: {pct(valuation['dividend_safe_yield'])}
- Yield medio: {pct(divs.get('yield_mean'))}
- Yield mediano: {pct(divs.get('yield_median'))}
- Crescimento de DPA: {pct(divs.get('dpa_growth'))}
- Estabilidade: {divs.get('stability')}
- Yield on cost projetado no ano 5: {pct(valuation['projected_yield_on_cost_year_5'])}

### Eventos de dividendos
{render_dividend_events(valuation.get('dividend_events', []))}

### Politica de dividendos para valuation
{render_dividend_policy(valuation.get('diagnosis', {}).get('dividend_policy', {}))}

## 8. Endividamento
- Divida liquida/EBITDA: {latest.get('net_debt_ebitda')}
- Divida liquida/PL: {latest.get('net_debt_equity')}
- Cobertura de juros: {latest.get('interest_coverage')}

## 9. Projecoes ano a ano
{render_projection(base['projections'])}

## 10. Metodos de valuation
{render_methods(valuation)}

## 11. Analise de sensibilidade
{render_sensitivity(sensitivity)}

## 12. Preco teto
- Preco teto base por margem informada: {brl(valuation['suggested_ceiling_price'])}
- Preco teto ajustado ao risco: {brl(valuation.get('risk_adjusted_ceiling_price'))}
- Precos teto Bazin: {json.dumps(valuation['valuation']['bazin']['ceiling_prices'], ensure_ascii=True)}

## 13. Preco teto projetivo
- Preco teto projetivo: {brl(valuation['projected_ceiling_price'])}
{render_projected_ceiling_prices(valuation.get('projected_ceiling_prices', []))}

## 14. Reverse DCF
- Crescimento implicito: {pct(valuation['valuation']['reverse_dcf'].get('implied_growth'))}

## 15. Comparacao com pares
{render_peers(valuation)}

## 16. Riscos
{render_risks(valuation['risks'])}

## 17. Score final
- Score de qualidade: {valuation['quality_score']}/100
- Score de oportunidade: {valuation['opportunity_score']}/100
- Score de dividendos: {valuation['scores']['dividends']}/100
- Score de divida: {valuation['scores']['debt']}/100

## 18. Veredito
{valuation['verdict']}

## 19. Limitacoes da analise
{lines([f"- {item}" for item in valuation['limitations']])}
"""


def main():
    if len(sys.argv) != 3:
        print("usage: generate_report.py <valuation.json> <sensitivity.json>", file=sys.stderr)
        sys.exit(1)
    valuation = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sensitivity = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    valuation["sensitivity"] = sensitivity
    print(json.dumps({"markdown": generate_markdown(valuation, sensitivity), "json": valuation}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
