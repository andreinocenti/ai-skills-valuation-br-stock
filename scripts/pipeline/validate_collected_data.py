#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import calculate_indicators, load_json, normalize_financials, write_json


def validate_collected_data(data):
    normalized = normalize_financials(data)
    indicators = calculate_indicators(normalized)
    return {"ok": indicators["data_quality"]["confidence"] != "low", "data_quality": indicators["data_quality"]}


def main():
    if len(sys.argv) != 2:
        print("usage: validate_collected_data.py <valuation-input.json>", file=sys.stderr)
        sys.exit(1)
    print(write_json(validate_collected_data(load_json(sys.argv[1]))))


if __name__ == "__main__":
    main()
