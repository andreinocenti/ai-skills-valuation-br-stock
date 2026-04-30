#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import load_json, write_json


def main():
    if len(sys.argv) not in (2, 3):
        print("usage: inflation_adjuster.py <input.json> [factor]", file=sys.stderr)
        sys.exit(1)
    data = load_json(sys.argv[1])
    factor = float(sys.argv[2]) if len(sys.argv) == 3 else 1.0
    for row in data.get("financials", []):
        for key in ("revenue", "ebitda", "net_income", "equity", "operating_cash_flow", "capex", "free_cash_flow", "dividends_paid"):
            if key in row:
                row[key] *= factor
    print(write_json(data))


if __name__ == "__main__":
    main()
