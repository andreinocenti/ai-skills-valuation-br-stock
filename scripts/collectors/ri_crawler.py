#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import SOURCE_AUXILIARY, SOURCE_NOT_FOUND, fetch_url, write_json


def crawl_ri(url):
    try:
        html = fetch_url(url).decode("utf-8", errors="replace")
        links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', html)))
        documents = [link for link in links if any(term in link.lower() for term in ("resultado", "release", "apresent", ".pdf"))]
        return {"url": url, "documents": documents[:100], "source_status": SOURCE_AUXILIARY}
    except Exception as exc:
        return {"url": url, "documents": [], "source_status": SOURCE_NOT_FOUND, "error": str(exc)}


def main():
    if len(sys.argv) != 2:
        print("usage: ri_crawler.py <ri-url>", file=sys.stderr)
        sys.exit(1)
    print(write_json(crawl_ri(sys.argv[1])))


if __name__ == "__main__":
    main()
