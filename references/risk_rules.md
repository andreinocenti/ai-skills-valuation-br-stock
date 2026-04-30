# Risk Rules

- Se `divida_liquida_EBITDA > 3`, marque risco financeiro elevado, aumente taxa de desconto e margem de seguranca.
- Se `payout > 1`, marque dividendo potencialmente insustentavel.
- Se lucro sobe e caixa operacional cai, gere alerta de qualidade do lucro.
- Se `ROE` alto depende de patrimonio muito baixo, trate ROE como possivelmente distorcido.
- Se o dividend yield vier de evento extraordinario, exclua da media recorrente.
- Se houver varios anos de prejuizo, nao aplique Graham de forma mecanica.
- Se houver risco regulatorio material, ajuste crescimento terminal ou desconto.
- Se a governanca for fraca ou houver baixa liquidez, aumente premio especifico.
