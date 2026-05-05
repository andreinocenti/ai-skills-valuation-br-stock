#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("insurance", ["p_vp_justified", "residual_income"], ["ddm"], ["graham"], ["peter_lynch"], ["roe", "sinistralidade", "capital"], 0.2, 0.11)
