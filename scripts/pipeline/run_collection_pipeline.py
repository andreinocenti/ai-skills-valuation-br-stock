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
from collectors.ri_document_collector import collect_ri_documents
from nlp.covenant_detector import detect_covenants
from nlp.guidance_extractor import extract_guidance
from nlp.management_tone_analyzer import analyze_tone
from nlp.non_recurring_detector import extract_non_recurring_items
from nlp.risk_extractor import extract_risks
from parsers.release_parser import parse_release
from quality.quality_of_earnings import build_quality_of_earnings
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


DEFAULT_OUTPUT_DIR = Path.home() / ".valuation-stock-br"


def default_years(count=7):
    last_year = date.today().year - 1
    return list(range(last_year - count + 1, last_year + 1))


def run_pipeline(ticker, cache_dir, years=None, fetch_macro_data=True):
    ticker = ticker.upper().strip()
    years = years or default_years()
    company = enrich_from_cvm_registry(resolve_company(ticker))
    market_data = collect_market_data(ticker)
    ri_documents = collect_ri_documents(ticker)
    parsed_ri_documents = []
    ri_nlp = []
    for document in ri_documents.get("documents", [])[:20]:
        if isinstance(document, dict):
            text = document.get("text") or ""
            meta = dict(document)
        else:
            text = str(document)
            meta = {"url": document}
        parsed = parse_release(text)
        parsed["source"] = meta.get("url") or meta.get("id") or "ri_document"
        parsed_ri_documents.append(parsed)
        ri_nlp.append({
            "source": parsed["source"],
            "guidance": extract_guidance(text),
            "risks": extract_risks(text),
            "covenants": detect_covenants(text),
            "non_recurring_items": extract_non_recurring_items(text),
            "management_tone": analyze_tone(text),
        })
    dividend_data = collect_dividends(ticker, company, cache_dir=cache_dir, years=years)
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
        if dividend_data.get("events"):
            financials = enrich_financials_with_market_data(financials, {"dividend_events": dividend_data.get("events")}, company)
        sources.append(source_entry("CVM DFP estruturada", cvm_result.get("source_status", SOURCE_OFFICIAL), "collected"))
        sources.append(source_entry("CVM ITR estruturada", itr_result.get("source_status", SOURCE_OFFICIAL), "collected"))
    ttm = calculate_ttm(financials, itr_financials)
    peer_group = collect_peer_group(ticker)
    quality_of_earnings = build_quality_of_earnings(financials, parsed_ri_documents)
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
        "investment_horizon_years": None,
        "required_return": None,
        "required_return_reference": infer_required_return(macro_data),
        "desired_dividend_yields": [0.06, 0.08, 0.10, 0.12],
        "margin_of_safety": 0.20,
        "projection_policy": {
            "large_cap_horizon_years": 3,
            "small_cap_horizon_years": 5,
            "large_cap_threshold": 30_000_000_000,
            "inflation_growth_rate": 0.05,
            "current_year_only_explicit_growth": True,
        },
        "company": company,
        "market_data": market_data,
        "macro_data": macro_data,
        "financials": financials,
        "itr_financials": itr_financials,
        "ttm": ttm,
        "dividend_events": dividend_data.get("events", []),
        "dividend_reconciliation": dividend_data.get("reconciliation", {}),
        "dividend_source_summary": dividend_data.get("source_summary", {}),
        "ri_documents": ri_documents.get("documents", []),
        "parsed_ri_documents": parsed_ri_documents,
        "ri_nlp": ri_nlp,
        "quality_of_earnings": quality_of_earnings,
        "peer_group": peer_group.get("peers", []),
        "sources": sources,
        "limitations": limitations,
    }
    return normalize_financials(payload)


def infer_required_return(macro_data):
    selic = macro_data.get("selic")
    if selic is None:
        return 0.12
    spot_required_return = float(selic) / 100 + 0.03
    return clamp_required_return(spot_required_return)


def clamp_required_return(spot_required_return):
    return min(max(float(spot_required_return), 0.10), 0.24)


def main():
    parser = argparse.ArgumentParser(description="Collect public data and build valuation input for a B3 ticker.")
    parser.add_argument("ticker")
    parser.add_argument("--cache-dir", default=str(DEFAULT_OUTPUT_DIR / "cache"))
    parser.add_argument("--years", help="Comma-separated DFP years, e.g. 2020,2021,2022,2023,2024")
    parser.add_argument("--no-macro", action="store_true")
    args = parser.parse_args()
    years = [int(item) for item in args.years.split(",")] if args.years else None
    print(write_json(run_pipeline(args.ticker, args.cache_dir, years, fetch_macro_data=not args.no_macro)))


if __name__ == "__main__":
    main()
