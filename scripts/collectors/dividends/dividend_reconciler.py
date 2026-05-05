#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
import hashlib
from typing import Any

from collectors.dividends.dividend_models import SOURCE_PRIORITY


def _parse_date(value: Any) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        year, month, day = value[:10].split("-")
        return date(int(year), int(month), int(day))
    except Exception:
        return None


def _canonical_type(value: Any) -> str:
    raw = str(value or "unknown").lower()
    if raw in ("dividendo", "dividend"):
        return "dividend"
    if raw == "jcp":
        return "jcp"
    if raw in ("capital_reduction", "reduction_of_capital"):
        return "capital_reduction"
    if raw in ("restitution", "capital_restitution"):
        return "restitution"
    if raw == "bonus":
        return "bonus"
    return raw


def _event_key(event: dict[str, Any]) -> tuple[Any, ...]:
    amount = float(event.get("gross_amount_per_share") or event.get("amount_per_share") or 0.0)
    rounded_amount = round(amount, 2)
    date = event.get("ex_date") or event.get("payment_date") or event.get("approval_date") or event.get("record_date")
    return (
        event.get("ticker"),
        event.get("share_class"),
        _canonical_type(event.get("type")),
        rounded_amount,
        date,
    )


def _reconciled_event_id(event: dict[str, Any]) -> str:
    raw = "|".join(str(item) for item in _event_key(event))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _dates_close(left: dict[str, Any], right: dict[str, Any], tolerance_days: int = 7) -> bool:
    left_dates = [_parse_date(left.get(field)) for field in ("approval_date", "ex_date", "record_date", "payment_date")]
    right_dates = [_parse_date(right.get(field)) for field in ("approval_date", "ex_date", "record_date", "payment_date")]
    left_dates = [item for item in left_dates if item is not None]
    right_dates = [item for item in right_dates if item is not None]
    if not left_dates or not right_dates:
        return True
    return min(abs((l - r).days) for l in left_dates for r in right_dates) <= tolerance_days


def _amounts_close(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_amount = float(left.get("gross_amount_per_share") or left.get("amount_per_share") or 0.0)
    right_amount = float(right.get("gross_amount_per_share") or right.get("amount_per_share") or 0.0)
    if left_amount <= 0 or right_amount <= 0:
        return left_amount == right_amount
    absolute_delta = abs(left_amount - right_amount)
    relative_delta = absolute_delta / max(left_amount, right_amount)
    return absolute_delta <= 0.005 or relative_delta <= 0.005


def _events_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("ticker") != right.get("ticker"):
        return False
    if left.get("share_class") != right.get("share_class"):
        return False
    if _canonical_type(left.get("type")) != _canonical_type(right.get("type")):
        return False
    return _amounts_close(left, right) and _dates_close(left, right)


def _merge_events(primary: dict[str, Any], candidate: dict[str, Any], divergences: list[dict[str, Any]]) -> dict[str, Any]:
    merged = dict(primary)
    for field in (
        "amount_per_share",
        "gross_amount_per_share",
        "net_amount_per_share",
        "approval_date",
        "ex_date",
        "record_date",
        "payment_date",
        "raw_evidence",
    ):
        selected = merged.get(field)
        incoming = candidate.get(field)
        if selected in (None, "", []) and incoming not in (None, "", []):
            merged[field] = incoming
        elif incoming not in (None, "", []) and selected not in (None, "", []) and incoming != selected:
            divergences.append({
                "event_key": merged.get("reconciled_event_id") or merged.get("event_id"),
                "field": field,
                "values": {merged.get("source"): selected, candidate.get("source"): incoming},
                "selected": merged.get("source"),
                "selection_reason": "higher_priority_source",
            })
    merged["warnings"] = list(dict.fromkeys(list(merged.get("warnings") or []) + list(candidate.get("warnings") or [])))
    return merged


def reconcile_dividend_events(*event_groups: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = []
    for group in event_groups:
        ordered.extend(group or [])
    ordered.sort(key=lambda item: (SOURCE_PRIORITY.get(item.get("source", "UNKNOWN"), 9), item.get("payment_date") or "", item.get("event_id") or ""))
    merged_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    divergences: list[dict[str, Any]] = []
    primary_sources_used: list[str] = []
    fallback_sources_checked: list[str] = []
    for event in ordered:
        source = event.get("source")
        if source in ("CVM_IPE", "B3", "RI") and source not in primary_sources_used:
            primary_sources_used.append(source)
        if source in ("BRAPI_FREE", "AGGREGATOR") and source not in fallback_sources_checked:
            fallback_sources_checked.append(source)
        key = None
        current = None
        for candidate_key, candidate_event in merged_by_key.items():
            if _events_match(candidate_event, event):
                key = candidate_key
                current = candidate_event
                break
        if current is None:
            seeded = dict(event)
            seeded["reconciled_event_id"] = _reconciled_event_id(seeded)
            merged_by_key[_event_key(event)] = seeded
            continue
        merged_by_key[key] = _merge_events(current, event, divergences)
    events = sorted(
        merged_by_key.values(),
        key=lambda item: (
            item.get("payment_date") or item.get("ex_date") or item.get("approval_date") or "9999-12-31",
            SOURCE_PRIORITY.get(item.get("source", "UNKNOWN"), 9),
            item.get("event_id") or "",
        ),
    )
    return {
        "events": events,
        "reconciliation": {
            "primary_sources_used": primary_sources_used,
            "fallback_sources_checked": fallback_sources_checked,
            "divergences": divergences,
            "warnings": [],
            "matching_policy": {
                "date_tolerance_days": 7,
                "amount_tolerance_absolute_brl": 0.005,
                "amount_tolerance_relative": 0.005,
            },
        },
    }
