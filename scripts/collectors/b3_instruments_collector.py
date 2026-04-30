#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import SOURCE_AUXILIARY, ticker_registry, write_json


def collect_b3_instruments():
    rows = []
    for ticker, company in sorted(ticker_registry().items()):
        rows.append({
            "ticker": ticker,
            "company_name": company.get("name"),
            "sector": company.get("sector"),
            "subsector": company.get("subsector"),
            "segment": company.get("segment"),
            "share_class": company.get("share_class"),
            "cvm_code": company.get("cvm_code"),
            "cnpj": company.get("cnpj"),
            "ri_url": company.get("ri_url"),
        })
    return {
        "source_status": SOURCE_AUXILIARY,
        "source": "references/ticker_registry.json",
        "instruments": rows,
    }


def main():
    print(write_json(collect_b3_instruments()))


if __name__ == "__main__":
    main()
