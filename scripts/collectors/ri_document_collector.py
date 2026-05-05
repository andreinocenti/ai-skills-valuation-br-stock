#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.ri_crawler import crawl_ri
from collectors.ri_site_resolver import resolve_ri_site
from valuation_core import SOURCE_NOT_FOUND, write_json


def collect_ri_documents(ticker):
    site = resolve_ri_site(ticker)
    if not site.get("ri_url"):
        return {
            "ticker": ticker.upper(),
            "ri_url": None,
            "documents": [],
            "source_status": SOURCE_NOT_FOUND,
            "error": "RI URL not mapped for ticker.",
        }
    crawled = crawl_ri(site["ri_url"])
    crawled["ticker"] = ticker.upper()
    crawled["company_name"] = site.get("company_name")
    crawled["ri_url"] = site["ri_url"]
    return crawled


def main():
    if len(sys.argv) != 2:
        print("usage: ri_document_collector.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_ri_documents(sys.argv[1])))


if __name__ == "__main__":
    main()
