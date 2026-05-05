#!/usr/bin/env python3
import re
import sys
from urllib.parse import urljoin
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import SOURCE_AUXILIARY, SOURCE_NOT_FOUND, fetch_url, write_json


TARGET_TERMS = (
    "resultado",
    "release",
    "apresent",
    "dividend",
    "dividendos",
    "provento",
    "proventos",
    "acionistas",
    ".pdf",
)


def discover_ri_candidates(base_url: str) -> list[str]:
    candidates = [base_url]
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    try:
        sitemap = fetch_url(sitemap_url).decode("utf-8", errors="replace")
        candidates.append(sitemap_url)
        locations = re.findall(r"<loc>([^<]+)</loc>", sitemap, flags=re.IGNORECASE)
        for location in locations:
            if any(term in location.lower() for term in TARGET_TERMS):
                candidates.append(location)
    except Exception:
        pass
    return list(dict.fromkeys(candidates))


def crawl_ri(url):
    try:
        documents = []
        for candidate in discover_ri_candidates(url):
            html = fetch_url(candidate).decode("utf-8", errors="replace")
            links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', html)))
            for link in links:
                if not any(term in link.lower() for term in TARGET_TERMS):
                    continue
                full_url = urljoin(candidate, link)
                text = ""
                if not full_url.lower().endswith(".pdf"):
                    try:
                        text = fetch_url(full_url).decode("utf-8", errors="replace")
                    except Exception:
                        text = ""
                documents.append({"url": full_url, "text": text, "document_type": "RI"})
            if any(term in candidate.lower() for term in ("dividend", "provento", "acionistas")):
                documents.append({"url": candidate, "text": html, "document_type": "RI"})
        documents = list({item["url"]: item for item in documents}.values())
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
