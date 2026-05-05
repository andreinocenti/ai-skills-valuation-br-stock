#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("holding", ["nav", "sotp"], ["dividend_look_through"], ["graham"], ["peter_lynch"], ["participacoes", "desconto_holding", "caixa_divida"], 0.25, 0.11)
