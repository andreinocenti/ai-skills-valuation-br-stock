#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command):
    return subprocess.check_output(command, text=True)


def load(command):
    return json.loads(run(command))


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    registry = load([sys.executable, "-B", str(ROOT / "scripts" / "storage" / "ticker_registry.py")])
    assert_true(len(registry["tickers"]) >= 10, "ticker registry should cover at least 10 liquid B3 tickers")

    instruments = load([sys.executable, "-B", str(ROOT / "scripts" / "collectors" / "b3_instruments_collector.py")])
    assert_true(any(row["ticker"] == "CMIG4" for row in instruments["instruments"]), "B3 instrument registry should include CMIG4")

    peers = load([sys.executable, "-B", str(ROOT / "scripts" / "collectors" / "peer_group_collector.py"), "CMIG4"])
    assert_true(peers["available"] and "TAEE11" in peers["peers"], "CMIG4 peer group should include TAEE11")

    ri = load([sys.executable, "-B", str(ROOT / "scripts" / "collectors" / "ri_site_resolver.py"), "CMIG4"])
    assert_true(ri.get("ri_url"), "CMIG4 should resolve RI URL")

    mapping = load([sys.executable, "-B", str(ROOT / "scripts" / "parsers" / "cvm_financial_mapper.py")])
    assert_true("net_income" in mapping["account_mapping"], "CVM mapper should expose net income accounts")

    with tempfile.TemporaryDirectory() as tmp:
        input_path = ROOT / "examples" / "example_input.json"
        ttm_path = Path(tmp) / "ttm.json"
        ttm_input = json.loads(input_path.read_text(encoding="utf-8"))
        ttm_path.write_text(json.dumps(ttm_input), encoding="utf-8")
        ttm = load([sys.executable, "-B", str(ROOT / "scripts" / "pipeline" / "build_ttm.py"), str(ttm_path)])
        assert_true(ttm["ttm"] is not None, "TTM builder should return a fallback row")

    print("ok")


if __name__ == "__main__":
    main()
