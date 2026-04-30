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


def fetch_bcb_values(series_id, count=1):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados/ultimos/{count}?formato=json"
    data = json.loads(fetch_url(url).decode("utf-8"))
    return [float(item["valor"].replace(",", ".")) for item in data]


def fetch_bcb_latest(series_id):
    return fetch_bcb_values(series_id, 1)[-1]


def collect_macro():
    output = {"source_status": SOURCE_OFFICIAL}
    for name, series_id in BCB_SERIES.items():
        try:
            output[name] = fetch_bcb_latest(series_id)
        except Exception as exc:
            output[name] = None
            output[f"{name}_error"] = str(exc)
            output["source_status"] = SOURCE_NOT_FOUND
    if output.get("ipca") is not None:
        output["ipca_monthly_latest"] = output["ipca"]
        try:
            monthly = fetch_bcb_values(BCB_SERIES["ipca"], 12)
            accumulated = 1.0
            for value in monthly:
                accumulated *= 1 + value / 100
            output["ipca_12m_estimated"] = (accumulated - 1) * 100
        except Exception as exc:
            output["ipca_12m_estimated"] = None
            output["ipca_12m_error"] = str(exc)
    return output


def main():
    print(write_json(collect_macro()))


if __name__ == "__main__":
    main()
