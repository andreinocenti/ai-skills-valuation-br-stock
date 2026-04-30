#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import parse_cvm_dfp_zip, write_json


def parse_itr_zip(zip_path, cvm_code):
    rows = parse_cvm_dfp_zip(zip_path, cvm_code)
    for row in rows:
        row["period_type"] = "ITR"
    return rows


def main():
    if len(sys.argv) != 3:
        print("usage: cvm_itr_parser.py <itr-zip> <cvm-code>", file=sys.stderr)
        sys.exit(1)
    print(write_json({"financials": parse_itr_zip(sys.argv[1], sys.argv[2])}))


if __name__ == "__main__":
    main()
