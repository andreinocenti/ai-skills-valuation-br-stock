#!/usr/bin/env python3
import sys
from pathlib import Path

from valuation_core import calculate_indicators, load_json, normalize_financials, write_json


def main():
    if len(sys.argv) != 2:
        print("usage: calculate_indicators.py <input.json>", file=sys.stderr)
        sys.exit(1)
    data = normalize_financials(load_json(Path(sys.argv[1])))
    print(write_json(calculate_indicators(data)))


if __name__ == "__main__":
    main()
