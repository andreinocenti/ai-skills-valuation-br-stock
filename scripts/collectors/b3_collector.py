#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.company_resolver import resolve_company
from valuation_core import write_json


def collect_b3_profile(ticker):
    profile = resolve_company(ticker)
    profile["source_note"] = "Resolver local; enriquecer com B3 quando endpoint ou arquivo oficial estiver disponivel."
    return profile


def main():
    if len(sys.argv) != 2:
        print("usage: b3_collector.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_b3_profile(sys.argv[1])))


if __name__ == "__main__":
    main()
