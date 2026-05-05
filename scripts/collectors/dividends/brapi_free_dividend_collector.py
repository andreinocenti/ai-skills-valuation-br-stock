#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from typing import Any

from collectors.dividends.dividend_models import build_dividend_event
from config_loader import data_source_flag
from valuation_core import fetch_url


def collect_brapi_free_dividends(ticker: str) -> dict[str, Any]:
    if not data_source_flag("allow_brapi_free_fallback", True):
        return {"ticker": ticker.upper(), "events": [], "warnings": ["BRAPI fallback desabilitado por configuracao."]}
    token = os.getenv("BRAPI_TOKEN")
    url = f"https://brapi.dev/api/quote/{ticker.upper()}?modules=dividends"
    if token:
        url += f"&token={token}"
    try:
        payload = json.loads(fetch_url(url).decode("utf-8"))
        results = payload.get("results") or []
        history = (((results[0] if results else {}).get("dividendsData") or {}).get("cashDividends") or [])
    except Exception as exc:
        return {"ticker": ticker.upper(), "events": [], "warnings": [f"BRAPI indisponivel: {exc}"]}
    events = []
    for item in history:
        amount = item.get("rate")
        if amount in (None, 0, 0.0):
            continue
        events.append(build_dividend_event(
            ticker=ticker.upper(),
            type="dividend",
            amount_per_share=float(amount),
            payment_date=item.get("paymentDate"),
            ex_date=item.get("approvedOn"),
            share_class="ALL",
            is_recurring=True,
            source="BRAPI_FREE",
            source_url=url,
            source_document_type="API quote dividends",
            source_confidence="medium",
            raw_evidence=str(item),
            parser_confidence="medium",
        ))
    return {"ticker": ticker.upper(), "events": events, "warnings": []}
