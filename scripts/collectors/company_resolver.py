#!/usr/bin/env python3
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import KNOWN_B3_COMPANIES, SOURCE_AUXILIARY, SOURCE_INFERRED, SOURCE_OFFICIAL, fetch_url, ticker_registry, write_json


CAD_CIA_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
AUXILIARY_PROFILE_URL = "https://www.dadosdemercado.com.br/acoes/{ticker}"


SHARE_CLASS_BY_SUFFIX = {
    "3": "ON",
    "4": "PN",
    "5": "PNA",
    "6": "PNB",
    "7": "PNC",
    "8": "PND",
}


def infer_share_class(ticker):
    ticker = ticker.upper().strip()
    if ticker.endswith("11"):
        return "UNIT"
    return SHARE_CLASS_BY_SUFFIX.get(ticker[-1:], "nao_encontrado")


def valid_b3_equity_ticker(ticker):
    return bool(re.fullmatch(r"[A-Z0-9]{4}[0-9]{1,2}", ticker.upper().strip()))


def normalize_ws(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def find_after_label(text, label):
    terminators = (
        "Razao social|Razão social|CNPJ|Site do RI|Site|Classificacao setorial B3|"
        "Classificação setorial B3|Codigo ISIN|Código ISIN|Codigo CVM|Código CVM|"
        "Setor|Subsetor|Segmento|Situacao|Situação|Anos na bolsa|Free float|Outros tickers"
    )
    pattern = rf"{re.escape(label)}\s+(.*?)(?=\s+(?:{terminators})\s+|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return normalize_ws(match.group(1)) if match else None


def fetch_auxiliary_profile(ticker):
    url = AUXILIARY_PROFILE_URL.format(ticker=ticker.lower())
    content = fetch_url(url).decode("utf-8", errors="replace")
    text = normalize_ws(re.sub(r"<[^>]+>", " ", content))
    name = find_after_label(text, "Razão social") or find_after_label(text, "Razao social")
    cnpj = find_after_label(text, "CNPJ")
    cvm_code = find_after_label(text, "Código CVM") or find_after_label(text, "Codigo CVM")
    sector_line = find_after_label(text, "Classificação setorial B3") or find_after_label(text, "Classificacao setorial B3")
    sector = subsector = segment = None
    if sector_line:
        parts = [normalize_ws(part) for part in re.split(r"/|>", sector_line) if normalize_ws(part)]
        sector = parts[0] if len(parts) > 0 else None
        subsector = parts[1] if len(parts) > 1 else None
        segment = parts[2] if len(parts) > 2 else None
    if not any((name, cnpj, cvm_code, sector)):
        return {}
    return {
        "name": name,
        "cnpj": cnpj,
        "cvm_code": re.sub(r"\D", "", cvm_code or "") or None,
        "sector": sector,
        "subsector": subsector,
        "segment": segment,
        "source_status": SOURCE_AUXILIARY,
        "source_note": "ticker resolvido por fonte auxiliar; confirmar em CVM/B3 quando possivel",
        "source_url": url,
    }


def resolve_company(ticker):
    ticker = ticker.upper().strip()
    if not valid_b3_equity_ticker(ticker):
        return {
            "ticker": ticker,
            "market": "B3",
            "name": ticker,
            "currency": "BRL",
            "share_class": "nao_encontrado",
            "sector": None,
            "cvm_code": None,
            "source_status": SOURCE_INFERRED,
            "validation_error": "ticker fora do padrao de acoes B3 esperado, como PETR4, VALE3 ou KLBN11",
        }
    registry_item = ticker_registry().get(ticker, {})
    known = registry_item or KNOWN_B3_COMPANIES.get(ticker, {})
    auxiliary = {}
    if not known:
        try:
            auxiliary = fetch_auxiliary_profile(ticker)
        except Exception as exc:
            auxiliary = {"resolver_error": str(exc)}
    known = known or (auxiliary if auxiliary.get("cvm_code") or auxiliary.get("cnpj") or auxiliary.get("sector") else {})
    share_class = infer_share_class(ticker)
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
        profile["source_status"] = known.get("source_status", SOURCE_OFFICIAL)
        profile["source_note"] = known.get("source_note", "ticker resolvido por registry local de companhias B3/CVM")
        for key in ("cnpj", "subsector", "segment", "ri_url", "source_url"):
            if known.get(key):
                profile[key] = known[key]
    if auxiliary.get("resolver_error"):
        profile["resolver_error"] = auxiliary["resolver_error"]
    return profile


def fetch_cvm_registry():
    content = fetch_url(CAD_CIA_URL).decode("latin1", errors="replace").splitlines()
    import csv

    return [dict(row) for row in csv.DictReader(content, delimiter=";")]


def enrich_from_cvm_registry(profile):
    cvm_code = str(profile.get("cvm_code") or "").strip()
    cnpj = re.sub(r"\D", "", str(profile.get("cnpj") or ""))
    if not cvm_code and not cnpj:
        return profile
    try:
        rows = fetch_cvm_registry()
    except Exception as exc:
        profile["registry_error"] = str(exc)
        return profile
    match = None
    if cvm_code:
        match = next((row for row in rows if str(row.get("CD_CVM", "")).strip() == cvm_code), None)
    if not match and cnpj:
        match = next((row for row in rows if re.sub(r"\D", "", str(row.get("CNPJ_CIA", ""))) == cnpj), None)
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
