# Changelog Plan v5

- Yahoo Finance removido como padrao em `config/defaults.json`; `allow_yahoo_fallback=false`.
- Nova camada canonica de dividendos oficiais em `scripts/collectors/dividends/` com CVM/B3/RI, BRAPI gratuita, agregadores e reconciliacao.
- Pipeline principal agora carrega reconciliacao de dividendos, RI documents parseados e `quality_of_earnings`.
- Custo de capital formalizado em `scripts/valuation/discount_rate_builder.py`.
- Selecao setorial formalizada em `scripts/valuation/method_role_selector.py`.
- Sanity checks formais adicionados em `scripts/valuation/validate_valuation_sanity.py`.
- Relatorio final expandido com fontes de dividendos, ponte de DPA recorrente/seguro, metodologia setorial, sanity checks e semantica do preco teto projetivo.
