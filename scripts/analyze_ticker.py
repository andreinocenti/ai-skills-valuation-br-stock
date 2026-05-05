#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline.run_collection_pipeline import run_pipeline
from valuation_core import calculate_sensitivity, calculate_valuation, valuation_readiness, write_json
from generate_report import generate_markdown


DEFAULT_OUTPUT_DIR = Path.home() / ".valuation-stock-br"


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
    readiness = valuation_readiness(dataset, valuation.get("financial_diagnosis", {}))
    if not readiness["full_valuation_allowed"]:
        return {
            "ok": False,
            "stage": "valuation",
            "dataset": dataset,
            "report": {
                "markdown": generate_markdown(valuation, calculate_sensitivity(valuation)),
                "json": valuation,
            },
            "errors": readiness["reasons"],
        }
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


def default_output_paths(ticker, output_dir):
    ticker_slug = ticker.upper().strip().lower()
    directory = Path(output_dir).expanduser()
    return {
        "json": directory / f"{ticker_slug}-analysis.json",
        "markdown": directory / f"{ticker_slug}-report.md",
    }


def write_report_files(result, ticker, output_dir=None, out_json=None, out_md=None):
    paths = default_output_paths(ticker, output_dir or DEFAULT_OUTPUT_DIR)
    json_path = Path(out_json).expanduser() if out_json else paths["json"]
    md_path = Path(out_md).expanduser() if out_md else paths["markdown"]

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(write_json(result), encoding="utf-8")

    written = {"json": str(json_path)}
    markdown = result.get("report", {}).get("markdown")
    if markdown:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
        written["markdown"] = str(md_path)
    return written


def main():
    parser = argparse.ArgumentParser(description="Run ticker -> collection -> valuation -> report.")
    parser.add_argument("ticker")
    parser.add_argument("--cache-dir", default=str(DEFAULT_OUTPUT_DIR / "cache"))
    parser.add_argument("--years", help="Comma-separated DFP years")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for generated support reports")
    parser.add_argument("--out-json", help="Write full analysis JSON to this path")
    parser.add_argument("--out-md", help="Write markdown report to this path (only when ok=true)")
    parser.add_argument("--no-write-reports", action="store_true", help="Do not write support report files")
    args = parser.parse_args()
    years = [int(item) for item in args.years.split(",")] if args.years else None
    result = analyze_ticker(args.ticker, args.cache_dir, years)
    if not args.no_write_reports:
        result["support_reports"] = write_report_files(result, args.ticker, args.output_dir, args.out_json, args.out_md)
    print(write_json(result))


if __name__ == "__main__":
    main()
