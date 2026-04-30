#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import write_json


def classify_document(path):
    name = Path(path).name.lower()
    if "dfp" in name:
        kind = "DFP"
    elif "itr" in name:
        kind = "ITR"
    elif "release" in name or "resultado" in name:
        kind = "release"
    elif "apresent" in name:
        kind = "presentation"
    elif "fato" in name:
        kind = "material_fact"
    else:
        kind = "unknown"
    return {"path": str(path), "document_type": kind}


def main():
    if len(sys.argv) != 2:
        print("usage: document_classifier.py <path>", file=sys.stderr)
        sys.exit(1)
    print(write_json(classify_document(sys.argv[1])))


if __name__ == "__main__":
    main()
