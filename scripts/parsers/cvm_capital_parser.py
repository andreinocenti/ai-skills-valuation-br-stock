#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import parse_cvm_dfp_zip, write_json


def parse_capital_from_zip(zip_path, cvm_code):
    financials = parse_cvm_dfp_zip(zip_path, cvm_code)
    rows = []
    for row in financials:
        rows.append({
            "year": row.get("year"),
            "shares_outstanding": row.get("shares_outstanding"),
            "basis": row.get("basis"),
        })
    return rows


def main():
    if len(sys.argv) != 3:
        print("usage: cvm_capital_parser.py <cvm-zip> <cvm-code>", file=sys.stderr)
        sys.exit(1)
    print(write_json({"capital": parse_capital_from_zip(sys.argv[1], sys.argv[2])}))


if __name__ == "__main__":
    main()
