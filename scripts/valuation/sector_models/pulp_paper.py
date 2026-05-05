#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("pulp_paper", ["dcf_fcfe", "normalized_ev_ebitda"], ["fcff"], ["graham"], ["peter_lynch"], ["celulose_usd", "cambio", "capex", "alavancagem"], 0.2, 0.11)
