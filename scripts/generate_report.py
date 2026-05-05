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


def render_ttm(ttm, sector=None):
    if not ttm:
        return "- TTM nao calculado"
    if sector in ("banks", "insurance"):
        return lines([
            f"- Periodo: {ttm.get('period', 'TTM')}",
            f"- Receita TTM: {brl(ttm.get('revenue'))}",
            f"- Lucro liquido TTM: {brl(ttm.get('net_income'))}",
            f"- Dividendos TTM: {brl(ttm.get('dividends_paid'))}",
        ])
    return lines([
        f"- Periodo: {ttm.get('period', 'TTM')}",
        f"- Receita TTM: {brl(ttm.get('revenue'))}",
        f"- EBITDA TTM: {brl(ttm.get('ebitda'))}",
        f"- Lucro liquido TTM: {brl(ttm.get('net_income'))}",
        f"- FCF TTM: {brl(ttm.get('free_cash_flow'))}",
    ])


def render_fundamental_diagnosis(latest, sector=None):
    rows = [
        f"- P/L: {latest.get('p_l')}",
        f"- P/VP: {latest.get('p_vp')}",
        f"- ROE: {pct(latest.get('roe'))}",
        f"- Margem liquida: {pct(latest.get('net_margin'))}",
    ]
    if sector not in ("banks", "insurance"):
        rows.insert(2, f"- EV/EBITDA: {latest.get('ev_ebitda')}")
        rows.insert(4, f"- ROIC: {pct(latest.get('roic'))}")
    return lines(rows)


def render_leverage(latest, sector=None):
    rows = [
        f"- Divida liquida/PL: {latest.get('net_debt_equity')}",
        f"- Cobertura de juros: {latest.get('interest_coverage')}",
    ]
    if sector not in ("banks", "insurance"):
        rows.insert(0, f"- Divida liquida/EBITDA: {latest.get('net_debt_ebitda')}")
    return lines(rows)


def render_dividend_events(events):
    if not events:
        return "- Eventos de dividendos nao coletados"
    recurring = [event for event in events if event.get("is_recurring")]
    extraordinary = [event for event in events if event.get("is_extraordinary") or event.get("event_type") == "extraordinario" or event.get("type") in ("capital_reduction", "restitution")]
    sample = events[-5:]
    rows = [
        f"- Eventos coletados: {len(events)}",
        f"- Recorrentes estimados: {len(recurring)}",
        f"- Extraordinarios/fora da curva estimados: {len(extraordinary)}",
    ]
    rows.extend(
        f"- {event.get('date', event.get('payment_date', 'sem data'))}: {brl(event.get('amount_per_share'))} por acao ({event.get('event_type', event.get('type', 'unknown'))})"
        for event in sample
    )
    return lines(rows)


def render_dividend_policy(policy):
    if not policy:
        return "- Politica de dividendos nao calculada"
    return lines([
        f"- DPA reportado medio anual: {brl(policy.get('reported_dpa_per_year_average'))}",
        f"- DPA extraordinario medio anual: {brl(policy.get('extraordinary_dpa_per_year_average'))}",
        f"- DPA recorrente medio anual: {brl(policy.get('recurring_dpa_per_year_average'))}",
        f"- DPA medio anual recorrente: {brl(policy.get('annual_dpa_mean'))}",
        f"- DPA mediano anual recorrente: {brl(policy.get('annual_dpa_median'))}",
        f"- Dividendo seguro usado: {brl(policy.get('safe_dividend_per_share'))}",
        f"- Yield medio sobre preco atual: {pct(policy.get('yield_mean_on_current_price'))}",
        f"- Yield seguro sobre preco atual: {pct(policy.get('safe_yield_on_current_price'))}",
        f"- Estabilidade: {policy.get('stability')}",
        f"- Cobertura historica de pagamentos: {pct(policy.get('coverage'))}",
        f"- Anos confiaveis: {policy.get('reliable_years')}",
        f"- Payout medio 5 anos: {pct(policy.get('payout_5y'))}",
        f"- Payout medio 10 anos: {pct(policy.get('payout_10y'))}",
        f"- Fontes por evento: {json.dumps(policy.get('source_counts', {}), ensure_ascii=True, sort_keys=True)}",
        f"- Decisao para Bazin/DDM no valor justo: {policy.get('method_action')}",
    ])


