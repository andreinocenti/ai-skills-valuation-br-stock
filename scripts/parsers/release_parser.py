#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import detect_non_recurring_from_text, write_json


def parse_release(text):
    guidance = re.findall(r"guidance[^.\n]*[.\n]", text, flags=re.IGNORECASE)
    risks = re.findall(r"risco[^.\n]*[.\n]", text, flags=re.IGNORECASE)
    return {
        "guidance_mentions": guidance,
        "risk_mentions": risks,
        "non_recurring_items": detect_non_recurring_from_text(text),
    }


def main():
    if len(sys.argv) != 2:
        print("usage: release_parser.py <text-file>", file=sys.stderr)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    print(write_json(parse_release(text)))


if __name__ == "__main__":
    main()
