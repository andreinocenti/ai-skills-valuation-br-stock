#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import peer_groups, write_json


def collect_peer_group(ticker):
    ticker = ticker.upper()
    peers = peer_groups().get(ticker, [])
    return {"ticker": ticker, "peers": peers, "available": bool(peers)}


def main():
    if len(sys.argv) != 2:
        print("usage: peer_group_collector.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_peer_group(sys.argv[1])))


if __name__ == "__main__":
    main()
