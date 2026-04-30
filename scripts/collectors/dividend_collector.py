#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.market_data_collector import collect_market_data
from valuation_core import normalize_dividend_events, write_json


def collect_dividends(ticker):
    market = collect_market_data(ticker)
    events = normalize_dividend_events(market.get("dividend_history") or [])
    return {
        "ticker": ticker.upper(),
        "events": events,
        "source_status": market.get("source_status"),
        "source_url": market.get("source_url"),
        "limitations": ["Proventos via fonte auxiliar quando fonte oficial B3/CVM/RI nao estiver disponivel."],
    }


def main():
    if len(sys.argv) != 2:
        print("usage: dividend_collector.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_dividends(sys.argv[1])))


if __name__ == "__main__":
    main()