def render_dividend_sources(valuation):
    policy = valuation.get("diagnosis", {}).get("dividend_policy", {})
    reconciliation = valuation.get("dividend_reconciliation", {})
    source_summary = valuation.get("dividend_source_summary", {})
    rows = [
        f"- Fontes primarias usadas: {', '.join(reconciliation.get('primary_sources_used', [])) or 'nenhuma'}",
        f"- Fallbacks verificados: {', '.join(reconciliation.get('fallback_sources_checked', [])) or 'nenhum'}",
        f"- Eventos por fonte: {json.dumps(policy.get('source_counts', {}), ensure_ascii=True, sort_keys=True)}",
        f"- Confianca final para Bazin/DDM: {policy.get('income_method_reliability', 'nao informada')}",
    ]
    rows.extend(
        f"- Fonte {name}: attempted={item.get('attempted')} succeeded={item.get('succeeded')} events={item.get('events_found')}"
        for name, item in source_summary.items()
    )
    rows.extend(
        f"- Divergencia reconciliada em {item.get('field')}: selecionado {item.get('selected')}"
        for item in reconciliation.get("divergences", [])
    )
    return lines(rows)


def render_methodology(valuation):
    roles = valuation.get("valuation", {}).get("method_roles", {})
    return lines([
        f"- Metodos principais: {', '.join(roles.get('primary_methods', [])) or 'n/a'}",
        f"- Metodos secundarios: {', '.join(roles.get('secondary_methods', [])) or 'n/a'}",
        f"- Sanity checks: {', '.join(roles.get('sanity_checks', [])) or 'n/a'}",
        f"- Informativos: {', '.join(roles.get('informational_methods', [])) or 'n/a'}",
        *[
            f"- Metodo excluido {item.get('method')}: {item.get('reason')}"
            for item in roles.get("excluded_methods", [])
        ],
    ])


def render_sanity_checks(valuation):
    checks = valuation.get("sanity_validation", {}).get("sanity_checks", [])
    if not checks:
        return "- Nenhum alerta adicional"
    return lines([
        f"- {item.get('check')}: {item.get('status')} - {item.get('message')}"
        for item in checks
    ])


def render_methods(valuation):
    methods = valuation["valuation"]
    bazin = methods["bazin"]["ceiling_prices"]
    bazin_classic = methods["bazin"].get("classic_ceiling_prices", {})
    ddm_inputs = methods["ddm"].get("inputs", {})
    fcfe_inputs = methods["dcf_fcfe"].get("inputs", {})
    fcff_inputs = methods["dcf_fcff"].get("inputs", {})
    rows = [
        f"- Graham: {brl(methods['graham'].get('fair_value'))} | confiabilidade {methods['graham'].get('reliability')}",
        f"- Bazin conservador 6%: {brl(bazin.get('0.06'))}; 8%: {brl(bazin.get('0.08'))}; 10%: {brl(bazin.get('0.1'))}; 12%: {brl(bazin.get('0.12'))}",
        f"- Bazin classico 6%: {brl(bazin_classic.get('0.06'))}; 8%: {brl(bazin_classic.get('0.08'))}; 10%: {brl(bazin_classic.get('0.1'))}; 12%: {brl(bazin_classic.get('0.12'))}",
        f"- Peter Lynch: {methods['peter_lynch'].get('score')} | peso no valor justo: 0",
        f"- DDM/Gordon: {brl(methods['ddm'].get('fair_value'))} | D1 {brl(ddm_inputs.get('d1'))}, Ke {pct(ddm_inputs.get('ke'))}, g {pct(ddm_inputs.get('g'))}, Ke-g {pct(ddm_inputs.get('ke_minus_g'))}",
        f"- DCF FCFE: {brl(methods['dcf_fcfe'].get('fair_value'))} | perpetuidade {pct(fcfe_inputs.get('terminal_value_share'))}",
        f"- DCF FCFF: {brl(methods['dcf_fcff'].get('fair_value'))} | perpetuidade {pct(fcff_inputs.get('terminal_value_share'))}",
        f"- EV/EBITDA normalizado: {brl(methods.get('normalized_ev_ebitda', {}).get('fair_value'))}",
        f"- Lucro residual: {brl(methods['residual_income'].get('fair_value'))}",
        f"- P/VP justificado: {brl(methods.get('p_vp_justified', {}).get('fair_value'))}",
        f"- SOTP: {brl(methods['sotp'].get('fair_value'))}",
        f"- NAV: {brl(methods['nav'].get('fair_value'))}",
    ]
    weights = methods.get("sector_weights") or {}
    if weights:
        rows.append(f"- Pesos setoriais usados no valor justo: {json.dumps(weights, ensure_ascii=True, sort_keys=True)}")
    return lines(rows)


