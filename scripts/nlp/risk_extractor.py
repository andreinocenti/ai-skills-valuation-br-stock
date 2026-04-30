#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import write_json


RISK_TERMS = ["regulatorio", "cambial", "juros", "credito", "concessao", "commodity", "politico", "fiscal", "governanca", "concorrencia", "tecnologico", "alavancagem", "liquidez", "margem"]


def extract_risks(text):
    lower = text.lower()
    risks = []
    for term in RISK_TERMS:
        if term in lower:
            matches = re.findall(rf"[^.\n]*{term}[^.\n]*", lower)
            risks.append({"risk": term, "mentions": matches[:5], "probability": "medium", "impact": "medium"})
    return risks


def main():
    if len(sys.argv) != 2:
        print("usage: risk_extractor.py <text-file>", file=sys.stderr)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    print(write_json({"risks": extract_risks(text)}))


if __name__ == "__main__":
    main()
