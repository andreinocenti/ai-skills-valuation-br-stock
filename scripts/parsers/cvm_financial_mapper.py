#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import write_json


ACCOUNT_MAPPING = {
    "revenue": ["3.01", "3.01.01"],
    "ebit": ["3.05", "3.05.01"],
    "net_income": ["3.11", "3.13", "3.99"],
    "cash": ["1.01.01"],
    "equity": ["2.03"],
    "short_debt": ["2.01.04", "2.01.04.01", "2.01.04.02"],
    "long_debt": ["2.02.01", "2.02.01.01", "2.02.01.02"],
    "operating_cash_flow": ["6.01"],
    "capex": ["6.02.01", "6.02.02"],
}


def main():
    if len(sys.argv) == 1:
        print(write_json({"account_mapping": ACCOUNT_MAPPING}))
        return
    metric = sys.argv[1]
    print(write_json({"metric": metric, "accounts": ACCOUNT_MAPPING.get(metric, [])}))


if __name__ == "__main__":
    main()
