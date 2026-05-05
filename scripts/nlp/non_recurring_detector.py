#!/usr/bin/env python3
from __future__ import annotations

from valuation_core import detect_non_recurring_from_text


def extract_non_recurring_items(text: str) -> list[dict[str, object]]:
    return detect_non_recurring_from_text(text)
