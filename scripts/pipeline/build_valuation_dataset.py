#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import load_json, normalize_financials, write_json


def build_dataset(input_path):
    data = load_json(input_path)
    return normalize_financials(data)


def main():
    if len(sys.argv) != 2:
        print("usage: build_valuation_dataset.py <raw-input.json>", file=sys.stderr)
        sys.exit(1)
    print(write_json(build_dataset(sys.argv[1])))


if __name__ == "__main__":
    main()
