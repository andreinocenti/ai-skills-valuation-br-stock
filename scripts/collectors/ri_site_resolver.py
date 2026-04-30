#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.company_resolver import resolve_company
from valuation_core import SOURCE_NOT_FOUND, ticker_registry, write_json


def resolve_ri_site(ticker):
    ticker = ticker.upper()
    company = ticker_registry().get(ticker) or resolve_company(ticker)
    ri_url = company.get("ri_url")
    return {
        "ticker": ticker,
        "company_name": company.get("name"),
        "ri_url": ri_url,
        "source_status": company.get("source_status") if ri_url else SOURCE_NOT_FOUND,
    }


def main():
    if len(sys.argv) != 2:
        print("usage: ri_site_resolver.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(resolve_ri_site(sys.argv[1])))


if __name__ == "__main__":
    main()
