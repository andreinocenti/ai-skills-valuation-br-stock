#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collectors import company_resolver


def run(command):
    return subprocess.check_output(command, text=True)


def load(command):
    return json.loads(run(command))


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_auxiliary_resolution_for_unmapped_b3_ticker():
    original_fetch = company_resolver.fetch_url
    html = """
    <html><body>
      <h1>ABEV3 (Ambev)</h1>
      <p>Razao social AMBEV S.A.</p>
      <p>CNPJ 07.526.557/0001-00</p>
      <p>Classificacao setorial B3 Consumo nao Ciclico / Bebidas / Cervejas e Refrigerantes</p>
      <p>Codigo CVM 23264</p>
    </body></html>
    """.encode("utf-8")
    try:
        company_resolver.fetch_url = lambda url: html
        profile = company_resolver.resolve_company("ABEV3")
    finally:
        company_resolver.fetch_url = original_fetch
    assert_true(profile["source_status"] == "auxiliar", profile)
    assert_true(profile["cvm_code"] == "23264", profile)
    assert_true(profile["share_class"] == "ON", profile)
    assert_true(profile["sector"] == "Consumo nao Ciclico", profile)


def test_invalid_b3_ticker_is_rejected_without_fabricating_company():
    profile = company_resolver.resolve_company("PETR4F")
    assert_true(profile["cvm_code"] is None, profile)
    assert_true(profile["source_status"] == "inferido", profile)
    assert_true("validation_error" in profile, profile)


def test_b3_ticker_with_digit_in_prefix_is_valid():
    original_fetch = company_resolver.fetch_url
    try:
        company_resolver.fetch_url = lambda url: (_ for _ in ()).throw(RuntimeError("offline"))
        profile = company_resolver.resolve_company("B3SA3")
    finally:
        company_resolver.fetch_url = original_fetch
    assert_true("validation_error" not in profile, profile)
    assert_true(profile["share_class"] == "ON", profile)
    assert_true(profile["source_status"] == "inferido", profile)


def test_cvm_registry_enrichment_can_match_by_cnpj():
    original_fetch = company_resolver.fetch_url
    csv_data = (
        "CD_CVM;DENOM_SOCIAL;CNPJ_CIA;SITE;SETOR_ATIV\n"
        "23264;AMBEV S.A.;07.526.557/0001-00;https://ri.ambev.com.br;Bebidas\n"
    ).encode("latin1")
    try:
        company_resolver.fetch_url = lambda url: csv_data
        profile = company_resolver.enrich_from_cvm_registry({
            "ticker": "ABEV3",
            "name": "Ambev S.A.",
            "cnpj": "07.526.557/0001-00",
            "cvm_code": None,
            "source_status": "auxiliar",
        })
    finally:
        company_resolver.fetch_url = original_fetch
    assert_true(profile["cvm_code"] == "23264", profile)
    assert_true(profile["source_status"] == "oficial", profile)


def main():
    test_auxiliary_resolution_for_unmapped_b3_ticker()
    test_invalid_b3_ticker_is_rejected_without_fabricating_company()
    test_b3_ticker_with_digit_in_prefix_is_valid()
    test_cvm_registry_enrichment_can_match_by_cnpj()

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
