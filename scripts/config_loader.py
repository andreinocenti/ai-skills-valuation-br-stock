#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "config" / "defaults.json"


def load_defaults() -> dict[str, Any]:
    return json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))


def data_source_flag(name: str, default: Any = None) -> Any:
    return load_defaults().get("data_sources", {}).get(name, default)


def valuation_default(name: str, default: Any = None) -> Any:
    return load_defaults().get("valuation", {}).get(name, default)
