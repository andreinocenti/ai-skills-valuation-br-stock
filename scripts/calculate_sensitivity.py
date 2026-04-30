#!/usr/bin/env python3
import sys
from pathlib import Path

from valuation_core import calculate_sensitivity, load_json, write_json


def main():
    if len(sys.argv) != 2:
        print("usage: calculate_sensitivity.py <valuation.json>", file=sys.stderr)
        sys.exit(1)
    print(write_json(calculate_sensitivity(load_json(Path(sys.argv[1])))))


if __name__ == "__main__":
    main()
