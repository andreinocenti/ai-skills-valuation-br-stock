#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


SOURCE_PRIORITY = {
    "CVM_IPE": 1,
    "B3": 2,
    "RI": 3,
    "BRAPI_FREE": 4,
    "AGGREGATOR": 5,
    "USER_INPUT": 6,
    "YAHOO": 7,
    "UNKNOWN": 9,
}


def deterministic_event_id(event: dict[str, Any]) -> str:
    base = "|".join([
        str(event.get("ticker") or ""),
        str(event.get("type") or ""),
        str(event.get("share_class") or ""),
        str(event.get("approval_date") or ""),
        str(event.get("ex_date") or ""),
        str(event.get("payment_date") or ""),
        f"{float(event.get('gross_amount_per_share') or event.get('amount_per_share') or 0.0):.6f}",
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


def build_dividend_event(**kwargs: Any) -> dict[str, Any]:
    event = {
        "ticker": kwargs.get("ticker"),
        "company_cvm_code": kwargs.get("company_cvm_code"),
        "event_id": None,
        "type": kwargs.get("type", "unknown"),
        "amount_per_share": kwargs.get("amount_per_share"),
        "gross_amount_per_share": kwargs.get("gross_amount_per_share", kwargs.get("amount_per_share")),
        "net_amount_per_share": kwargs.get("net_amount_per_share"),
        "declared_date": kwargs.get("declared_date"),
        "approval_date": kwargs.get("approval_date"),
        "ex_date": kwargs.get("ex_date"),
        "record_date": kwargs.get("record_date"),
        "payment_date": kwargs.get("payment_date"),
        "fiscal_year": kwargs.get("fiscal_year"),
        "reference_period": kwargs.get("reference_period"),
        "share_class": kwargs.get("share_class", "unknown"),
        "is_recurring": kwargs.get("is_recurring", False),
        "is_extraordinary": kwargs.get("is_extraordinary", False),
        "extraordinary_reason": kwargs.get("extraordinary_reason"),
        "source": kwargs.get("source", "UNKNOWN"),
        "source_url": kwargs.get("source_url"),
        "source_document_type": kwargs.get("source_document_type"),
        "source_document_id": kwargs.get("source_document_id"),
        "source_confidence": kwargs.get("source_confidence", "low"),
        "raw_evidence": kwargs.get("raw_evidence"),
        "parser_confidence": kwargs.get("parser_confidence", "low"),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).isoformat()),
        "warnings": list(kwargs.get("warnings") or []),
    }
    event["event_id"] = kwargs.get("event_id") or deterministic_event_id(event)
    return event
