#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import source_entry, write_json


class SourceRegistry:
    def __init__(self, path):
        self.path = Path(path)
        self.sources = []
        if self.path.exists():
            self.sources = json.loads(self.path.read_text(encoding="utf-8"))

    def add(self, name, kind, status="confirmed", url=None, notes=None):
        item = source_entry(name, kind, status, url)
        if notes:
            item["notes"] = notes
        self.sources.append(item)
        return item

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(write_json(self.sources), encoding="utf-8")


def main():
    if len(sys.argv) < 4:
        print("usage: source_registry.py <registry.json> <name> <type> [url]", file=sys.stderr)
        sys.exit(1)
    registry = SourceRegistry(sys.argv[1])
    registry.add(sys.argv[2], sys.argv[3], url=sys.argv[4] if len(sys.argv) > 4 else None)
    registry.save()
    print(write_json(registry.sources))


if __name__ == "__main__":
    main()
