#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import ticker_registry, write_json


def resolve_ticker(ticker):
    return ticker_registry().get(ticker.upper())


def main():
    registry = ticker_registry()
    if len(sys.argv) == 1:
        print(write_json({"tickers": sorted(registry), "companies": registry}))
        return
    if len(sys.argv) == 2:
        ticker = sys.argv[1].upper()
        print(write_json({"ticker": ticker, "company": resolve_ticker(ticker)}))
        return
    print("usage: ticker_registry.py [ticker]", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
