#!/usr/bin/env python3
from __future__ import annotations

import re

from collectors.dividends.dividend_models import build_dividend_event
from config_loader import data_source_flag


def scrape_aggregator_dividends(ticker: str, page_text: str = "", source_url: str | None = None) -> dict[str, object]:
    if not data_source_flag("allow_aggregator_scraping", True):
        return {"ticker": ticker.upper(), "events": [], "warnings": ["Scraping de agregadores desabilitado por configuracao."]}
    values = re.findall(r"R\$\s*([0-9]+(?:[.,][0-9]{1,6})?)", page_text, flags=re.IGNORECASE)
    events = [
        build_dividend_event(
            ticker=ticker.upper(),
            type="dividend",
            amount_per_share=float(value.replace(".", "").replace(",", ".")),
            share_class="ALL",
            is_recurring=True,
            source="AGGREGATOR",
            source_url=source_url,
            source_document_type="Aggregator page",
            source_confidence="low",
            raw_evidence=value,
            parser_confidence="low",
            warnings=["Fonte agregadora usada apenas como fallback."],
        )
        for value in values
    ]
    return {"ticker": ticker.upper(), "events": events, "warnings": []}
