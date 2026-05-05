#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("utilities", ["ddm", "dcf_fcfe"], ["ev_ebitda"], ["bazin", "graham"], ["peter_lynch"], ["tarifa", "rap", "capex", "divida", "concessoes"], 0.15, 0.1)
