#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import SOURCE_AUXILIARY, SOURCE_NOT_FOUND, fetch_url, write_json


def collect_market_data(ticker):
    symbol = ticker.upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.SA?range=10y&interval=1d&events=div"
    try:
        payload = json.loads(fetch_url(url).decode("utf-8"))
        result = payload["chart"]["result"][0]
        meta = result.get("meta", {})
        quote = result["indicators"]["quote"][0]
        closes = [value for value in quote.get("close", []) if value is not None]
        dividends = result.get("events", {}).get("dividends", {})
        dividend_history = [event.get("amount") for event in dividends.values() if event.get("amount") is not None]
        return {
            "current_price": closes[-1] if closes else None,
            "market_cap": meta.get("marketCap"),
            "currency": meta.get("currency"),
            "price_history": closes,
            "dividend_history": dividend_history,
            "source_status": SOURCE_AUXILIARY,
            "source_url": url,
        }
    except Exception as exc:
        return {"current_price": None, "price_history": [], "dividend_history": [], "source_status": SOURCE_NOT_FOUND, "error": str(exc)}


def main():
    if len(sys.argv) != 2:
        print("usage: market_data_collector.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_market_data(sys.argv[1])))


if __name__ == "__main__":
    main()
