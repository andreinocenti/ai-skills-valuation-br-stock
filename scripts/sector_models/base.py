#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from valuation_core import sector_method_weights


def model_for_sector(sector):
    return {"sector": sector, "weights": sector_method_weights(sector)}
