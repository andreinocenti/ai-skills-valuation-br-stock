#!/usr/bin/env python3
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import fetch_url


def cache_path(cache_dir, key):
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return Path(cache_dir) / digest


def get_or_fetch(cache_dir, url):
    path = cache_path(cache_dir, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(fetch_url(url))
    return path


def main():
    if len(sys.argv) != 3:
        print("usage: cache_manager.py <cache-dir> <url>", file=sys.stderr)
        sys.exit(1)
    print(get_or_fetch(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
