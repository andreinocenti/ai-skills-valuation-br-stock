# Dividend Policy

Classify dividend events before using them in valuation:

- `dividendo`: ordinary dividend.
- `jcp`: interest on equity.
- `extraordinario`: non-recurring distribution, asset sale, one-off payout, capital return.
- `outro`: unresolved event.

Rules:

- Bazin uses only recurring dividends and JCP.
- Yield seguro must not exceed recurring adjusted yield.
- Extraordinary events stay in reported dividends but are excluded from recurring dividends.
- If official B3/CVM/RI events are unavailable, auxiliary market data may be used with explicit source status.