def render_sensitivity(sensitivity):
    matrix = sensitivity.get("ddm_matrix", [])
    rates = sensitivity.get("rates", [])
    growths = sensitivity.get("growths", [])
    rows = ["| Ke \\ g | " + " | ".join(pct(growth) for growth in growths) + " |"]
    rows.append("|---|" + "|".join("---" for _ in growths) + "|")
    for rate, values in zip(rates, matrix):
        rows.append("| " + pct(rate) + " | " + " | ".join(brl(value) for value in values) + " |")
    rows.extend(f"- Bazin yield {key}: {brl(value)}" for key, value in sensitivity.get("bazin_ceiling_prices", {}).items())
    rows.extend(f"- Preco teto com margem {key}: {brl(value)}" for key, value in sensitivity.get("ceiling_by_margin", {}).items())
    return lines(rows)


def render_ceiling_bridge(valuation):
    ceilings = valuation.get("ceiling_prices", {})
    recommended = ceilings.get("recommended", {})
    bazin = ceilings.get("bazin", {})
    intrinsic = ceilings.get("intrinsic_margin", {})
    risk_adjusted = ceilings.get("risk_adjusted", {})
    projected = ceilings.get("projected", {}).get("year_5") or {}
    projected_meta = ceilings.get("projected", {})
    margin_bands = ceilings.get("margin_bands", {})
    risk_policy = valuation.get("calculation_metadata", {}).get("risk_adjustments", {})
    adjustments = risk_policy.get("adjustments", [])
    rows = [
        f"- Valor justo ponderado base: {brl(valuation.get('fair_value_base'))}",
        f"- Teto por margem base: {brl(intrinsic.get('ceiling_price'))} ({pct(intrinsic.get('required_margin'))})",
        f"- Teto ajustado ao risco: {brl(risk_adjusted.get('ceiling_price'))} ({pct(risk_adjusted.get('required_margin'))})",
        f"- Margem base: {pct(risk_policy.get('base_margin'))}",
        f"- Margem final ajustada ao risco: {pct(risk_policy.get('final_margin'))}",
        f"- Bazin classico selecionado: {brl(bazin.get('selected_classic_price'))}",
        f"- Bazin conservador selecionado: {brl(bazin.get('selected_price'))} no yield {pct(bazin.get('selected_yield'))}",
        f"- Teto projetivo presente de entrada: {brl(projected_meta.get('entry_projected_ceiling_price'))}",
        f"- Teto projetivo futuro bruto: {brl(projected_meta.get('projected_future_ceiling_price'))}",
        f"- Teto projetivo ano 5: {brl(projected.get('ceiling_price'))}",
        f"- Faixa teto 15%: {brl(margin_bands.get('0.15'))}",
        f"- Faixa teto 20%: {brl(margin_bands.get('0.20'))}",
        f"- Faixa teto 25%: {brl(margin_bands.get('0.25'))}",
        f"- Preco teto recomendado: {brl(recommended.get('price'))}",
        f"- Semantica do preco teto recomendado: {recommended.get('price_semantics', 'preco_presente_de_entrada')}",
        f"- Metodo recomendado: {recommended.get('method')}",
        f"- Motivo: {recommended.get('reason')}",
    ]
    rows.extend(
        f"- Ajuste de risco: {item.get('name')} +{pct(item.get('impact'))} ({item.get('reason')})"
        for item in adjustments
    )
    return lines(rows)


