#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import load_json, normalize_financials, write_json


def main():
    if len(sys.argv) != 2:
        print("usage: dividend_normalizer.py <input.json>", file=sys.stderr)
        sys.exit(1)
    data = normalize_financials(load_json(sys.argv[1]))
    print(write_json([{"year": row["year"], "reported": row["dividends_reported"], "recurring": row["dividends_recurring"]} for row in data["financials"]]))


if __name__ == "__main__":
    main()
