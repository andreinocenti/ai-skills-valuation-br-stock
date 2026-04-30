#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import write_json


def parse_tables(path):
    return {
        "tables": [],
        "warning": "Extracao real de tabelas PDF requer dependencia externa como tabula, camelot ou pdfplumber.",
        "source_file": str(path),
    }


def main():
    if len(sys.argv) != 2:
        print("usage: pdf_table_parser.py <pdf>", file=sys.stderr)
        sys.exit(1)
    print(write_json(parse_tables(sys.argv[1])))


if __name__ == "__main__":
    main()
