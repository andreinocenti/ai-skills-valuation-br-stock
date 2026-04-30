# Data Quality Policy

Classifique a confianca da base em:

- `high`
- `medium_high`
- `medium`
- `medium_low`
- `low`

## Checklist

- Ha pelo menos 5 anos de historico?
- Existem anos faltantes?
- O numero de acoes mudou materialmente?
- O patrimonio e positivo?
- O lucro e recorrente ou fortemente distorcido?
- Os dividendos sao recorrentes?
- O caixa operacional acompanha o lucro?
- Ha itens nao recorrentes sem ajuste?

## Interpretacao

- `high`: base longa, coerente e pouco dependente de inferencias.
- `medium_high`: base boa com poucos ajustes.
- `medium`: ha dados suficientes, mas com ruido relevante.
- `medium_low`: varios campos inferidos, historico curto ou setor pouco previsivel.
- `low`: faltam dados criticos para valuation confiavel.
