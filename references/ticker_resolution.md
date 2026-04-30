# Ticker Resolution

Use `references/ticker_registry.json` as the deterministic local registry for liquid B3 tickers. Prefer official CVM/B3 data when online collection succeeds, then merge it over the local registry.

Resolution order:

1. Exact ticker in `ticker_registry.json`.
2. `KNOWN_B3_COMPANIES` in `scripts/valuation_core.py`.
3. CVM company registry enrichment by `cvm_code`.
4. Inferred share class from ticker suffix.

Never fabricate CNPJ, CVM code, sector, free float or RI URL. If a field is unavailable, keep it missing and mark the source status accordingly.
