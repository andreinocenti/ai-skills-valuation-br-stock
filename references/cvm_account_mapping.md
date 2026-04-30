# CVM Account Mapping

The parser uses consolidated DFP/ITR statements first.

Core mappings:

- Revenue: `3.01`, fallback `3.01.01`
- EBIT: `3.05`, fallback `3.05.01`
- Net income: `3.11`, fallback `3.13`, `3.99`
- Cash: `1.01.01`
- Equity: `2.03`
- Short debt: `2.01.04`, `2.01.04.01`, `2.01.04.02`
- Long debt: `2.02.01`, `2.02.01.01`, `2.02.01.02`
- Operating cash flow: `6.01`
- CAPEX: `6.02.01`, `6.02.02`

Sector caveat:

- Banks and insurers often need specialized financial statement treatment. For those sectors, prioritize P/VP, ROE, payout and residual income, and lower the reliability of industrial-style DCF/EV methods.
