#!/usr/bin/env python3
import sys
from pathlib import Path

from valuation_core import detect_non_recurring_from_text, write_json


def main():
    if len(sys.argv) != 2:
        print("usage: detect_non_recurring_items.py <text-file>", file=sys.stderr)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    print(write_json({"non_recurring_items": detect_non_recurring_from_text(text)}))


if __name__ == "__main__":
    main()
