#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import write_json


POSITIVE = ["crescimento", "recorde", "melhora", "expansao", "reduzimos", "forte"]
NEGATIVE = ["queda", "pressao", "risco", "deterioracao", "aumento da divida", "perda"]


def analyze_tone(text):
    lower = text.lower()
    positive = sum(lower.count(word) for word in POSITIVE)
    negative = sum(lower.count(word) for word in NEGATIVE)
    tone = "neutral"
    if positive > negative * 1.5:
        tone = "positive"
    elif negative > positive * 1.5:
        tone = "negative"
    return {"tone": tone, "positive_terms": positive, "negative_terms": negative}


def main():
    if len(sys.argv) != 2:
        print("usage: management_tone_analyzer.py <text-file>", file=sys.stderr)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    print(write_json(analyze_tone(text)))


if __name__ == "__main__":
    main()
