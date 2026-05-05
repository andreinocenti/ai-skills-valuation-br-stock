#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("commodities", ["normalized_ev_ebitda", "dcf_fcff"], ["fcf_yield", "multiples"], ["graham"], ["peter_lynch"], ["preco_commodity", "cambio", "custo_caixa", "ciclo"], 0.3, 0.12)
