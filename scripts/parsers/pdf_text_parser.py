#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_text_from_bytes(raw: bytes) -> str:
    # Heuristica sem dependencias externas:
    # 1. tenta texto simples
    # 2. tenta strings literais de PDF entre parenteses
    # 3. fallback para sequencias ASCII legiveis
    try:
        text = raw.decode("utf-8")
        if text.strip():
            return text
    except UnicodeDecodeError:
        text = raw.decode("latin1", errors="replace")
        if text.strip():
            return text
    decoded = raw.decode("latin1", errors="replace")
    literal_strings = re.findall(r"\(([^()]{2,400})\)", decoded)
    if literal_strings:
        return "\n".join(item.replace("\\n", "\n").replace("\\r", "\n") for item in literal_strings)
    ascii_runs = re.findall(r"[A-Za-z0-9$%/.,:;() \-]{8,}", decoded)
    return "\n".join(item.strip() for item in ascii_runs if item.strip())


def extract_text(path):
    raw = Path(path).read_bytes()
    return extract_text_from_bytes(raw)


def main():
    if len(sys.argv) != 2:
        print("usage: pdf_text_parser.py <file>", file=sys.stderr)
        sys.exit(1)
    print(extract_text(sys.argv[1]))


if __name__ == "__main__":
    main()
