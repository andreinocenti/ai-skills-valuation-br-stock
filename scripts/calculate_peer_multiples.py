#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collectors.peer_group_collector import collect_peer_group
from valuation_core import write_json


def main():
    if len(sys.argv) != 2:
        print("usage: calculate_peer_multiples.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(collect_peer_group(sys.argv[1])))


if __name__ == "__main__":
    main()
