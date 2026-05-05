#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config_loader import data_source_flag
from valuation_core import SOURCE_AUXILIARY, SOURCE_NOT_FOUND, fetch_url, write_json


BRAPI_URL = "https://brapi.dev/api/quote/{symbol}"
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.SA?range=10y&interval=1d&events=div"


def _parse_events_from_brapi(payload):
    results = payload.get("results") or []
    if not results:
        return None
    item = results[0]
    current_price = item.get("regularMarketPrice")
    market_cap = item.get("marketCap")
    currency = item.get("currency") or "BRL"
    dividend_events = []
    cash_dividends = ((item.get("dividendsData") or {}).get("cashDividends") or [])
    for dividend in cash_dividends:
        amount = dividend.get("rate")
        payment_date = dividend.get("paymentDate")
        if amount is None:
            continue
        dividend_events.append({
            "date": payment_date,
            "year": int(payment_date[:4]) if payment_date else None,
            "amount_per_share": float(amount),
            "source": "BRAPI_FREE",
            "source_confidence": "medium",
        })
    return {
        "current_price": current_price,
        "market_cap": market_cap,
        "currency": currency,
        "price_history": [],
        "dividend_history": [event["amount_per_share"] for event in dividend_events],
        "dividend_events": dividend_events,
        "source_status": SOURCE_AUXILIARY,
        "source_url": BRAPI_URL.format(symbol=item.get("symbol") or ""),
    }


def collect_market_data(ticker):
    symbol = ticker.upper()
    brapi_url = BRAPI_URL.format(symbol=symbol)
    try:
        payload = json.loads(fetch_url(brapi_url).decode("utf-8"))
        parsed = _parse_events_from_brapi(payload)
        if parsed:
            return parsed
    except Exception as exc:
        brapi_error = str(exc)
    else:
        brapi_error = "BRAPI sem payload util"
    if not data_source_flag("allow_yahoo_fallback", False):
        return {
            "current_price": None,
            "price_history": [],
            "dividend_history": [],
            "dividend_events": [],
            "source_status": SOURCE_NOT_FOUND,
            "error": f"BRAPI indisponivel e nenhuma fonte auxiliar opcional foi habilitada: {brapi_error}",
            "source_policy": "official_or_free_auxiliary_only",
        }
    url = YAHOO_URL.format(symbol=symbol)
    try:
        payload = json.loads(fetch_url(url).decode("utf-8"))
        result = payload["chart"]["result"][0]
        meta = result.get("meta", {})
        quote = result["indicators"]["quote"][0]
        closes = [value for value in quote.get("close", []) if value is not None]
        dividends = result.get("events", {}).get("dividends", {})
        dividend_events = []
        for event in dividends.values():
            amount = event.get("amount")
            timestamp = event.get("date")
            if amount is None:
                continue
            event_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat() if timestamp else None
            dividend_events.append({
                "date": event_date,
                "year": int(event_date[:4]) if event_date else None,
                "amount_per_share": float(amount),
                "source": "YAHOO",
                "source_confidence": "low",
            })
        dividend_events.sort(key=lambda item: item.get("date") or "")
        return {
            "current_price": closes[-1] if closes else None,
            "market_cap": meta.get("marketCap"),
            "currency": meta.get("currency"),
            "price_history": closes,
            "dividend_history": [event["amount_per_share"] for event in dividend_events],
            "dividend_events": dividend_events,
            "source_status": SOURCE_AUXILIARY,
            "source_url": url,
            "source_policy": "yahoo_fallback_enabled",
        }
    except Exception as exc:
        return {"current_price": None, "price_history": [], "dividend_history": [], "dividend_events": [], "source_status": SOURCE_NOT_FOUND, "error": str(exc)}


def main():
    if len(sys.argv) != 2:
        print("usage: market_data_collector.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_market_data(sys.argv[1])))


if __name__ == "__main__":
    main()
