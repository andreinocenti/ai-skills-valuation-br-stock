#!/usr/bin/env python3
import csv
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_report import render_dividend_events
from valuation_core import (
    build_bazin_ceiling,
    calculate_valuation,
    ddm_value,
    enrich_financials_with_market_data,
    parse_cvm_dfp_zip,
    project_years,
    sector_key,
    sector_method_weights,
)
from pipeline.run_collection_pipeline import infer_required_return


def assert_close(actual, expected, tolerance=1e-6):
    if actual is None or abs(actual - expected) > tolerance:
        raise AssertionError(f"expected {expected}, got {actual}")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def csv_content(rows):
    output = io.StringIO()
    fields = ["CD_CVM", "DT_FIM_EXERC", "CD_CONTA", "VL_CONTA", "ESCALA_MOEDA", "ORDEM_EXERC", "CNPJ_CIA", "DENOM_CIA"]
    writer = csv.DictWriter(output, fieldnames=fields, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("latin1")


def test_peter_lynch_scale():
    financials = []
    revenue = 1000.0
    net_income = 100.0
    for year in range(2020, 2025):
        financials.append({
            "year": year,
            "revenue": revenue,
            "ebitda": revenue * 0.30,
            "ebit": revenue * 0.25,
            "net_income": net_income,
            "equity": 1000.0,
            "operating_cash_flow": 140.0,
            "capex": 30.0,
            "free_cash_flow": 110.0,
            "dividends_paid": 5.0,
            "shares_outstanding": 10.0,
            "gross_debt": 100.0,
            "cash": 50.0,
            "depreciation_amortization": 50.0,
            "working_capital_change": 0.0,
            "net_debt_issuance": 0.0,
        })
        revenue *= 1.15
        net_income *= 1.15
    latest_lpa = financials[-1]["net_income"] / financials[-1]["shares_outstanding"]
    price = latest_lpa * 10
    data = {
        "ticker": "TEST3",
        "required_return": 0.12,
        "company": {"name": "Teste", "sector": "Geral"},
        "market_data": {"current_price": price},
        "financials": financials,
    }
    valuation = calculate_valuation(data)
    lynch = valuation["valuation"]["peter_lynch"]["score"]
    assert_true(lynch and 1.4 < lynch < 2.2, f"Peter Lynch scale should be around 2.0, got {lynch}")


def test_projection_uses_operating_margins():
    base = {
        "revenue": 1000.0,
        "equity": 1000.0,
        "shares_outstanding": 100.0,
        "net_debt": 100.0,
        "net_income": 100.0,
        "ebitda": 300.0,
        "ebit": 250.0,
        "depreciation_amortization": 50.0,
        "capex": 30.0,
        "working_capital_change": 0.0,
        "tax_rate": 0.34,
    }
    scenario = {"years": 1, "revenue_growth": 0.0, "margin": 0.10, "payout": 0.3}
    projected = project_years(base, scenario)[0]
    assert_close(projected["ebitda_margin"], 0.30)
    assert_close(projected["ebit"] / projected["revenue"], 0.25)


def test_cvm_da_builds_ebitda():
    row_base = {
        "CD_CVM": "2453",
        "DT_FIM_EXERC": "2024-12-31",
        "ESCALA_MOEDA": "UNIDADE",
        "ORDEM_EXERC": "ULTIMO",
        "CNPJ_CIA": "00.000.000/0001-00",
        "DENOM_CIA": "TESTE",
    }

    def row(code, value):
        item = dict(row_base)
        item.update({"CD_CONTA": code, "VL_CONTA": str(value)})
        return item

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "dfp.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("DRE_con.csv", csv_content([row("3.01", 1000), row("3.05", 250), row("3.11", 150)]))
            archive.writestr("BPA_con.csv", csv_content([row("1.01.01", 100)]))
            archive.writestr("BPP_con.csv", csv_content([row("2.03", 800), row("2.01.04", 50), row("2.02.01", 100)]))
            archive.writestr("DFC_MI_con.csv", csv_content([row("6.01", 300), row("6.01.01.01", 80), row("6.02.01", -40)]))
            archive.writestr("composicao_capital.csv", csv_content([]))
        parsed = parse_cvm_dfp_zip(path, "2453")
    assert_true(parsed, "CVM parser should return a row")
    assert_close(parsed[0]["depreciation_amortization"], 80.0)
    assert_close(parsed[0]["ebitda"], 330.0)
    assert_true(parsed[0]["ebitda_estimated"] is False, "EBITDA should not be marked estimated when D&A exists")


def test_dividend_event_render_keys():
    text = render_dividend_events([
        {"date": "2024-01-01", "amount_per_share": 1.0, "event_type": "dividendo", "is_recurring": True},
        {"date": "2024-06-01", "amount_per_share": 4.0, "event_type": "extraordinario", "is_recurring": False},
    ])
    assert_true("Recorrentes estimados: 1" in text, text)
    assert_true("Extraordinarios/fora da curva estimados: 1" in text, text)
    assert_true("(extraordinario)" in text, text)


def test_dividends_are_aggregated_by_year():
    financials = [
        {"year": 2023, "net_income": 1000.0, "shares_outstanding": 100.0},
        {"year": 2024, "net_income": 1000.0, "shares_outstanding": 100.0},
    ]
    market_data = {
        "dividend_events": [
            {"date": "2024-01-10", "year": 2024, "amount_per_share": 0.20},
            {"date": "2024-05-10", "year": 2024, "amount_per_share": 0.30},
            {"date": "2024-10-10", "year": 2024, "amount_per_share": 0.50},
        ]
    }
    enriched = enrich_financials_with_market_data(financials, market_data, {"shares_outstanding": 100.0})
    assert_close(enriched[-1]["dividends_paid"], 100.0)


def test_projected_ceiling_prices_are_yearly():
    data = json.loads((ROOT / "examples" / "example_input.json").read_text(encoding="utf-8"))
    valuation = calculate_valuation(data)
    rows = valuation.get("projected_ceiling_prices")
    assert_true(len(rows) == data["investment_horizon_years"], "projected ceiling should have one row per year")
    assert_true(rows[-1]["ceiling_price"] == valuation["projected_ceiling_price"], "headline projected ceiling should match final year")


def test_irregular_dividends_do_not_drive_weighted_fair_value():
    data = json.loads((ROOT / "examples" / "example_input.json").read_text(encoding="utf-8"))
    for index, row in enumerate(data["financials"]):
        row["dividends_paid"] = 0.0 if index % 2 == 0 else row["net_income"] * 1.5
    valuation = calculate_valuation(data)
    policy = valuation["diagnosis"]["dividend_policy"]
    assert_true(policy["income_method_reliability"] == "low", policy)
    assert_true(policy["suitable_for_bazin_ddm_weight"] is False, policy)
    assert_true(valuation["valuation"]["bazin"]["ceiling_prices"], "Bazin should still be calculated for reference")
    assert_true(valuation["valuation"]["ddm"]["fair_value"] is not None, "DDM should still be calculated for reference")


def test_paper_and_pulp_is_cyclical_sector():
    sector = sector_key({"sector": "Papel e Celulose", "subsector": "Madeira e Papel"})
    assert_true(sector == "commodities", sector)


def test_ceiling_prices_are_split_between_base_and_risk_adjusted():
    data = json.loads((ROOT / "examples" / "example_input.json").read_text(encoding="utf-8"))
    data["margin_of_safety"] = 0.25
    valuation = calculate_valuation(data)
    ceilings = valuation["ceiling_prices"]
    assert_close(valuation["suggested_ceiling_price"], ceilings["recommended"]["price"])
    assert_close(valuation["base_ceiling_price"], ceilings["intrinsic_margin"]["ceiling_price"])
    assert_true("risk_adjusted_ceiling_price" in valuation, "risk-adjusted ceiling should be explicit")
    assert_true(ceilings["recommended"]["method"], ceilings["recommended"])


def test_required_return_uses_macro_and_is_not_fixed_at_12_percent():
    assert_true(infer_required_return({"selic": 14.5}) > 0.12, "high Selic should produce Ke above 12%")
    assert_close(infer_required_return({"selic": 14.5}), 0.175)


def test_bazin_classic_and_conservative_are_separate():
    policy = {
        "annual_dpa_median": 1.20,
        "annual_dpa_mean": 1.30,
        "safe_dividend_per_share": 0.84,
        "method_action": "calculate_but_exclude_from_weighted_fair_value",
    }
    bazin = build_bazin_ceiling(policy, [0.06, 0.08, 0.10, 0.12], {"selic": 10.0})
    assert_close(bazin["classic"]["0.08"], 15.0)
    assert_close(bazin["conservative"]["0.08"], 10.5)
    assert_true(bazin["selected_yield"] == 0.10, bazin)


def test_ddm_is_invalid_when_ke_is_not_above_growth():
    assert_true(ddm_value(1.0, 0.08, 0.09) is None, "DDM must not apply when Ke <= g")
    assert_close(ddm_value(1.0, 0.12, 0.04), 12.5)


def test_sector_weights_are_distinct_and_complete():
    assert_true("multiples" in sector_method_weights("utilities"), sector_method_weights("utilities"))
    assert_true(sector_method_weights("insurance") != sector_method_weights("banks"), "insurance should not reuse bank weights")
    assert_true("normalized_ev_ebitda" in sector_method_weights("commodities"), sector_method_weights("commodities"))


def test_commodity_uses_normalized_ev_ebitda():
    data = json.loads((ROOT / "examples" / "vale3_example_input.json").read_text(encoding="utf-8"))
    data["company"]["sector"] = "Mineracao e commodities"
    valuation = calculate_valuation(data)
    assert_true(valuation["valuation"]["normalized_ev_ebitda"]["fair_value"] is not None, valuation["valuation"]["normalized_ev_ebitda"])
    assert_true("normalized_ev_ebitda" in valuation["valuation"]["sector_weights"], valuation["valuation"]["sector_weights"])


def test_holding_without_sotp_is_limited():
    data = json.loads((ROOT / "examples" / "example_input.json").read_text(encoding="utf-8"))
    data["company"]["sector"] = "Holding"
    valuation = calculate_valuation(data)
    assert_true(valuation["valuation"]["sotp"]["reliability"] == "not_available", valuation["valuation"]["sotp"])
    assert_true(any("Holding sem SOTP/NAV" in item for item in valuation["limitations"]), valuation["limitations"])


def test_report_exposes_skill_and_engine_versions():
    data = json.loads((ROOT / "examples" / "example_input.json").read_text(encoding="utf-8"))
    valuation = calculate_valuation(data)
    assert_true(valuation["skill_version"] == "valuation-br-stock", valuation.get("skill_version"))
    assert_true(valuation["calculation_metadata"]["engine_version"], valuation["calculation_metadata"])


def main():
    test_peter_lynch_scale()
    test_projection_uses_operating_margins()
    test_cvm_da_builds_ebitda()
    test_dividend_event_render_keys()
    test_dividends_are_aggregated_by_year()
    test_projected_ceiling_prices_are_yearly()
    test_irregular_dividends_do_not_drive_weighted_fair_value()
    test_paper_and_pulp_is_cyclical_sector()
    test_ceiling_prices_are_split_between_base_and_risk_adjusted()
    test_required_return_uses_macro_and_is_not_fixed_at_12_percent()
    test_bazin_classic_and_conservative_are_separate()
    test_ddm_is_invalid_when_ke_is_not_above_growth()
    test_sector_weights_are_distinct_and_complete()
    test_commodity_uses_normalized_ev_ebitda()
    test_holding_without_sotp_is_limited()
    test_report_exposes_skill_and_engine_versions()
    print("ok")


if __name__ == "__main__":
    main()