def render_projected_ceiling_prices(rows):
    if not rows:
        return "- Precos teto projetivos ano a ano nao calculados"
    return lines([
        "- Ano {year}: valor justo futuro {future}, valor presente {present}, margem {mos}, preco teto presente {ceiling}, preco teto futuro {future_ceiling}".format(
            year=row.get("year"),
            future=brl(row.get("future_fair_value")),
            present=brl(row.get("present_value")),
            mos=pct(row.get("margin_of_safety")),
            ceiling=brl(row.get("ceiling_price")),
            future_ceiling=brl(row.get("future_ceiling_price")),
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


def render_future_impacts(items):
    if not items:
        return "- Nenhum cenario adicional informado"
    return lines([
        f"- {item.get('title', 'cenario')}: impacto {item.get('impact', 'n/a')} | efeito no valuation {item.get('effect_on_valuation', 'n/a')} | leitura {item.get('summary', 'n/a')}"
        for item in items
    ])


def generate_markdown(valuation, sensitivity):
    latest = valuation["financial_diagnosis"]["latest"]
    divs = valuation["financial_diagnosis"]["dividends"]
    base = valuation["scenarios"]["base"]
    sector = valuation.get("calculation_metadata", {}).get("sector_key")
    payout_profile = valuation.get("diagnosis", {}).get("payout_profile", {})
    projection_policy = valuation.get("calculation_metadata", {}).get("projection_policy", {})
    projected_basis = valuation.get("projected_ceiling_by_basis", {})
    return f"""# Valuation de {valuation['ticker']} - {valuation['company_name']}

## 1. Resumo executivo
{valuation['ticker']} negocia a {brl(valuation['current_price'])}. O valor justo base estimado e {brl(valuation['fair_value_base'])}, com preco teto recomendado de {brl(valuation['suggested_ceiling_price'])}, preco teto ajustado ao risco de {brl(valuation.get('risk_adjusted_ceiling_price'))} e preco teto projetivo de {brl(valuation['projected_ceiling_price'])}. Veredito: {valuation['verdict']}. Confianca: {valuation['confidence']}.

- Versao da skill: {valuation.get('skill_version', valuation.get('calculation_metadata', {}).get('skill_version', 'valuation-br-stock'))}
- Versao do motor: {valuation.get('calculation_metadata', {}).get('engine_version', 'nao informada')}
- Status do valuation: {valuation.get('calculation_metadata', {}).get('valuation_status', 'nao informado')}

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
- Versao da skill: {valuation.get('skill_version', valuation.get('calculation_metadata', {}).get('skill_version', 'valuation-br-stock'))}
- Versao do motor: {valuation.get('calculation_metadata', {}).get('engine_version', 'nao informada')}
- Setor classificado: {valuation.get('calculation_metadata', {}).get('sector_key', 'nao informado')}
- Pesos setoriais: {json.dumps(valuation.get('calculation_metadata', {}).get('sector_weights', {}), ensure_ascii=True, sort_keys=True)}
- Ke usado: {pct(valuation.get('calculation_metadata', {}).get('discount_rate_policy', {}).get('ke_used'))}
- Ke spot: {pct(valuation.get('calculation_metadata', {}).get('discount_rate_policy', {}).get('ke_spot'))}

## 5. Diagnostico fundamentalista
{render_fundamental_diagnosis(latest, sector)}

### TTM
{render_ttm(valuation.get('ttm'), sector)}

## 6. Qualidade do lucro
- Score de qualidade dos dados: {valuation['data_quality']['score']}/100
- Alertas: {', '.join(valuation['data_quality']['issues']) if valuation['data_quality']['issues'] else 'nenhum alerta critico'}
- Lucro reportado: {brl((valuation.get('quality_of_earnings') or {}).get('reported_net_income'))}
- Lucro ajustado: {brl((valuation.get('quality_of_earnings') or {}).get('adjusted_net_income'))}
- FCF reportado: {brl((valuation.get('quality_of_earnings') or {}).get('reported_fcf'))}
- FCF normalizado: {brl((valuation.get('quality_of_earnings') or {}).get('normalized_fcf'))}

## 7. Dividendos e payout
- Yield seguro: {pct(valuation['dividend_safe_yield'])}
- Yield medio: {pct(divs.get('yield_mean'))}
- Yield mediano: {pct(divs.get('yield_median'))}
- Crescimento de DPA: {pct(divs.get('dpa_growth'))}
- Estabilidade: {divs.get('stability')}
- Payout medio 5 anos: {pct(payout_profile.get('average_5y'))}
- Payout medio 10 anos: {pct(payout_profile.get('average_10y'))}
- Yield on cost projetado no ano 5: {pct(valuation['projected_yield_on_cost_year_5'])}

### Eventos de dividendos
{render_dividend_events(valuation.get('dividend_events', []))}

### Fontes e reconciliacao de dividendos
{render_dividend_sources(valuation)}

### Politica de dividendos para valuation
{render_dividend_policy(valuation.get('diagnosis', {}).get('dividend_policy', {}))}

## 8. Endividamento
{render_leverage(latest, sector)}

## 9. Projecoes ano a ano
- Horizonte usado: {valuation.get('calculation_metadata', {}).get('investment_horizon_years')} anos
- Porte inferido: {valuation.get('calculation_metadata', {}).get('company_size_segment')}
- Inflacao usada do ano 2 em diante: {pct(projection_policy.get('inflation_growth_rate'))}
- Crescimento maximo por Peter Lynch: {pct(valuation.get('diagnosis', {}).get('peter_lynch_expected_growth_rate'))}
- ROE projetado no primeiro ano: {pct(valuation.get('diagnosis', {}).get('projected_roe'))}
- ROE projetado no ultimo ano: {pct(valuation.get('diagnosis', {}).get('projected_roe_year_final'))}
{render_projection(base['projections'])}

## 10. Metodos de valuation
{render_methods(valuation)}

### Metodologia setorial
{render_methodology(valuation)}

## 11. Analise de sensibilidade
{render_sensitivity(sensitivity)}

## 12. Preco teto
- Preco teto recomendado: {brl(valuation['suggested_ceiling_price'])}
- Preco teto base por margem informada: {brl(valuation.get('base_ceiling_price'))}
- Preco teto ajustado ao risco: {brl(valuation.get('risk_adjusted_ceiling_price'))}
- Precos teto Bazin: {json.dumps(valuation['valuation']['bazin']['ceiling_prices'], ensure_ascii=True)}

### Como chegamos ao preco teto recomendado
{render_ceiling_bridge(valuation)}

## 13. Preco teto projetivo
- Preco teto projetivo: {brl(valuation['projected_ceiling_price'])}
- Semantica: preco presente de entrada, descontado ao custo de capital e ja com margem de seguranca
- Preco teto projetivo futuro sem desconto: {brl(valuation.get('projected_future_ceiling_price'))}
{render_projected_ceiling_prices(valuation.get('projected_ceiling_prices', []))}

### Teto projetivo por base
- Lucro liquido: {brl((projected_basis.get('net_income') or {}).get('final_year', {}).get('ceiling_price'))}
- Fluxo de caixa livre: {brl((projected_basis.get('free_cash_flow') or {}).get('final_year', {}).get('ceiling_price'))}
- Lucro liquido sem margem: {brl((projected_basis.get('net_income') or {}).get('final_year', {}).get('future_fair_value'))}
- Fluxo de caixa livre sem margem: {brl((projected_basis.get('free_cash_flow') or {}).get('final_year', {}).get('future_fair_value'))}

## 14. Reverse DCF
- Crescimento implicito: {pct(valuation['valuation']['reverse_dcf'].get('implied_growth'))}
- Base usada: {valuation['valuation']['reverse_dcf'].get('basis')}
- Fluxo atual por acao usado: {brl(valuation['valuation']['reverse_dcf'].get('current_cash_flow_per_share'))}
- Metodo: {valuation['valuation']['reverse_dcf'].get('method')}

## 15. Comparacao com pares
{render_peers(valuation)}

## 16. Riscos
{render_risks(valuation['risks'])}

### Cenarios futuros de impacto
{render_future_impacts(valuation.get('future_impacts', []))}

### Sanity checks do valuation
{render_sanity_checks(valuation)}

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
