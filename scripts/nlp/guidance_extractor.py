#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import write_json


def extract_guidance(text):
    matches = re.findall(r"[^.\n]*(guidance|projecao|estimativa|meta|capex|ebitda)[^.\n]*", text, flags=re.IGNORECASE)
    return [{"text": match if isinstance(match, str) else " ".join(match), "confidence": "medium"} for match in matches]


def main():
    if len(sys.argv) != 2:
        print("usage: guidance_extractor.py <text-file>", file=sys.stderr)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    print(write_json({"guidance": extract_guidance(text)}))


if __name__ == "__main__":
    main()
