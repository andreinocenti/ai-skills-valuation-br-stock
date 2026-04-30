# Data Sources

Ordem de prioridade:

1. CVM
2. B3
3. RI da empresa
4. Banco Central
5. IBGE
6. provedores de mercado
7. agregadores

## Regras

- Confirme numeros materialmente relevantes com CVM, B3 ou RI quando possivel.
- Se o dado vier de fonte auxiliar, marque como `auxiliar`.
- Se o dado nao puder ser confirmado, marque como `estimada` ou `inferida`.
- Prefira demonstracoes estruturadas da CVM a extracao de PDF.
- Use DFP anual como base historica principal e ITR/TTM para tendencia recente.
