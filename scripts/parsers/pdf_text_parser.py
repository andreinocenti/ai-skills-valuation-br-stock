#!/usr/bin/env python3
import sys
from pathlib import Path


def extract_text(path):
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin1", errors="replace")


def main():
    if len(sys.argv) != 2:
        print("usage: pdf_text_parser.py <file>", file=sys.stderr)
        sys.exit(1)
    print(extract_text(sys.argv[1]))


if __name__ == "__main__":
    main()
