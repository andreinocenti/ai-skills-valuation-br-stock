#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parsers.pdf_text_parser import extract_text, extract_text_from_bytes
from valuation_core import write_json


def parse_tables_from_text(text: str):
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    rows = []
    for line in lines:
        if ";" in line:
            cells = [cell.strip() for cell in line.split(";") if cell.strip()]
        elif "|" in line:
            cells = [cell.strip() for cell in line.split("|") if cell.strip()]
        else:
            cells = re.split(r"\s{2,}", line)
            cells = [cell.strip() for cell in cells if cell.strip()]
        if len(cells) >= 2:
            rows.append(cells)
    tables = []
    if rows:
        tables.append({"rows": rows})
    return tables


def parse_tables(path):
    text = extract_text(path)
    return {
        "tables": parse_tables_from_text(text),
        "warning": None if parse_tables_from_text(text) else "Nenhuma tabela heuristica encontrada no PDF.",
        "source_file": str(path),
    }


def main():
    if len(sys.argv) != 2:
        print("usage: pdf_table_parser.py <pdf>", file=sys.stderr)
        sys.exit(1)
    print(write_json(parse_tables(sys.argv[1])))


if __name__ == "__main__":
    main()
