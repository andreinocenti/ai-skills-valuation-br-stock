#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import parse_cvm_dfp_zip, read_csv_from_zip, write_json


def parse_cvm_zip(zip_path):
    rows = read_csv_from_zip(Path(zip_path))
    return {"rows": rows, "row_count": len(rows)}


def main():
    if len(sys.argv) not in (2, 3):
        print("usage: cvm_statement_parser.py <cvm-zip> [cvm-code]", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) == 3:
        print(write_json({"financials": parse_cvm_dfp_zip(sys.argv[1], sys.argv[2])}))
    else:
        print(write_json(parse_cvm_zip(sys.argv[1])))


if __name__ == "__main__":
    main()
