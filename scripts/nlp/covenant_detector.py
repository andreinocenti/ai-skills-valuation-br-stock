#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import write_json


def detect_covenants(text):
    matches = re.findall(r"[^.\n]*(covenant|indice financeiro|divida liquida|ebitda|restricao)[^.\n]*", text, flags=re.IGNORECASE)
    return [{"text": item if isinstance(item, str) else " ".join(item), "confidence": "medium"} for item in matches]


def main():
    if len(sys.argv) != 2:
        print("usage: covenant_detector.py <text-file>", file=sys.stderr)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    print(write_json({"covenants": detect_covenants(text)}))


if __name__ == "__main__":
    main()
