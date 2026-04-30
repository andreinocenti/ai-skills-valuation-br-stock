#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import calculate_ttm, write_json


def main():
    if len(sys.argv) != 2:
        print("usage: build_ttm.py <valuation-input.json>", file=sys.stderr)
        sys.exit(1)
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(write_json({"ttm": calculate_ttm(data.get("financials", []), data.get("itr_financials", []))}))


if __name__ == "__main__":
    main()
