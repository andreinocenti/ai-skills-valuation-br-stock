#!/usr/bin/env python3
from __future__ import annotations


def sector_model(name, primary_methods, secondary_methods, sanity_checks, excluded_methods, drivers, min_margin, min_ke):
    return {
        "name": name,
        "primary_methods": primary_methods,
        "secondary_methods": secondary_methods,
        "sanity_checks": sanity_checks,
        "excluded_methods": excluded_methods,
        "drivers": drivers,
        "minimum_margin_of_safety": min_margin,
        "minimum_cost_of_capital": min_ke,
    }
