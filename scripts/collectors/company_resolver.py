#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import KNOWN_B3_COMPANIES, SOURCE_INFERRED, SOURCE_OFFICIAL, fetch_url, ticker_registry, write_json


CAD_CIA_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"


def resolve_company(ticker):
    ticker = ticker.upper().strip()
    registry_item = ticker_registry().get(ticker, {})
    known = registry_item or KNOWN_B3_COMPANIES.get(ticker, {})
    share_class = "UNIT" if ticker.endswith("11") else "PN" if ticker.endswith(("4", "5", "6")) else "ON" if ticker.endswith("3") else "nao_encontrado"
    profile = {
        "ticker": ticker,
        "market": "B3",
        "name": known.get("name", ticker),
        "currency": "BRL",
        "share_class": known.get("share_class", share_class),
        "sector": known.get("sector"),
        "cvm_code": known.get("cvm_code"),
        "source_status": SOURCE_INFERRED,
    }
    if known:
        profile["source_status"] = SOURCE_OFFICIAL
        profile["source_note"] = "ticker resolvido por registry local de companhias B3/CVM"
        for key in ("cnpj", "subsector", "segment", "ri_url"):
            if known.get(key):
                profile[key] = known[key]
    return profile


def fetch_cvm_registry():
    content = fetch_url(CAD_CIA_URL).decode("latin1", errors="replace").splitlines()
    import csv

    return [dict(row) for row in csv.DictReader(content, delimiter=";")]


def enrich_from_cvm_registry(profile):
    cvm_code = str(profile.get("cvm_code") or "").strip()
    if not cvm_code:
        return profile
    try:
        rows = fetch_cvm_registry()
    except Exception as exc:
        profile["registry_error"] = str(exc)
        return profile
    match = next((row for row in rows if str(row.get("CD_CVM", "")).strip() == cvm_code), None)
    if not match:
        return profile
    profile.update({
        "name": match.get("DENOM_SOCIAL") or profile.get("name"),
        "cnpj": match.get("CNPJ_CIA"),
        "cvm_code": match.get("CD_CVM") or cvm_code,
        "ri_url": match.get("SITE"),
        "source_status": SOURCE_OFFICIAL,
    })
    if match.get("SETOR_ATIV"):
        profile.setdefault("sector", match.get("SETOR_ATIV"))
    return profile


def main():
    if len(sys.argv) != 2:
        print("usage: company_resolver.py <ticker>", file=sys.stderr)
        sys.exit(1)
    print(write_json(enrich_from_cvm_registry(resolve_company(sys.argv[1]))))


if __name__ == "__main__":
    main()
