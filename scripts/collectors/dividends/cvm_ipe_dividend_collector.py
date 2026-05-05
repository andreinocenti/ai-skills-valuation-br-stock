#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import re
import zipfile
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from collectors.dividends.dividend_models import build_dividend_event
from parsers.pdf_table_parser import parse_tables_from_text
from parsers.pdf_text_parser import extract_text_from_bytes
from valuation_core import fetch_url


DIVIDEND_TERMS = (
    "dividendo",
    "dividendos",
    "juros sobre capital proprio",
    "juros sobre o capital proprio",
    "jcp",
    "proventos",
    "remuneracao aos acionistas",
    "data ex",
    "data com",
    "pagamento",
)

DOCUMENT_TYPE_TERMS = (
    "aviso aos acionistas",
    "comunicado ao mercado",
    "fato relevante",
    "politica de dividendos",
    "assembleia",
)

IPE_ZIP_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{year}.zip"
IPE_BASE_URL = "https://dados.cvm.gov.br/"


def _parse_date(text: str, label: str) -> str | None:
    match = re.search(rf"{label}[^\d]*(\d{{2}}/\d{{2}}/\d{{4}})", text, flags=re.IGNORECASE)
    if not match:
        return None
    dd, mm, yyyy = match.group(1).split("/")
    return f"{yyyy}-{mm}-{dd}"


def _infer_type(text: str) -> tuple[str, bool, str | None]:
    lower = text.lower()
    if "reducao de capital" in lower or "restitu" in lower:
        return "capital_reduction", False, "evento de capital"
    if "extraordin" in lower or "especial" in lower:
        return "dividend", False, "evento explicitamente extraordinario"
    if "jcp" in lower or "juros sobre capital" in lower:
        return "jcp", True, None
    if "dividend" in lower:
        return "dividend", True, None
    return "unknown", False, None


