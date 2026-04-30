#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline.run_collection_pipeline import run_pipeline
from valuation_core import calculate_sensitivity, calculate_valuation, write_json
from generate_report import generate_markdown


def analyze_ticker(ticker, cache_dir, years=None):
    dataset = run_pipeline(ticker, cache_dir, years)
    if len(dataset.get("financials", [])) < 3 or not dataset.get("market_data", {}).get("current_price"):
        return {
            "ok": False,
            "stage": "collection",
            "dataset": dataset,
            "errors": dataset.get("limitations", []),
        }
    valuation = calculate_valuation(dataset)
    sensitivity = calculate_sensitivity(valuation)
    valuation["sensitivity"] = sensitivity
    return {
        "ok": True,
        "dataset": dataset,
        "report": {
            "markdown": generate_markdown(valuation, sensitivity),
            "json": valuation,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run ticker -> collection -> valuation -> report.")
    parser.add_argument("ticker")
    parser.add_argument("--cache-dir", default="/tmp/valuation-br-stock-cache")
    parser.add_argument("--years", help="Comma-separated DFP years")
    args = parser.parse_args()
    years = [int(item) for item in args.years.split(",")] if args.years else None
    print(write_json(analyze_ticker(args.ticker, args.cache_dir, years)))


if __name__ == "__main__":
    main()
