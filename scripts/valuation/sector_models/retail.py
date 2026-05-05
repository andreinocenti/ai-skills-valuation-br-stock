#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("retail", ["dcf_fcff", "dcf_fcfe"], ["ev_ebitda"], ["graham"], ["peter_lynch"], ["sss", "margem_bruta", "sga", "capital_de_giro", "juros"], 0.3, 0.12)
