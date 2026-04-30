#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import SOURCE_OFFICIAL, SOURCE_NOT_FOUND, fetch_url, parse_cvm_dfp_zip, write_json


CVM_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC"


def cvm_zip_url(document_type, year):
    document_type = document_type.upper()
    return f"{CVM_BASE}/{document_type}/DADOS/{document_type.lower()}_cia_aberta_{year}.zip"


def download_cvm_document(document_type, year, output_dir):
    url = cvm_zip_url(document_type, year)
    output = Path(output_dir) / Path(url).name
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.stat().st_size > 0:
        return {"path": str(output), "url": url, "source_status": SOURCE_OFFICIAL, "cache": True}
    try:
        output.write_bytes(fetch_url(url))
        return {"path": str(output), "url": url, "source_status": SOURCE_OFFICIAL}
    except Exception as exc:
        return {"path": None, "url": url, "source_status": SOURCE_NOT_FOUND, "error": str(exc)}


def collect_dfp_financials(cvm_code, years, output_dir):
    rows = []
    downloads = []
    for year in years:
        result = download_cvm_document("DFP", year, output_dir)
        downloads.append(result)
        if result.get("path"):
            rows.extend(parse_cvm_dfp_zip(result["path"], cvm_code))
    return {"financials": rows, "downloads": downloads, "source_status": SOURCE_OFFICIAL if rows else SOURCE_NOT_FOUND}


def collect_itr_financials(cvm_code, years, output_dir):
    rows = []
    downloads = []
    for year in years:
        result = download_cvm_document("ITR", year, output_dir)
        downloads.append(result)
        if result.get("path"):
            rows.extend(parse_cvm_dfp_zip(result["path"], cvm_code))
    return {"financials": rows, "downloads": downloads, "source_status": SOURCE_OFFICIAL if rows else SOURCE_NOT_FOUND}


def main():
    if len(sys.argv) < 4:
        print("usage: cvm_collector.py <DFP|ITR|FCA|FRE|DFP_FINANCIALS|ITR_FINANCIALS> <year-or-cvm-code> <output-dir> [years_csv]", file=sys.stderr)
        sys.exit(1)
    if sys.argv[1].upper() == "DFP_FINANCIALS":
        years = [int(item) for item in (sys.argv[4].split(",") if len(sys.argv) > 4 else [])]
        print(write_json(collect_dfp_financials(sys.argv[2], years, sys.argv[3])))
    elif sys.argv[1].upper() == "ITR_FINANCIALS":
        years = [int(item) for item in (sys.argv[4].split(",") if len(sys.argv) > 4 else [])]
        print(write_json(collect_itr_financials(sys.argv[2], years, sys.argv[3])))
    else:
        print(write_json(download_cvm_document(sys.argv[1], sys.argv[2], sys.argv[3])))


if __name__ == "__main__":
    main()
