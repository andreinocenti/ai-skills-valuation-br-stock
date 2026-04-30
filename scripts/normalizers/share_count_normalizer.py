#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import load_json, write_json


def main():
    if len(sys.argv) != 2:
        print("usage: share_count_normalizer.py <input.json>", file=sys.stderr)
        sys.exit(1)
    data = load_json(sys.argv[1])
    counts = [{"year": row["year"], "shares_outstanding": row["shares_outstanding"]} for row in data.get("financials", [])]
    print(write_json({"share_counts": counts}))


if __name__ == "__main__":
    main()
