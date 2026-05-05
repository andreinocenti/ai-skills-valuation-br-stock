#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("financial_services", ["dcf_fcfe", "multiples"], ["dcf_fcff"], ["graham"], ["peter_lynch"], ["volume", "take_rate", "margem", "regulacao"], 0.2, 0.11)
