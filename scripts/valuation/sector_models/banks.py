#!/usr/bin/env python3
from valuation.sector_models.base import sector_model


MODEL = sector_model("banks", ["residual_income", "p_vp_justified"], ["dividend_capacity"], ["graham"], ["ev_ebitda", "dcf_fcff"], ["roe", "equity", "payout", "inadimplencia"], 0.2, 0.12)
