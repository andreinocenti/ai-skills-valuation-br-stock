#!/usr/bin/env python3
from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from typing import Any

from collectors.dividends.cvm_ipe_dividend_collector import parse_cvm_dividend_events
from collectors.ri_document_collector import collect_ri_documents
from parsers.pdf_table_parser import parse_tables_from_text
from parsers.pdf_text_parser import extract_text_from_bytes
from valuation_core import fetch_url


def parse_ri_dividend_table(html_text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    cleaned = unescape(re.sub(r"<[^>]+>", " ", html_text))
    events = parse_cvm_dividend_events(cleaned, metadata)
    for event in events:
        event["source"] = "RI"
        event["source_confidence"] = "high"
        event["parser_confidence"] = "high"
    return events


def _load_document_content(document: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    html = document.get("html")
    text = document.get("text")
    url = document.get("url") or ""
    if html:
        parsed_text = unescape(re.sub(r"<[^>]+>", " ", html))
        return parsed_text, parse_tables_from_text(parsed_text)
    if text:
        return text, parse_tables_from_text(text)
    if url:
        content = fetch_url(url)
        if url.lower().endswith(".pdf"):
            parsed_text = extract_text_from_bytes(content)
        else:
            parsed_text = unescape(re.sub(r"<[^>]+>", " ", content.decode("utf-8", errors="replace")))
        return parsed_text, parse_tables_from_text(parsed_text)
    return "", []


def collect_ri_dividends(ticker: str, company_profile: dict[str, Any], documents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    events = []
    warnings = []
    for raw_document in documents or []:
        document = raw_document if isinstance(raw_document, dict) else {"url": str(raw_document), "text": ""}
        metadata = {
            "ticker": ticker.upper(),
            "company_cvm_code": company_profile.get("cvm_code"),
            "share_class": company_profile.get("share_class", "ALL"),
            "source_url": document.get("url"),
            "source_document_id": document.get("id"),
            "source_document_type": document.get("document_type", "RI"),
            "fiscal_year": document.get("fiscal_year"),
        }
        content, tables = _load_document_content(document)
        if tables:
            document["tables"] = tables
        if not content:
            warnings.append(f"Documento RI sem conteudo parseavel: {document.get('url') or document.get('id')}")
        events.extend(parse_ri_dividend_table(content, metadata))
    return {"ticker": ticker.upper(), "events": events, "warnings": warnings}


def discover_ri_dividend_documents(
    ticker: str,
    company_profile: dict[str, Any],
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    del company_profile
    del cache_dir
    result = collect_ri_documents(ticker)
    return {
        "documents": result.get("documents", []),
        "warnings": [result.get("error")] if result.get("error") else [],
        "source_urls": [result.get("ri_url")] if result.get("ri_url") else [],
    }
