#!/usr/bin/env python3
from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from urllib.parse import quote, urljoin
from typing import Any

from collectors.dividends.cvm_ipe_dividend_collector import parse_cvm_dividend_events
from parsers.pdf_table_parser import parse_tables_from_text
from parsers.pdf_text_parser import extract_text_from_bytes
from valuation_core import fetch_url


B3_SEARCH_URL = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/search?language=pt-br"
B3_COMPANY_URL = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/main/{slug}/overview?language=pt-br"


def _html_to_text(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html or ""))).strip()


def _fetch_b3_document(url: str) -> tuple[str, list[dict[str, Any]]]:
    content = fetch_url(url)
    if url.lower().endswith(".pdf"):
        text = extract_text_from_bytes(content)
    else:
        text = _html_to_text(content.decode("utf-8", errors="replace"))
    return text, parse_tables_from_text(text)


def discover_b3_documents(
    ticker: str,
    company_profile: dict[str, Any],
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    del cache_dir
    ticker = ticker.upper()
    slug_candidates = [quote(ticker.lower())]
    if company_profile.get("name"):
        slug_candidates.append(quote(str(company_profile["name"]).lower().replace(" ", "-")))
    documents = []
    warnings = []
    source_urls = [B3_SEARCH_URL]
    for slug in slug_candidates:
        url = B3_COMPANY_URL.format(slug=slug)
        source_urls.append(url)
        try:
            html = fetch_url(url).decode("utf-8", errors="replace")
        except Exception as exc:
            warnings.append(f"Falha ao consultar B3 em {url}: {exc}")
            continue
        links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)))
        candidates = []
        for link in links:
            if any(term in link.lower() for term in ("provento", "dividend", "jscp", "jcp", ".pdf")):
                candidates.append(urljoin(url, link))
        if not candidates and ("provento" in html.lower() or "dividend" in html.lower() or "jcp" in html.lower()):
            candidates.append(url)
        for candidate_url in candidates:
            try:
                text, tables = _fetch_b3_document(candidate_url)
            except Exception as exc:
                warnings.append(f"Falha ao baixar documento B3 {candidate_url}: {exc}")
                continue
            if "provento" not in text.lower() and "dividend" not in text.lower() and "jcp" not in text.lower():
                continue
            documents.append({
                "id": f"{ticker.lower()}-b3-{len(documents) + 1}",
                "url": candidate_url,
                "text": text,
                "tables": tables,
                "document_type": "Formulário de Provento em Dinheiro Aprovado",
            })
        if documents:
            break
    return {"documents": documents, "warnings": warnings, "source_urls": source_urls}


def collect_b3_cash_dividends(ticker: str, company_profile: dict[str, Any], documents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    events = []
    for document in documents or []:
        for event in parse_cvm_dividend_events(document.get("text") or "", {
            "ticker": ticker.upper(),
            "company_cvm_code": company_profile.get("cvm_code"),
            "share_class": company_profile.get("share_class", "ALL"),
            "source_url": document.get("url"),
            "source_document_id": document.get("id"),
            "source_document_type": "Formulário de Provento em Dinheiro Aprovado",
            "fiscal_year": document.get("fiscal_year"),
        }):
            event["source"] = "B3"
            event["source_confidence"] = "high" if event.get("raw_evidence") else "medium_high"
            events.append(event)
    return {"ticker": ticker.upper(), "events": events, "warnings": []}
