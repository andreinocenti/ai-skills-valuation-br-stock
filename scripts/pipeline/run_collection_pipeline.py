#!/usr/bin/env python3
import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.company_resolver import enrich_from_cvm_registry, resolve_company
from collectors.cvm_collector import collect_dfp_financials, collect_itr_financials
from collectors.dividend_collector import collect_dividends
from collectors.market_data_collector import collect_market_data
from collectors.macro_collector import collect_macro
from collectors.peer_group_collector import collect_peer_group
from valuation_core import (
    calculate_ttm,
    SOURCE_AUXILIARY,
    SOURCE_INFERRED,
    SOURCE_OFFICIAL,
    enrich_financials_with_market_data,
    merge_financial_rows,
    normalize_financials,
    source_entry,
    write_json,
)


def default_years(count=7):
    last_year = date.today().year - 1
    return list(range(last_year - count + 1, last_year + 1))


def run_pipeline(ticker, cache_dir, years=None, fetch_macro_data=True):
    ticker = ticker.upper().strip()
    years = years or default_years()
    company = enrich_from_cvm_registry(resolve_company(ticker))
    market_data = collect_market_data(ticker)
    dividend_data = collect_dividends(ticker)
    macro_data = collect_macro() if fetch_macro_data else {}
    sources = [
        source_entry("company_resolver", company.get("source_status", SOURCE_INFERRED), "resolved"),
        source_entry("market_data_collector", market_data.get("source_status", SOURCE_AUXILIARY), "collected", market_data.get("source_url")),
        source_entry("dividend_collector", dividend_data.get("source_status", SOURCE_AUXILIARY), "collected", dividend_data.get("source_url")),
    ]
    if macro_data:
        sources.append(source_entry("Banco Central SGS", macro_data.get("source_status", SOURCE_OFFICIAL), "collected"))
    financials = []
    itr_financials = []
    cvm_code = company.get("cvm_code")
    if cvm_code:
        cvm_result = collect_dfp_financials(cvm_code, years, cache_dir)
        financials = merge_financial_rows(cvm_result.get("financials", []))
        itr_result = collect_itr_financials(cvm_code, [years[-1]], cache_dir)
        itr_financials = merge_financial_rows(itr_result.get("financials", []))
        financials = enrich_financials_with_market_data(financials, market_data, company)
        sources.append(source_entry("CVM DFP estruturada", cvm_result.get("source_status", SOURCE_OFFICIAL), "collected"))
        sources.append(source_entry("CVM ITR estruturada", itr_result.get("source_status", SOURCE_OFFICIAL), "collected"))
    ttm = calculate_ttm(financials, itr_financials)
    peer_group = collect_peer_group(ticker)
    limitations = []
    if not cvm_code:
        limitations.append("Codigo CVM nao resolvido automaticamente para o ticker.")
    if len(financials) < 3:
        limitations.append("Demonstrativos financeiros insuficientes para valuation completo; forneca JSON estruturado ou revise coleta CVM.")
    if not market_data.get("current_price"):
        limitations.append("Cotacao atual nao coletada automaticamente.")
    payload = {
        "ticker": ticker,
        "market": "B3",
        "analysis_focus": "full",
        "investment_horizon_years": 5,
        "required_return": infer_required_return(macro_data),
        "desired_dividend_yields": [0.06, 0.08, 0.10, 0.12],
        "margin_of_safety": 0.25,
        "company": company,
        "market_data": market_data,
        "macro_data": macro_data,
        "financials": financials,
        "itr_financials": itr_financials,
        "ttm": ttm,
        "dividend_events": dividend_data.get("events", []),
        "peer_group": peer_group.get("peers", []),
        "sources": sources,
        "limitations": limitations,
    }
    return normalize_financials(payload)


def infer_required_return(macro_data):
    selic = macro_data.get("selic")
    if selic is None:
        return 0.12
    # BCB SGS 432 is annual percentage, so convert 10.5 into 0.105 and add equity risk buffer.
    return max(float(selic) / 100 + 0.03, 0.10)


def main():
    parser = argparse.ArgumentParser(description="Collect public data and build valuation input for a B3 ticker.")
    parser.add_argument("ticker")
    parser.add_argument("--cache-dir", default="/tmp/valuation-br-stock-cache")
    parser.add_argument("--years", help="Comma-separated DFP years, e.g. 2020,2021,2022,2023,2024")
    parser.add_argument("--no-macro", action="store_true")
    args = parser.parse_args()
    years = [int(item) for item in args.years.split(",")] if args.years else None
    print(write_json(run_pipeline(args.ticker, args.cache_dir, years, fetch_macro_data=not args.no_macro)))


if __name__ == "__main__":
    main()
