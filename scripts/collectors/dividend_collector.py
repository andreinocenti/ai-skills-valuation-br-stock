#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.dividends.official_dividend_collector import OfficialDividendCollector
from valuation_core import SOURCE_AUXILIARY, SOURCE_NOT_FOUND, write_json


def collect_dividends(ticker, company_profile=None, cache_dir=None, years=None, test_overrides=None):
    company_profile = company_profile or {"ticker": ticker.upper()}
    result = OfficialDividendCollector().collect(ticker, company_profile, cache_dir=cache_dir, years=years, test_overrides=test_overrides)
    sources = {event.get("source") for event in result.get("events", [])}
    if sources & {"CVM_IPE", "B3", "RI"}:
        source_status = "oficial"
    elif result.get("events"):
        source_status = SOURCE_AUXILIARY
    else:
        source_status = SOURCE_NOT_FOUND
    return {
        "ticker": ticker.upper(),
        "events": result.get("events", []),
        "reconciliation": result.get("reconciliation", {}),
        "collection": result.get("collection", {}),
        "warnings": result.get("warnings", []),
        "source_summary": result.get("source_summary", {}),
        "source_status": source_status,
        "source_url": None,
        "limitations": ["Fontes oficiais CVM/B3/RI priorizadas; auxiliares usados apenas como fallback."],
    }


def main():
    if len(sys.argv) != 2:
        print("usage: dividend_collector.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_dividends(sys.argv[1])))


if __name__ == "__main__":
    main()