def parse_cvm_dividend_events(text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    lower = text.lower()
    if not any(term in lower for term in DIVIDEND_TERMS):
        return []
    values = re.findall(r"r\$\s*([0-9]+(?:[.,][0-9]{1,6})?)", text, flags=re.IGNORECASE)
    if not values:
        return []
    event_type, recurring, extraordinary_reason = _infer_type(text)
    events = []
    for raw in values:
        amount = float(raw.replace(".", "").replace(",", "."))
        if amount <= 0:
            continue
        evidence_match = re.search(rf".{{0,80}}{re.escape(raw)}.{{0,120}}", text, flags=re.IGNORECASE | re.DOTALL)
        evidence = evidence_match.group(0).strip() if evidence_match else text[:160].strip()
        events.append(build_dividend_event(
            ticker=metadata.get("ticker"),
            company_cvm_code=metadata.get("company_cvm_code"),
            type=event_type,
            amount_per_share=amount,
            approval_date=_parse_date(text, "aprov"),
            ex_date=_parse_date(text, "data ex"),
            record_date=_parse_date(text, "data com"),
            payment_date=_parse_date(text, "pagamento"),
            fiscal_year=metadata.get("fiscal_year"),
            reference_period=str(metadata.get("fiscal_year")) if metadata.get("fiscal_year") else None,
            share_class=metadata.get("share_class", "ALL"),
            is_recurring=recurring,
            is_extraordinary=not recurring,
            extraordinary_reason=extraordinary_reason,
            source="CVM_IPE",
            source_url=metadata.get("source_url"),
            source_document_type=metadata.get("source_document_type", "Aviso aos Acionistas"),
            source_document_id=metadata.get("source_document_id"),
            source_confidence="high",
            raw_evidence=evidence,
            parser_confidence="high" if "por ac" in lower or "por ação" in lower else "medium",
        ))
    return events


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _document_is_relevant(row: dict[str, Any], cvm_code: str | None) -> bool:
    if cvm_code:
        row_code = _normalize_text(row.get("CD_CVM") or row.get("cd_cvm"))
        if row_code and row_code != str(cvm_code):
            return False
    combined = " ".join(_normalize_text(row.get(key)) for key in row.keys()).lower()
    return any(term in combined for term in DIVIDEND_TERMS) and any(term in combined for term in DOCUMENT_TYPE_TERMS)


def _row_to_document(row: dict[str, Any], ticker: str, share_class: str, year: int) -> dict[str, Any]:
    text_parts = []
    for key, value in row.items():
        value = _normalize_text(value)
        if value:
            text_parts.append(f"{key}: {value}")
    url = row.get("LINK_DOC") or row.get("link_doc") or row.get("LINK") or row.get("link")
    return {
        "id": row.get("ID") or row.get("SEQ_DOC") or row.get("PROTOCOLO") or f"{ticker.lower()}-ipe-{year}",
        "url": url,
        "text": "\n".join(text_parts),
        "document_type": row.get("CATEGORIA") or row.get("categoria") or row.get("ASSUNTO") or "Aviso aos Acionistas",
        "fiscal_year": year,
        "share_class": share_class,
    }


def _html_to_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def _fetch_document_payload(url: str) -> tuple[str, list[dict[str, Any]], str | None]:
    full_url = urljoin(IPE_BASE_URL, url)
    content = fetch_url(full_url)
    if full_url.lower().endswith(".pdf"):
        text = extract_text_from_bytes(content)
        tables = parse_tables_from_text(text)
    else:
        text = _html_to_text(content.decode("utf-8", errors="replace"))
        tables = parse_tables_from_text(text)
    return text, tables, full_url


def discover_cvm_ipe_documents(
    ticker: str,
    company_profile: dict[str, Any],
    years: list[int] | None,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    cvm_code = company_profile.get("cvm_code")
    if not cvm_code:
        return {"documents": [], "warnings": ["Codigo CVM ausente; coleta CVM IPE ignorada."], "source_urls": []}
    documents = []
    warnings = []
    source_urls = []
    for year in years or []:
        url = IPE_ZIP_URL.format(year=year)
        source_urls.append(url)
        try:
            content = fetch_url(url)
        except Exception as exc:
            warnings.append(f"Falha ao baixar IPE {year}: {exc}")
            continue
        if cache_dir:
            base = Path(cache_dir).expanduser() / "cvm_ipe" / "raw"
            base.mkdir(parents=True, exist_ok=True)
            (base / f"{ticker.lower()}-{year}.zip").write_bytes(content)
        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
        except Exception as exc:
            warnings.append(f"ZIP IPE invalido para {year}: {exc}")
            continue
        with archive:
            for name in archive.namelist():
                if not name.lower().endswith(".csv"):
                    continue
                try:
                    rows = [dict(row) for row in csv.DictReader(archive.read(name).decode("latin1", errors="replace").splitlines(), delimiter=";")]
                except Exception:
                    continue
                for row in rows:
                    if _document_is_relevant(row, str(cvm_code)):
                        document = _row_to_document(row, ticker.upper(), company_profile.get("share_class", "ALL"), year)
                        if document.get("url"):
                            try:
                                fetched_text, tables, full_url = _fetch_document_payload(document["url"])
                                document["url"] = full_url
                                document["text"] = fetched_text or document["text"]
                                if tables:
                                    document["tables"] = tables
                            except Exception as exc:
                                warnings.append(f"Falha ao baixar documento CVM {document.get('url')}: {exc}")
                        documents.append(document)
    return {"documents": documents, "warnings": warnings, "source_urls": source_urls}


def collect_cvm_ipe_dividends(ticker: str, company_profile: dict[str, Any], documents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    events = []
    warnings = []
    for document in documents or []:
        text = document.get("text") or ""
        parsed = parse_cvm_dividend_events(text, {
            "ticker": ticker.upper(),
            "company_cvm_code": company_profile.get("cvm_code"),
            "share_class": company_profile.get("share_class", "ALL"),
            "source_url": document.get("url"),
            "source_document_id": document.get("id"),
            "source_document_type": document.get("document_type", "Aviso aos Acionistas"),
            "fiscal_year": document.get("fiscal_year"),
        })
        if not parsed and any(term in text.lower() for term in DIVIDEND_TERMS):
            warnings.append(f"Documento CVM menciona proventos sem valor extraivel: {document.get('id') or document.get('url')}")
        events.extend(parsed)
    return {"ticker": ticker.upper(), "events": events, "warnings": warnings}
