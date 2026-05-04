# Output Template

```markdown
# Valuation de [TICKER] - [Empresa]

## 1. Resumo executivo
## 2. Dados da empresa
## 3. Fontes utilizadas
## 4. Cotacao atual e visao geral
- Versao da skill: [skill_version]
- Versao do motor: [engine_version]
## 5. Diagnostico fundamentalista
## 6. Qualidade do lucro
## 7. Dividendos e payout
## 8. Endividamento
## 9. Projecoes ano a ano
## 10. Metodos de valuation
## 11. Analise de sensibilidade
## 12. Preco teto
## 13. Preco teto projetivo
## 14. Reverse DCF
## 15. Comparacao com pares
## 16. Riscos
## 17. Score final
## 18. Veredito
## 19. Limitacoes da analise
```

## JSON Minimo

Inclua:

- `ticker`
- `skill_version`
- `company_name`
- `current_price`
- `fair_value_base`
- `fair_value_conservative`
- `fair_value_optimistic`
- `suggested_ceiling_price`
- `projected_ceiling_price`
- `margin_of_safety`
- `dividend_safe_yield`
- `projected_yield_on_cost_year_5`
- `quality_score`
- `opportunity_score`
- `risk_level`
- `verdict`
- `confidence`
