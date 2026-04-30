# Examples

## Uso simples

```text
$valuation-br-stock Faca o valuation completo de CMIG4.
```

## Uso focado em dividendos

```text
$valuation-br-stock Analise BBAS3 com foco em dividendos e preco teto projetivo.
```

## Uso com JSON

```json
{
  "ticker": "CMIG4",
  "market": "B3",
  "analysis_focus": "dividends",
  "investment_horizon_years": 5,
  "required_return": 0.12,
  "desired_dividend_yields": [0.06, 0.08, 0.10, 0.12],
  "margin_of_safety": 0.25,
  "use_official_sources_only": false,
  "generate_full_report": true
}
```
