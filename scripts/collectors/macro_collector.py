#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import SOURCE_OFFICIAL, SOURCE_NOT_FOUND, fetch_url, write_json


BCB_SERIES = {
    "selic": 432,
    "ipca": 433,
    "cdi": 4389,
    "usd_brl": 1,
}


def fetch_bcb_latest(series_id):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados/ultimos/1?formato=json"
    data = json.loads(fetch_url(url).decode("utf-8"))
    return float(data[-1]["valor"].replace(",", "."))


def collect_macro():
    output = {"source_status": SOURCE_OFFICIAL}
    for name, series_id in BCB_SERIES.items():
        try:
            output[name] = fetch_bcb_latest(series_id)
        except Exception as exc:
            output[name] = None
            output[f"{name}_error"] = str(exc)
            output["source_status"] = SOURCE_NOT_FOUND
    return output


def main():
    print(write_json(collect_macro()))


if __name__ == "__main__":
    main()
