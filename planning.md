
# Plano completo — Skill de Valuation de Ações Brasileiras

## 1. Objetivo da skill

Criar uma skill com o nome valuation-br-stock


Ela deve permitir que o usuário peça algo como:

```text
$valuation Faça o valuation completo de CMIG4.
```

Ou:

```text
$valuation Analise BBAS3 com foco em dividendos e preço teto projetivo.
```

E o agente deve entregar uma análise completa com:

```text
Preço justo estimado
Preço teto atual
Preço teto projetivo dos proximos 5 a 10 anos. Por padrao 5 anos.
Margem de segurança
Análise de dividendos
Yield seguro
Yield on cost projetado
DCF por FCFE
DCF por FCFF
Graham
Bazin
Peter Lynch
DDM/Gordon
Múltiplos comparativos
Reverse DCF
Análise de sensibilidade
Riscos
Qualidade do lucro
Endividamento
Premissas ano a ano
Veredito final
```

Importante: a skill deve classificar a oportunidade como:

```text
Evitar
Cara
Justa
Interessante
Atrativa com margem de segurança
```

---

# 2. Filosofia da skill

A skill não deve ser uma calculadora simples.

Ela deve funcionar como uma **esteira de análise fundamentalista**:

```text
Identificação da empresa
→ Coleta de dados
→ Validação das fontes
→ Extração dos demonstrativos
→ Normalização dos dados
→ Diagnóstico fundamentalista
→ Projeções
→ Valuation multi-método
→ Sensibilidade
→ Análise de riscos
→ Preço teto
→ Relatório final
```

O ponto principal é este:

> O valuation final depende mais da qualidade das premissas do que da fórmula usada.

Por isso, a skill precisa ser rigorosa em:

```text
Fonte dos dados
Dados recorrentes versus não recorrentes
Dividendos ordinários versus extraordinários
Lucro contábil versus geração real de caixa
Dívida e risco financeiro
Setor da empresa
Ciclicidade
Margem de segurança exigida
```

---

# 3. Estrutura de arquivos da skill

Sugestão de estrutura:

```text
valuation-br-stock/
├── SKILL.md
├── README.md
├── references/
│   ├── valuation_methods.md
│   ├── formulas.md
│   ├── data_sources.md
│   ├── sector_rules.md
│   ├── risk_rules.md
│   ├── output_template.md
│   ├── assumptions_policy.md
│   ├── data_quality_policy.md
│   └── examples.md
├── scripts/
│   ├── fetch_market_data.py
│   ├── fetch_cvm_data.py
│   ├── fetch_b3_data.py
│   ├── fetch_macro_data.py
│   ├── extract_pdf_tables.py
│   ├── parse_financial_statements.py
│   ├── normalize_financials.py
│   ├── detect_non_recurring_items.py
│   ├── calculate_indicators.py
│   ├── calculate_valuation.py
│   ├── calculate_sensitivity.py
│   ├── generate_report.py
│   └── validate_output.py
├── schemas/
│   ├── company_profile.schema.json
│   ├── financials.schema.json
│   ├── dividends.schema.json
│   ├── valuation_input.schema.json
│   ├── valuation_output.schema.json
│   └── report.schema.json
├── templates/
│   ├── report_summary.md
│   ├── full_report.md
│   ├── sensitivity_table.md
│   ├── assumptions_table.md
│   └── risk_matrix.md
└── examples/
    ├── cmig4_example_input.json
    ├── cmig4_example_output.md
    ├── bbas3_example_input.json
    └── bbas3_example_output.md
```

---

# 4. Função de cada arquivo

## 4.1. `SKILL.md`

Arquivo principal da skill.

Deve conter:

```yaml
---
name: valuation-br-stock
description: Use esta skill para analisar ações brasileiras da B3, coletar dados públicos, calcular valuation fundamentalista, preço justo, preço teto, preço teto projetivo, dividendos, margem de segurança, riscos e cenários.
---
```

Depois do front matter, o `SKILL.md` deve explicar:

```text
Quando usar a skill
Quando não usar
Fontes prioritárias
Workflow obrigatório
Métodos de valuation obrigatórios
Regras de normalização
Regras de segurança
Formato do output
Critérios mínimos de qualidade
```

---

## 4.2. `valuation_methods.md`

Documento com todas as metodologias aceitas.

Deve conter:

```text
Graham
Bazin
Peter Lynch
DDM/Gordon
DCF FCFE
DCF FCFF
Reverse DCF
Múltiplos comparativos
Lucro residual
SOTP
NAV
Valuation setorial
```

---

## 4.3. `formulas.md`

Documento com fórmulas padronizadas.

Exemplo:

```text
Valor Intrínseco Graham = √(22,5 × LPA × VPA)

Preço Teto Bazin = Dividendo Médio Recorrente / Yield Desejado

DDM Gordon = Dividendo Esperado / (Ke - g)

FCFE = Lucro Líquido + D&A - CAPEX - ΔCapital de Giro + Captação Líquida de Dívida

FCFF = EBIT × (1 - IR) + D&A - CAPEX - ΔCapital de Giro

Valor do Equity = Valor da Firma - Dívida Líquida

Preço Justo por Ação = Valor do Equity / Número de Ações

Margem de Segurança = (Valor Justo - Preço Atual) / Valor Justo

Yield on Cost Futuro = Dividendo Futuro por Ação / Preço Pago Hoje
```

---

## 4.4. `data_sources.md`

Documento com fontes em ordem de prioridade:

```text
1. CVM
2. B3
3. Site de RI da empresa
4. Banco Central
5. IBGE
6. Dados de mercado/cotação
7. Sites auxiliares como Investidor10, Status Invest, Fundamentus, Yahoo Finance etc.
```

Regra importante:

```text
Fontes auxiliares podem ser usadas para acelerar a análise, mas números relevantes devem ser confirmados, sempre que possível, com CVM, B3 ou RI da empresa.
```

---

## 4.5. `sector_rules.md`

Documento com regras por setor.

Exemplo:

```text
Bancos:
- Priorizar P/VP, ROE, P/L, payout, inadimplência, margem financeira.
- Não usar EV/EBITDA como método principal.
- DCF tradicional tem menor confiabilidade.
- Usar lucro residual como método relevante.

Elétricas:
- Priorizar DDM, Bazin, EV/EBITDA, dívida líquida/EBITDA.
- Avaliar concessões, revisão tarifária, CAPEX regulatório.
- Margem de segurança pode ser menor se receita for previsível.

Commodities:
- Normalizar lucro por ciclo.
- Não projetar último ano como recorrente.
- Usar EBITDA normalizado.
- Exigir margem de segurança maior.

Varejo:
- Priorizar margem, alavancagem, capital de giro, geração de caixa.
- Dividendos têm menor relevância.
- Exigir atenção alta à dívida e ciclo de juros.

Seguradoras:
- Priorizar P/VP, ROE, índice combinado, sinistralidade e lucro recorrente.

Holdings:
- Priorizar soma das partes.
```

---

## 4.6. `risk_rules.md`

Documento com regras automáticas de alerta.

Exemplo:

```text
Se Dívida Líquida/EBITDA > 3x:
- Marcar risco financeiro elevado.
- Aumentar taxa de desconto.
- Exigir margem de segurança maior.

Se payout > 100%:
- Marcar dividendo como potencialmente insustentável.

Se lucro líquido cresce, mas fluxo de caixa operacional cai:
- Marcar alerta de qualidade do lucro.

Se ROE alto ocorre com patrimônio líquido muito baixo:
- Marcar ROE possivelmente distorcido.

Se dividend yield alto veio de evento extraordinário:
- Não usar esse dividendo na média recorrente.

Se empresa teve prejuízo em vários anos:
- Não aplicar Graham de forma mecânica.
```

---

## 4.7. `output_template.md`

Documento com o formato do relatório final.

Deve padronizar a entrega para que toda análise tenha a mesma estrutura.

---

# 5. Workflow obrigatório da skill

## Etapa 1 — Receber input do usuário

A skill deve aceitar inputs simples:

```text
Analise CMIG4
```

Ou inputs completos:

```json
{
  "ticker": "CMIG4",
  "market": "B3",
  "focus": "dividends",
  "investment_horizon_years": 5,
  "required_return": 0.12,
  "desired_dividend_yield": 0.08,
  "margin_of_safety": 0.25
}
```

Se o usuário não informar premissas, a skill deve assumir defaults conservadores.

Defaults sugeridos:

```text
Horizonte de projeção: 5 anos
Cenários: conservador, base e otimista
Taxa de desconto inicial: Selic + prêmio de risco
Margem de segurança mínima: 20%
Yield desejado Bazin: 6%, 8%, 10% e 12%
Crescimento terminal: limitado por inflação + crescimento real conservador
```

---

## Etapa 2 — Identificar a empresa

A skill deve descobrir:

```text
Ticker
Nome da empresa
CNPJ
Código CVM
Setor B3
Subsetor
Segmento
Tipo de ação: ON, PN, Unit
Quantidade de ações
Free float
Site de RI
```

Output intermediário esperado:

```json
{
  "ticker": "CMIG4",
  "company_name": "Cemig",
  "cvm_code": "...",
  "sector": "Energia elétrica",
  "share_class": "PN",
  "currency": "BRL"
}
```

---

## Etapa 3 — Coletar dados

A skill deve coletar automaticamente:

```text
Cotação atual
Histórico de preço
Dividendos/JCP dos últimos 5 a 10 anos
DRE anual
DRE trimestral
Balanço patrimonial
DFC
Número de ações
Dívida bruta
Caixa
Dívida líquida
EBITDA
Lucro líquido
Patrimônio líquido
Receita
CAPEX
Depreciação e amortização
Fluxo de caixa operacional
Fluxo de caixa livre
Releases de resultados
Apresentações
Fatos relevantes
Guidance
Dados macroeconômicos
Pares do setor
```

A skill deve salvar os dados em uma estrutura intermediária.

Exemplo:

```json
{
  "years": [2020, 2021, 2022, 2023, 2024],
  "revenue": [],
  "ebitda": [],
  "net_income": [],
  "equity": [],
  "operating_cash_flow": [],
  "capex": [],
  "free_cash_flow": [],
  "dividends_paid": [],
  "shares_outstanding": []
}
```

---

## Etapa 4 — Validar qualidade dos dados

Antes de calcular valuation, a skill deve verificar:

```text
Os dados têm pelo menos 5 anos?
Há anos faltando?
Há mudança grande no número de ações?
Houve split ou grupamento?
O lucro é positivo?
O patrimônio líquido é positivo?
A empresa pagou dividendos recorrentes?
O fluxo de caixa operacional é compatível com lucro?
Há eventos não recorrentes?
```

Se a qualidade dos dados for baixa, a skill deve sinalizar:

```text
A confiabilidade da análise é baixa/média/alta.
```

---

## Etapa 5 — Normalizar dados financeiros

A skill precisa ajustar:

```text
Dividendos extraordinários
Lucros não recorrentes
Venda de ativos
Impairments
Reversões contábeis
Créditos tributários extraordinários
Multas ou acordos judiciais não recorrentes
Variações cambiais relevantes
Efeitos de M&A
Mudança de norma contábil
Split/grupamento
Inflação, quando necessário
```

Exemplo de regra:

```text
Se o lucro líquido teve crescimento forte, mas o release informa venda de ativo relevante, criar "lucro líquido ajustado".
```

A skill deve trabalhar com:

```text
Lucro líquido reportado
Lucro líquido ajustado
Dividendos reportados
Dividendos recorrentes
FCF reportado
FCF ajustado
```

---

# 6. Indicadores que a skill deve calcular

## 6.1. Indicadores por ação

```text
LPA = Lucro Líquido / Número de Ações
VPA = Patrimônio Líquido / Número de Ações
Dividendos por ação = Dividendos / Número de Ações
FCF por ação = FCF / Número de Ações
Receita por ação = Receita / Número de Ações
```

---

## 6.2. Indicadores de preço

```text
P/L = Preço Atual / LPA
P/VP = Preço Atual / VPA
Dividend Yield = Dividendo por Ação / Preço Atual
P/FCF = Preço Atual / FCF por Ação
EV/EBITDA = Enterprise Value / EBITDA
```

---

## 6.3. Indicadores de rentabilidade

```text
ROE = Lucro Líquido / Patrimônio Líquido
ROIC = NOPAT / Capital Investido
Margem Líquida = Lucro Líquido / Receita
Margem EBITDA = EBITDA / Receita
Margem FCF = FCF / Receita
```

---

## 6.4. Indicadores de dívida

```text
Dívida Líquida = Dívida Bruta - Caixa
Dívida Líquida/EBITDA
Dívida Líquida/Patrimônio Líquido
Cobertura de Juros = EBIT / Despesa Financeira
```

---

## 6.5. Indicadores de dividendos

```text
Payout = Dividendos / Lucro Líquido
Payout ajustado = Dividendos recorrentes / Lucro ajustado
Dividend Yield médio
Dividend Yield mediano
Crescimento dos dividendos
Anos com pagamento de dividendos
Estabilidade dos dividendos
```

---

# 7. Métodos de valuation obrigatórios

## 7.1. Benjamin Graham

Fórmula:

```text
Valor Intrínseco = √(22,5 × LPA × VPA)
```

Regras:

```text
Usar LPA ajustado quando houver lucro não recorrente.
Não aplicar se LPA for negativo.
Não aplicar se VPA for negativo.
Sinalizar baixa confiabilidade para empresas asset-light/growth.
```

Output:

```text
Valor Graham: R$ XX,XX
Preço atual: R$ XX,XX
Margem de segurança Graham: X%
Confiabilidade: baixa/média/alta
```

---

## 7.2. Décio Bazin

Fórmula:

```text
Preço Teto = Dividendo Médio Anual Recorrente / Yield Desejado
```

A skill deve calcular:

```text
Preço teto para yield de 6%
Preço teto para yield de 8%
Preço teto para yield de 10%
Preço teto para yield de 12%
```

Regras:

```text
Usar dividendos recorrentes.
Excluir dividendos extraordinários.
Não usar se a empresa não tiver histórico consistente de dividendos.
Calcular média e mediana.
Preferir mediana se houver outliers.
```

Output:

```text
Dividendo médio recorrente: R$ X,XX
Preço teto Bazin 6%: R$ XX,XX
Preço teto Bazin 8%: R$ XX,XX
Preço teto Bazin 10%: R$ XX,XX
Preço teto Bazin 12%: R$ XX,XX
```

---

## 7.3. Peter Lynch

Fórmula:

```text
Índice Lynch = (Crescimento Projetado do LPA + Dividend Yield) / P/L
```

Interpretação:

```text
< 1,0 = cara
1,0 a 1,5 = justa
1,5 a 2,0 = barata
> 2,0 = barganha
```

Regras:

```text
Usar crescimento conservador.
Para Brasil, priorizar projeção de 1 a 3 anos.
Não usar crescimento agressivo sem justificativa.
Usar dividend yield médio recorrente, não apenas o atual.
```

---

## 7.4. DDM/Gordon

Fórmula:

```text
Preço Justo = Dividendo Esperado / (Ke - g)
```

Regras:

```text
Usar apenas para empresas maduras e pagadoras consistentes de dividendos.
Ke precisa ser maior que g.
g não pode ser agressivo.
g terminal deve ser limitado por crescimento econômico/inflacionário sustentável.
```

Output:

```text
Dividendo esperado: R$ X,XX
Ke: X%
g: X%
Valor DDM: R$ XX,XX
```

---

## 7.5. DCF por FCFE

Fórmula:

```text
FCFE = Lucro Líquido
     + Depreciação e Amortização
     - CAPEX
     - Variação do Capital de Giro
     + Captação Líquida de Dívida
```

Desconto:

```text
Valor do Equity = Soma dos FCFE descontados + Valor Terminal descontado
Preço Justo = Valor do Equity / Número de Ações
```

Regras:

```text
Usar Ke como taxa de desconto.
Projetar 5 anos.
Criar cenário conservador, base e otimista.
Calcular valor terminal.
Aplicar margem de segurança.
```

---

## 7.6. DCF por FCFF

Fórmula:

```text
FCFF = EBIT × (1 - IR)
     + Depreciação e Amortização
     - CAPEX
     - Variação do Capital de Giro
```

Desconto:

```text
Valor da Firma = Soma dos FCFF descontados pelo WACC + Valor Terminal descontado
Valor do Equity = Valor da Firma - Dívida Líquida
Preço Justo = Valor do Equity / Número de Ações
```

Regras:

```text
Usar WACC.
Mais útil para empresas industriais, varejo, infraestrutura e serviços.
Menos útil para bancos.
```

---

## 7.7. Múltiplos comparativos

A skill deve comparar a empresa com pares do setor.

Múltiplos mínimos:

```text
P/L
P/VP
EV/EBITDA
Dividend Yield
ROE
ROIC
Margem EBITDA
Dívida Líquida/EBITDA
```

Output:

```text
A empresa negocia com desconto/prêmio em relação aos pares.
```

Exemplo:

```text
P/L da empresa: 6,5x
P/L médio dos pares: 8,0x
Desconto relativo: 18,75%
```

---

## 7.8. Reverse DCF

A skill deve calcular:

```text
Qual crescimento implícito justifica o preço atual?
```

Output:

```text
O preço atual implica crescimento médio de lucro/FCF de X% ao ano pelos próximos 5 anos.
```

Interpretação:

```text
Se o crescimento implícito for muito baixo, pode indicar oportunidade.
Se o crescimento implícito for muito alto, pode indicar expectativa agressiva.
```

---

## 7.9. Lucro residual

Obrigatório para bancos, seguradoras e financeiras.

Fórmula:

```text
Lucro Residual = Lucro Líquido - (Ke × Patrimônio Líquido)
```

Interpretação:

```text
Se positivo, a empresa gera valor acima do custo de capital.
Se negativo, destrói valor econômico.
```

---

## 7.10. Soma das partes — SOTP

Usar para:

```text
Holdings
Conglomerados
Empresas com negócios muito diferentes
Empresas com participações relevantes em outras companhias
```

Fórmula conceitual:

```text
Valor da operação A
+ Valor da operação B
+ Valor das participações
+ Caixa
- Dívida
= Valor justo do equity
```

---

# 8. Cálculo do preço teto

A skill deve gerar vários tipos de preço teto.

## 8.1. Preço teto Bazin

```text
Preço Teto Bazin = Dividendo Médio Recorrente / Yield Desejado
```

---

## 8.2. Preço teto por margem de segurança

```text
Preço Teto = Valor Justo × (1 - Margem de Segurança)
```

Exemplo:

```text
Valor justo: R$ 40,00
Margem de segurança: 25%
Preço teto: R$ 30,00
```

---

## 8.3. Preço teto projetivo

Esse deve ser um dos diferenciais da skill.

Fórmula conceitual:

```text
Preço Teto Projetivo =
Valor Justo Futuro Descontado para Hoje × (1 - Margem de Segurança)
```

Processo:

```text
1. Projetar lucro, dividendos ou FCFE para 5 anos.
2. Estimar valor justo da empresa no ano 5.
3. Trazer esse valor a valor presente pela taxa de desconto.
4. Aplicar margem de segurança.
```

Exemplo:

```text
Valor justo estimado em 5 anos: R$ 60,00
Taxa de desconto: 12% ao ano
Valor presente: R$ 34,05
Margem de segurança: 25%
Preço teto projetivo: R$ 25,54
```

---

# 9. Projeções ano a ano

A skill deve gerar projeções para pelo menos 5 anos.

Para cada ano:

```text
Receita
Crescimento da receita
EBITDA
Margem EBITDA
Lucro líquido
Margem líquida
LPA
Dividendos
Payout
FCFE
FCFF
Dívida líquida
Dívida líquida/EBITDA
ROE
ROIC
```

Formato:

```text
Ano 1:
- Receita: R$ X
- Crescimento: X%
- Lucro líquido: R$ X
- LPA: R$ X
- Dividendos por ação: R$ X
- FCFE: R$ X

Ano 2:
...
```

A skill deve explicar a origem das premissas:

```text
Histórico
Guidance
Média setorial
Crescimento do setor
Inflação
Ciclo econômico
Conservadorismo
```

---

# 10. Cenários obrigatórios

A skill deve sempre criar 3 cenários.

## 10.1. Cenário conservador

Características:

```text
Crescimento baixo
Margem pressionada
Payout menor
Taxa de desconto maior
Margem de segurança maior
```

---

## 10.2. Cenário base

Características:

```text
Crescimento próximo ao histórico ajustado
Margens normalizadas
Payout médio sustentável
Taxa de desconto padrão
```

---

## 10.3. Cenário otimista

Características:

```text
Crescimento acima da média
Margem melhorando
Dívida controlada
Payout sustentável
```

A skill nunca deve deixar o cenário otimista dominar o veredito. O preço teto deve ser baseado preferencialmente no cenário **base conservador**.

---

# 11. Taxa de desconto

## 11.1. Ke — custo do capital próprio

Usar para FCFE e DDM.

Modelo:

```text
Ke = Taxa livre de risco + Prêmio de risco
```

Versão mais completa:

```text
Ke = Rf + Beta × Prêmio de Mercado + Prêmio Brasil + Prêmio Específico
```

Para simplificação brasileira:

```text
Ke = Selic nominal + prêmio de risco da ação
```

A skill deve ajustar o prêmio de risco por:

```text
Setor
Alavancagem
Previsibilidade
Governança
Ciclicidade
Liquidez
Histórico de lucro
```

---

## 11.2. WACC

Usar para FCFF.

Fórmula:

```text
WACC = Ke × E/(D+E) + Kd × (1 - IR) × D/(D+E)
```

Onde:

```text
Ke = custo do capital próprio
Kd = custo da dívida
E = valor do equity
D = dívida
IR = imposto
```

---

# 12. Margem de segurança dinâmica

A skill deve sugerir margem de segurança conforme o risco.

Tabela inicial:

```text
Empresas muito previsíveis:
10% a 15%

Empresas maduras boas pagadoras de dividendos:
15% a 20%

Empresas cíclicas moderadas:
25% a 30%

Varejo, commodities, empresas alavancadas:
30% a 40%

Turnaround ou baixa previsibilidade:
40%+
```

Regras automáticas:

```text
Se Dívida Líquida/EBITDA > 3x:
+5% a +10% de margem exigida

Se payout > 100%:
+5% de margem exigida

Se lucro recorrente for duvidoso:
+10% de margem exigida

Se empresa for regulada e previsível:
pode reduzir margem exigida

Se empresa for commodity:
aumentar margem exigida
```

---

# 13. Qualidade do lucro

A skill deve gerar um bloco específico:

```text
Qualidade do lucro: alta/média/baixa
```

Critérios:

```text
Lucro acompanha caixa operacional?
Lucro depende de evento não recorrente?
Margem estável?
Receita cresce junto?
Há muitas reversões contábeis?
Há créditos tributários extraordinários?
Há venda de ativo relevante?
Há impairment?
Há ganho cambial relevante?
```

Alertas:

```text
Lucro líquido positivo, mas FCF negativo.
Lucro subiu por venda de ativo.
Dividendos pagos acima do lucro recorrente.
Margem líquida fora da média histórica.
```

---

# 14. Análise de dividendos

A skill deve calcular:

```text
Dividendos pagos por ano
Dividendos por ação
Dividend yield anual
Dividend yield médio
Dividend yield mediano
Payout médio
Payout ajustado
Dividendos recorrentes
Dividendos extraordinários
Crescimento dos dividendos
Anos sem pagamento
Estabilidade do dividendo
```

Classificação:

```text
Excelente pagadora
Boa pagadora
Pagadora irregular
Não adequada para dividendos
```

---

# 15. Yield seguro da empresa

A skill deve calcular um **yield seguro**, não apenas o yield atual.

Exemplo:

```text
Yield atual = 12%
Yield médio 5 anos = 8%
Yield recorrente ajustado = 7%
Yield seguro estimado = 6,5%
```

Regras:

```text
Excluir dividendos extraordinários.
Usar lucro recorrente.
Verificar payout sustentável.
Verificar fluxo de caixa.
Verificar dívida.
```

---

# 16. Yield on Cost projetado

A skill deve mostrar:

```text
Preço pago hoje: R$ XX
Dividendo esperado no ano 1: R$ X
Yield on cost ano 1: X%

Dividendo esperado no ano 5: R$ X
Yield on cost ano 5: X%
```

Fórmula:

```text
Yield on Cost Futuro = Dividendo Futuro por Ação / Preço Pago Hoje
```

---

# 17. Análise de sensibilidade

A skill deve gerar tabelas variando:

```text
Taxa de desconto
Crescimento terminal
Margem líquida
Payout
Crescimento do lucro
```

Tabela mínima:

```text
Sensibilidade DDM/DCF:

             g -1%      g base      g +1%
r -1%      R$ XX,XX   R$ XX,XX   R$ XX,XX
r base     R$ XX,XX   R$ XX,XX   R$ XX,XX
r +1%      R$ XX,XX   R$ XX,XX   R$ XX,XX
```

Também deve gerar:

```text
Sensibilidade do preço teto Bazin por yield desejado:

Yield desejado     Preço teto
6%                 R$ XX
8%                 R$ XX
10%                R$ XX
12%                R$ XX
```

---

# 18. Análise de riscos

A skill deve buscar e analisar riscos como:

```text
Risco regulatório
Risco cambial
Risco de juros
Risco de crédito
Risco de concessão
Risco de commodity
Risco político
Risco fiscal
Risco de governança
Risco de concorrência
Risco tecnológico
Risco de alavancagem
Risco de liquidez
Risco de queda de margem
Risco de dependência de poucos clientes
```

Para cada risco:

```text
Descrição
Impacto potencial
Probabilidade
Severidade
Como afeta o valuation
```

Formato:

```text
Risco: Vencimento de concessões
Impacto: Alto
Probabilidade: Média
Efeito no valuation: reduz crescimento terminal e aumenta taxa de desconto
```

---

# 19. Score final da empresa

A skill deve gerar um score de 0 a 100.

Sugestão de pesos:

```text
Qualidade do negócio: 20%
Rentabilidade: 15%
Geração de caixa: 15%
Dividendos: 15%
Endividamento: 15%
Preço/valuation: 15%
Riscos/governança: 5%
```

Classificação:

```text
85–100: Excelente
70–84: Boa
55–69: Mediana
40–54: Fraca
< 40: Evitar
```

---

# 20. Score de oportunidade

Separar qualidade da empresa de atratividade do preço.

Uma empresa pode ser:

```text
Excelente, mas cara
Mediana, mas muito barata
Boa, com preço justo
Fraca, mesmo parecendo barata
```

Score de oportunidade:

```text
Valuation relativo
Margem de segurança
Confluência entre métodos
Risco
Confiabilidade dos dados
```

---

# 21. Veredito final

A skill deve gerar um veredito assim:

```text
Veredito: Atrativa com margem de segurança moderada

Resumo:
A ação negocia a R$ XX,XX. O valor justo estimado no cenário base é R$ XX,XX, indicando desconto de X%. O preço teto conservador é R$ XX,XX. A empresa possui boa geração de caixa, dividendos recorrentes e dívida controlada. Os principais riscos são regulação, juros e necessidade de CAPEX.

Classificação:
- Qualidade da empresa: Boa
- Preço atual: Barato
- Risco: Médio
- Adequação: Dividendos + valor
- Confiança da análise: Média/Alta
```

---

# 22. Relatório final obrigatório

Estrutura sugerida:

```text
# Valuation de [TICKER] — [Nome da Empresa]

## 1. Resumo executivo
## 2. Dados da empresa
## 3. Fontes utilizadas
## 4. Cotação atual e visão geral
## 5. Diagnóstico fundamentalista
## 6. Qualidade do lucro
## 7. Dividendos e payout
## 8. Endividamento
## 9. Projeções ano a ano
## 10. Métodos de valuation
## 11. Análise de sensibilidade
## 12. Preço teto
## 13. Preço teto projetivo
## 14. Reverse DCF
## 15. Comparação com pares
## 16. Riscos
## 17. Score final
## 18. Veredito
## 19. Limitações da análise
```

---

# 23. JSON final estruturado

Além do relatório em Markdown, a skill deve gerar um JSON com os principais dados.

Exemplo:

```json
{
  "ticker": "CMIG4",
  "company_name": "Cemig",
  "current_price": 12.46,
  "fair_value_base": 23.96,
  "fair_value_conservative": 18.50,
  "fair_value_optimistic": 29.10,
  "suggested_ceiling_price": 17.30,
  "projected_ceiling_price": 20.42,
  "margin_of_safety": 0.32,
  "dividend_safe_yield": 0.065,
  "projected_yield_on_cost_year_5": 0.115,
  "quality_score": 78,
  "opportunity_score": 82,
  "risk_level": "medium",
  "verdict": "Atrativa com margem de segurança",
  "confidence": "medium_high"
}
```

---

# 24. Critérios de confiabilidade

A skill deve sempre declarar o nível de confiança:

```text
Alta
Média/Alta
Média
Média/Baixa
Baixa
```

A confiança depende de:

```text
Disponibilidade dos dados
Consistência histórica
Setor
Previsibilidade do negócio
Quantidade de premissas assumidas
Qualidade das fontes
Quantidade de eventos não recorrentes
```

Exemplo:

```text
Confiança: Média

Motivo:
A empresa possui dados históricos suficientes, mas o lucro recente foi impactado por itens não recorrentes e o setor apresenta volatilidade elevada.
```

---

# 25. Regras de segurança e honestidade

A skill deve seguir estas regras:

```text
Não inventar dados.
Não preencher lacunas como se fossem fatos.
Não dar recomendação direta de compra ou venda.
Não prometer retorno.
Não usar dividend yield extraordinário como recorrente.
Não usar apenas um método de valuation.
Não esconder baixa confiabilidade.
Não ignorar dívida.
Não ignorar qualidade do lucro.
Não ignorar riscos setoriais.
```

Quando faltar dado:

```text
Dado não encontrado.
Dado estimado.
Dado inferido.
Dado retirado de fonte auxiliar.
Dado confirmado em fonte oficial.
```

---

# 26. Implementação dos scripts

## 26.1. `fetch_market_data.py`

Responsável por:

```text
Buscar cotação atual
Buscar histórico de preços
Buscar histórico de dividendos
Ajustar splits/grupamentos
```

Output:

```json
{
  "current_price": 12.46,
  "price_history": [],
  "dividend_history": []
}
```

---

## 26.2. `fetch_cvm_data.py`

Responsável por:

```text
Buscar código CVM
Baixar DFP
Baixar ITR
Baixar documentos estruturados
Baixar fatos relevantes quando possível
```

---

## 26.3. `fetch_b3_data.py`

Responsável por:

```text
Buscar setor
Subsetor
Segmento
Tipo de ação
Dados cadastrais
```

---

## 26.4. `fetch_macro_data.py`

Responsável por:

```text
Selic
IPCA
CDI
Câmbio
Curva de juros, se disponível
```

---

## 26.5. `extract_pdf_tables.py`

Responsável por:

```text
Extrair tabelas de releases
Extrair guidance
Extrair dados financeiros de PDFs
Usar OCR como fallback
```

---

## 26.6. `normalize_financials.py`

Responsável por:

```text
Padronizar anos
Padronizar moeda
Calcular dados por ação
Remover não recorrentes
Ajustar dividendos extraordinários
Normalizar lucro cíclico
```

---

## 26.7. `detect_non_recurring_items.py`

Responsável por analisar releases e buscar termos como:

```text
não recorrente
extraordinário
venda de ativo
impairment
reversão
evento não caixa
crédito tributário
efeito cambial
provisão
acordo judicial
```

Output:

```json
{
  "non_recurring_items": [
    {
      "year": 2024,
      "description": "Venda de ativo relevante",
      "estimated_impact": 500000000,
      "confidence": "medium"
    }
  ]
}
```

---

## 26.8. `calculate_indicators.py`

Calcula todos os indicadores fundamentalistas.

---

## 26.9. `calculate_valuation.py`

Calcula:

```text
Graham
Bazin
Peter Lynch
DDM
DCF FCFE
DCF FCFF
Reverse DCF
Múltiplos
Lucro residual
SOTP, se aplicável
```

---

## 26.10. `calculate_sensitivity.py`

Gera tabelas de sensibilidade.

---

## 26.11. `generate_report.py`

Gera:

```text
Relatório Markdown
Resumo executivo
Tabelas
JSON final
```

---

## 26.12. `validate_output.py`

Verifica se o relatório final contém:

```text
Todos os métodos obrigatórios
Premissas explícitas
Fontes
Preço justo
Preço teto
Preço teto projetivo
Margem de segurança
Riscos
Limitações
Nível de confiança
```

---

# 27. Schema principal de entrada

```json
{
  "ticker": "string",
  "market": "B3",
  "analysis_focus": "dividends | value | growth | full",
  "investment_horizon_years": 5,
  "required_return": 0.12,
  "desired_dividend_yields": [0.06, 0.08, 0.10, 0.12],
  "margin_of_safety": 0.25,
  "use_official_sources_only": false,
  "generate_full_report": true
}
```

---

# 28. Schema principal de saída

```json
{
  "company": {},
  "data_quality": {},
  "financial_diagnosis": {},
  "dividends": {},
  "debt": {},
  "valuation": {
    "graham": {},
    "bazin": {},
    "peter_lynch": {},
    "ddm": {},
    "dcf_fcfe": {},
    "dcf_fcff": {},
    "multiples": {},
    "reverse_dcf": {}
  },
  "scenarios": {
    "conservative": {},
    "base": {},
    "optimistic": {}
  },
  "sensitivity": {},
  "risks": [],
  "scores": {},
  "verdict": {},
  "limitations": []
}
```

---

# 29. Prompt interno da skill

Esse é o texto central que eu colocaria no `SKILL.md`:

```markdown
Você é uma skill especializada em valuation fundamentalista de ações brasileiras listadas na B3.

Seu objetivo é analisar uma empresa usando dados públicos, preferindo fontes oficiais como CVM, B3, Banco Central, IBGE e site de RI da empresa.

Você deve executar uma análise completa, não apenas calcular fórmulas isoladas.

Workflow obrigatório:
1. Identifique corretamente a empresa, ticker, código CVM, setor e classe da ação.
2. Colete dados financeiros, cotações, dividendos, releases, guidance e dados macroeconômicos.
3. Valide a qualidade das fontes.
4. Normalize os dados antes de qualquer valuation.
5. Separe lucro reportado de lucro ajustado.
6. Separe dividendos recorrentes de dividendos extraordinários.
7. Calcule indicadores fundamentalistas.
8. Projete resultados ano a ano por pelo menos 5 anos.
9. Gere cenários conservador, base e otimista.
10. Calcule valuation por Graham, Bazin, Peter Lynch, DDM/Gordon, DCF FCFE, DCF FCFF, múltiplos comparativos e Reverse DCF.
11. Use métodos setoriais adicionais quando necessário, como lucro residual para bancos e soma das partes para holdings.
12. Gere análise de sensibilidade.
13. Calcule preço justo, preço teto e preço teto projetivo.
14. Analise riscos, endividamento, qualidade do lucro e sustentabilidade dos dividendos.
15. Entregue um relatório final em Markdown e um JSON estruturado.

Regras:
- Não invente dados.
- Declare quando um dado não foi encontrado.
- Declare quando uma premissa foi estimada.
- Não faça recomendação direta de compra ou venda.
- Não use dividendos extraordinários como recorrentes.
- Não use um único método como verdade absoluta.
- Sempre informe nível de confiança.
- Sempre informe limitações da análise.
```

---

# 30. Prompt de uso para o usuário

Exemplo simples:

```text
$valuation Faça o valuation completo de CMIG4 com foco em dividendos, preço teto Bazin, Graham, DCF e preço teto projetivo.
```

Exemplo avançado:

```text
$valuation Analise BBAS3 usando horizonte de 5 anos, retorno exigido de 12% ao ano, margem de segurança mínima de 25%, foco em dividendos e comparação com pares do setor bancário.
```

---

# 31. Critérios de aceite da skill

A skill só deve ser considerada pronta se conseguir entregar:

```text
1. Identificação correta da empresa.
2. Coleta de dados de fontes públicas.
3. Separação entre dado oficial, auxiliar, estimado e não encontrado.
4. Normalização de lucro e dividendos.
5. Cálculo de pelo menos 7 métodos de valuation.
6. Projeção ano a ano.
7. Cenários conservador, base e otimista.
8. Análise de sensibilidade.
9. Preço justo.
10. Preço teto.
11. Preço teto projetivo.
12. Riscos.
13. Score de qualidade.
14. Score de oportunidade.
15. Veredito final.
16. JSON estruturado.
17. Relatório em Markdown.
18. Declaração de limitações.
```

---

# 32. Plano de execução por fases

## Fase 1 — MVP da skill

Objetivo: fazer a skill funcionar sem automação pesada.

Entregas:

```text
SKILL.md
valuation_methods.md
formulas.md
output_template.md
Prompt interno completo
Relatório manual estruturado
Cálculo de Graham
Cálculo de Bazin
Cálculo de Peter Lynch
Cálculo de DDM
Cálculo de margem de segurança
```

Nessa fase, o agente pode usar dados fornecidos pelo usuário ou coletados manualmente.

---

## Fase 2 — Scripts de cálculo

Adicionar:

```text
calculate_indicators.py
calculate_valuation.py
calculate_sensitivity.py
generate_report.py
```

Com isso, a skill passa a gerar os cálculos de forma mais consistente.

---

## Fase 3 — Coleta de dados

Adicionar:

```text
fetch_market_data.py
fetch_cvm_data.py
fetch_b3_data.py
fetch_macro_data.py
etc...
```

Objetivo:

```text
Buscar dados financeiros automaticamente.
```

### 3.1 automaticamente descobrir/coletar:

Empresa
Código CVM
CNPJ
Setor
Subsetor
Ticker
Classe da ação
Relatórios CVM
DFP
ITR
FCA
FRE
Fatos relevantes
Releases de resultados
Apresentações
Histórico de dividendos
Cotação atual
Histórico de preço
Dados macroeconômicos
Pares do setor

Depois disso, ela deve transformar tudo em dados estruturados para alimentar os cálculos de valuation definidos anteriormente. O escopo original já deixa claro que a skill precisa acessar histórico de preços, relatórios públicos, calcular fluxo de caixa, lucro líquido projetado, payout, ROE, taxa de desconto, qualidade do lucro e preço teto projetivo

## 3.2 ordem de confiabilidade
1. CVM estruturada
2. B3
3. Site de RI da empresa
4. Fontes oficiais macroeconômicas
5. Provedores auxiliares de mercado
6. Sites agregadores

A regra principal:

Sempre que existir dado estruturado da CVM, a skill deve preferir esse dado em vez de tentar extrair o mesmo número de um PDF.

A CVM disponibiliza datasets de companhias abertas com arquivos em ZIP, TXT, CSV e ODS, incluindo cadastro, ITR, DFP, FRE, FCA e documentos periódicos/eventuais

3. Arquitetura recomendada da pipeline

Eu criaria os seguintes módulos/scripts:

scripts/
├── collectors/
│   ├── company_resolver.py
│   ├── cvm_collector.py
│   ├── b3_collector.py
│   ├── ri_crawler.py
│   ├── market_data_collector.py
│   └── macro_collector.py
├── parsers/
│   ├── cvm_statement_parser.py
│   ├── pdf_text_parser.py
│   ├── pdf_table_parser.py
│   ├── release_parser.py
│   └── document_classifier.py
├── normalizers/
│   ├── financial_statement_normalizer.py
│   ├── dividend_normalizer.py
│   ├── share_count_normalizer.py
│   ├── non_recurring_normalizer.py
│   └── inflation_adjuster.py
├── nlp/
│   ├── management_tone_analyzer.py
│   ├── guidance_extractor.py
│   ├── risk_extractor.py
│   ├── non_recurring_detector.py
│   └── covenant_detector.py
├── storage/
│   ├── document_store.py
│   ├── cache_manager.py
│   └── source_registry.py
└── pipeline/
    ├── run_collection_pipeline.py
    ├── validate_collected_data.py
    └── build_valuation_dataset.py

## 3.3 Normalização avançada

Essa é uma das partes mais importantes.

A skill deve transformar dados brutos em dados comparáveis.

Regra:

Usar demonstrações consolidadas como padrão.

Exceto quando:

Empresa não tiver consolidado
Banco/seguradora exigir tratamento específico
Holding exigir análise separada

A skill deve sempre informar:

Base usada: consolidado ou individual.

9.2. Anual versus trimestral

Para valuation:

DFP anual → base histórica principal.
ITR trimestral → tendência recente e atualização dos últimos 12 meses.

A skill deve calcular:

TTM — trailing twelve months
Último ano fiscal
Último trimestre
Variação YoY
Variação QoQ
---

## Fase 4 — Normalização e qualidade do lucro

Adicionar:

```text
normalize_financials.py
detect_non_recurring_items.py
```

Objetivo:

```text
Evitar valuation em cima de lucro inflado.
Separar dividendo recorrente de extraordinário.
```

---

## Fase 5 — Relatório avançado

Adicionar:

```text
Análise de riscos
Score de qualidade
Score de oportunidade
Comparação com pares
Reverse DCF
Preço teto projetivo
```

---

## Fase 6 — Testes e exemplos

Criar exemplos para:

```text
Empresa de dividendos: CMIG4, TAEE11, BBSE3
Banco: BBAS3, ITUB4
Commodity: VALE3, PETR4
Varejo: LREN3, MGLU3
Saneamento: SAPR11, SBSP3
Holding: Itaúsa, Bradespar
```

---

# 33. Testes que a skill precisa ter

## Teste 1 — Empresa pagadora de dividendos

A skill deve:

```text
Usar Bazin
Usar DDM
Calcular yield seguro
Calcular preço teto
Calcular yield on cost
```

---

## Teste 2 — Banco

A skill deve:

```text
Priorizar P/VP e ROE
Usar lucro residual
Não usar EV/EBITDA como principal
Analisar payout e Basileia se disponível
```

---

## Teste 3 — Commodity

A skill deve:

```text
Normalizar lucro
Exigir margem de segurança maior
Alertar sobre ciclo de commodity
Não projetar último ano como recorrente
```

---

## Teste 4 — Empresa sem lucro

A skill deve:

```text
Não aplicar Graham
Não aplicar P/L tradicional
Sinalizar baixa confiabilidade
Usar métodos alternativos, se fizer sentido
```

---

## Teste 5 — Dividend yield artificialmente alto

A skill deve:

```text
Detectar dividendo extraordinário
Não usar dividendo extraordinário no Bazin
Reduzir yield seguro
```

---

# 34. Ordem recomendada para criar a skill usando Codex

Eu faria nesta ordem:

```text
1. Criar a pasta valuation-br-stock/
2. Criar SKILL.md completo.
3. Criar references/formulas.md.
4. Criar references/valuation_methods.md.
5. Criar references/sector_rules.md.
6. Criar references/risk_rules.md.
7. Criar references/output_template.md.
8. Criar schemas/valuation_input.schema.json.
9. Criar schemas/valuation_output.schema.json.
10. Criar scripts/calculate_valuation.py.
11. Criar scripts/calculate_sensitivity.py.
12. Criar scripts/generate_report.py.
13. Criar exemplos manuais.
14. Testar com uma empresa simples.
15. Só depois adicionar scraping/coleta automática.
```

Eu evitaria começar pelo scraping. Primeiro vale garantir que a lógica da análise e dos cálculos está perfeita.

---

# 35. Comando/prompt para pedir ao Codex criar a skill

Você pode usar algo assim:

```text
Crie uma skill chamada valuation-br-stock para Codex.

A skill deve seguir a estrutura padrão de Agent Skills com um SKILL.md na raiz, arquivos de referência, schemas JSON, templates de relatório e scripts Python opcionais.

Objetivo:
Criar uma esteira completa de valuation fundamentalista para ações brasileiras da B3, com foco em preço justo, preço teto, preço teto projetivo, dividendos, margem de segurança, DCF, múltiplos, riscos e qualidade do lucro.

Implemente:
- SKILL.md completo
- references/formulas.md
- references/valuation_methods.md
- references/sector_rules.md
- references/risk_rules.md
- references/data_sources.md
- references/output_template.md
- schemas/valuation_input.schema.json
- schemas/valuation_output.schema.json
- scripts/calculate_valuation.py
- scripts/calculate_sensitivity.py
- scripts/generate_report.py
- examples/example_input.json
- examples/example_output.md

A primeira versão não precisa fazer scraping real. Ela deve aceitar dados estruturados em JSON e gerar os cálculos e relatório.

Depois que a base estiver pronta, vamos evoluir para coleta automática de CVM, B3, RI, Banco Central e dados de mercado.
```

---

# 36. Minha recomendação final de arquitetura

Eu criaria a skill em duas camadas:

## Camada 1 — Skill/instruções

Responsável por ensinar o Codex:

```text
Como pensar
Como analisar
Quais métodos usar
Como interpretar
Como escrever o relatório
Como evitar erros
```

## Camada 2 — Scripts determinísticos

Responsável por cálculos:

```text
Indicadores
Valuation
Sensibilidade
Scores
JSON final
```

Isso é importante porque:

```text
O agente é bom para análise, interpretação e busca.
Scripts são melhores para cálculo repetível e auditável.
```

A combinação ideal é:

```text
Codex/LLM:
- Buscar contexto
- Ler relatórios
- Interpretar riscos
- Identificar itens não recorrentes
- Escrever relatório

Scripts:
- Calcular indicadores
- Calcular valuation
- Gerar tabelas
- Validar outputs
```

---

# 37. Resultado esperado da skill pronta

Quando finalizada, a skill deve entregar algo nesse nível:

```text
CMIG4 está sendo negociada a R$ XX,XX.

O valor justo estimado no cenário base é R$ XX,XX.
O preço teto conservador é R$ XX,XX.
O preço teto Bazin para yield de 8% é R$ XX,XX.
O preço teto projetivo é R$ XX,XX.

A margem de segurança atual é de X%.

A empresa apresenta:
- Qualidade do lucro: média/alta
- Dividendos: bons, mas com necessidade de ajuste por eventos extraordinários
- Dívida: controlada/moderada/elevada
- Risco regulatório: relevante
- Confiança da análise: média/alta

Veredito:
Atrativa com margem de segurança moderada, desde que o investidor aceite os riscos regulatórios e acompanhe a sustentabilidade dos dividendos.
```


---

# 38. Planejamento de execução para completar a skill

Este plano transforma os 12 pontos pendentes em uma sequência de implementação. A ordem é importante: primeiro consolidar contratos e cálculos, depois normalização, depois coleta automática, e só então relatório avançado e testes setoriais completos.

## Fase 2.1 — Contratos de dados e schemas

Objetivo:

```text
Garantir que todos os dados usados pela skill tenham formato claro antes de ampliar os cálculos e a coleta.
```

Entregas:

```text
schemas/company_profile.schema.json
schemas/financials.schema.json
schemas/dividends.schema.json
schemas/market_data.schema.json
schemas/macro_data.schema.json
schemas/peer_group.schema.json
schemas/source_registry.schema.json
Atualização de valuation_input.schema.json
Atualização de valuation_output.schema.json
```

Critérios de aceite:

```text
Input completo validável por schema.
Output completo validável por schema.
Campos com classificação de fonte: oficial, auxiliar, estimado, inferido ou não encontrado.
Separação entre dados reportados, ajustados e normalizados.
```

---

## Fase 2.2 — Indicadores fundamentalistas

Objetivo:

```text
Criar uma camada dedicada para calcular indicadores antes do valuation.
```

Entregas:

```text
scripts/calculate_indicators.py
Indicadores por ação
Indicadores de preço
Indicadores de rentabilidade
Indicadores de dívida
Indicadores de dividendos
Indicadores de qualidade do lucro
```

Critérios de aceite:

```text
Calcular LPA, VPA, DPA, FCF por ação e receita por ação.
Calcular P/L, P/VP, P/FCF, dividend yield e EV/EBITDA.
Calcular ROE, ROIC, margem líquida, margem EBITDA e margem FCF.
Calcular dívida líquida, dívida líquida/EBITDA, dívida líquida/PL e cobertura de juros.
Calcular payout, payout ajustado, yield médio, yield mediano, crescimento e estabilidade dos dividendos.
```

---

## Fase 2.3 — Motor de valuation completo

Objetivo:

```text
Refatorar o valuation para usar indicadores, regras setoriais e métodos específicos de forma auditável.
```

Entregas:

```text
Refatoração de scripts/calculate_valuation.py
Módulos internos por método
Graham
Bazin
Peter Lynch
DDM/Gordon
DCF FCFE
DCF FCFF
Múltiplos comparativos
Reverse DCF
Lucro residual
SOTP
NAV
```

Critérios de aceite:

```text
Não aplicar Graham quando LPA ou VPA forem negativos.
Não usar EV/EBITDA como método principal para bancos.
Usar lucro residual para bancos, seguradoras e financeiras.
Usar SOTP para holdings e conglomerados quando houver dados.
Explicar confiabilidade de cada método.
Gerar valor justo por cenário e valor justo consolidado.
```

---

## Fase 2.4 — Preço teto, margem de segurança e desconto

Objetivo:

```text
Implementar regras completas para preço teto atual, preço teto projetivo e margem de segurança dinâmica.
```

Entregas:

```text
Preço teto Bazin por yields de 6%, 8%, 10% e 12%
Preço teto por margem de segurança
Preço teto projetivo
Ke por Selic + prêmio de risco
WACC
Margem de segurança dinâmica por risco e setor
```

Critérios de aceite:

```text
Preço teto projetivo calculado com valor justo futuro descontado para hoje.
Margem de segurança ajustada por previsibilidade, ciclicidade, dívida, payout e qualidade do lucro.
Taxa de desconto documentada no relatório.
WACC usado no FCFF quando houver estrutura de capital suficiente.
```

---

## Fase 2.5 — Sensibilidade e cenários

Objetivo:

```text
Tornar cenários e sensibilidade úteis para decisão, não apenas tabelas decorativas.
```

Entregas:

```text
Refatoração de scripts/calculate_sensitivity.py
Cenário conservador
Cenário base
Cenário otimista
Sensibilidade de DDM/DCF
Sensibilidade de Bazin
Sensibilidade de margem líquida
Sensibilidade de payout
Sensibilidade de crescimento do lucro
```

Critérios de aceite:

```text
Cenário otimista não pode dominar o veredito.
Preço teto deve usar cenário base conservador.
Tabela mínima r/g deve ser gerada.
Tabela Bazin por yield desejado deve ser gerada.
Premissas ano a ano devem aparecer no JSON e no Markdown.
```

---

## Fase 2.6 — Normalização financeira e qualidade do lucro

Objetivo:

```text
Evitar valuation sobre lucro inflado, dividendo extraordinário ou fluxo de caixa distorcido.
```

Entregas:

```text
scripts/normalize_financials.py
scripts/detect_non_recurring_items.py
Lucro líquido reportado
Lucro líquido ajustado
Dividendos reportados
Dividendos recorrentes
FCF reportado
FCF ajustado
Base consolidada ou individual
TTM
Último ano fiscal
Último trimestre
Variação YoY
Variação QoQ
```

Critérios de aceite:

```text
Detectar termos como não recorrente, extraordinário, impairment, venda de ativo, crédito tributário, reversão, provisão e acordo judicial.
Excluir dividendos extraordinários da média recorrente.
Sinalizar lucro positivo com FCF negativo.
Sinalizar payout acima de 100%.
Classificar qualidade do lucro como alta, média ou baixa.
```

---

## Fase 3 — Coleta automática de dados

Objetivo:

```text
Permitir que a skill descubra e colete dados públicos automaticamente, priorizando fontes oficiais.
```

Entregas:

```text
scripts/fetch_market_data.py
scripts/fetch_cvm_data.py
scripts/fetch_b3_data.py
scripts/fetch_macro_data.py
scripts/extract_pdf_tables.py
scripts/parse_financial_statements.py
scripts/collectors/company_resolver.py
scripts/collectors/cvm_collector.py
scripts/collectors/b3_collector.py
scripts/collectors/ri_crawler.py
scripts/collectors/market_data_collector.py
scripts/collectors/macro_collector.py
scripts/storage/source_registry.py
scripts/storage/cache_manager.py
```

Critérios de aceite:

```text
Identificar ticker, empresa, CNPJ, código CVM, setor, subsetor, segmento, classe da ação, free float e site de RI.
Coletar DFP, ITR, FCA, FRE e documentos relevantes quando disponíveis.
Coletar cotação, histórico de preço e dividendos.
Coletar Selic, IPCA, CDI e câmbio.
Registrar fonte, data de coleta, confiabilidade e status de confirmação.
Preferir CVM estruturada a PDF quando existir o mesmo dado.
```

---

## Fase 3.1 — Parsers e pipeline de dataset

Objetivo:

```text
Transformar dados brutos de CVM, B3, RI e mercado em dataset estruturado para valuation.
```

Entregas:

```text
scripts/parsers/cvm_statement_parser.py
scripts/parsers/pdf_text_parser.py
scripts/parsers/pdf_table_parser.py
scripts/parsers/release_parser.py
scripts/parsers/document_classifier.py
scripts/pipeline/run_collection_pipeline.py
scripts/pipeline/validate_collected_data.py
scripts/pipeline/build_valuation_dataset.py
```

Critérios de aceite:

```text
Gerar um valuation_input.json completo a partir da coleta.
Separar DFP anual de ITR trimestral.
Calcular TTM.
Marcar dados faltantes sem inventar valores.
Manter rastreabilidade de cada número relevante.
```

---

## Fase 4 — Riscos, setor e pares

Objetivo:

```text
Fazer a skill adaptar valuation, desconto, margem de segurança e riscos ao setor da empresa.
```

Entregas:

```text
Regras setoriais executáveis
Análise de pares
Múltiplos comparativos reais
Matriz de riscos
Extração de riscos em releases e documentos
scripts/nlp/risk_extractor.py
scripts/nlp/guidance_extractor.py
scripts/nlp/covenant_detector.py
scripts/nlp/management_tone_analyzer.py
```

Critérios de aceite:

```text
Bancos priorizam P/VP, ROE, payout e lucro residual.
Elétricas priorizam DDM, Bazin, EV/EBITDA e concessões.
Commodities usam lucro normalizado por ciclo.
Varejo aumenta peso de caixa, capital de giro e dívida.
Holdings usam SOTP.
Relatório mostra desconto ou prêmio contra pares.
Riscos têm descrição, probabilidade, impacto, severidade e efeito no valuation.
```

---

## Fase 5 — Score, veredito e relatório avançado

Objetivo:

```text
Gerar uma conclusão consistente, auditável e completa em Markdown e JSON.
```

Entregas:

```text
Score de qualidade da empresa
Score de oportunidade
Classificação de preço
Classificação de risco
Classificação de dividendos
Veredito final
Relatório Markdown completo
JSON final estruturado
Refatoração de scripts/generate_report.py
Refatoração de scripts/validate_output.py
```

Critérios de aceite:

```text
Score da empresa usa pesos: qualidade do negócio, rentabilidade, geração de caixa, dividendos, endividamento, valuation e riscos.
Score de oportunidade separa qualidade da empresa e atratividade do preço.
Veredito usa apenas: Evitar, Cara, Justa, Interessante, Atrativa com margem de segurança.
Relatório contém as 19 seções obrigatórias.
JSON contém todos os campos definidos no schema final.
Validação falha se faltar fonte, premissa, risco, preço teto, preço teto projetivo, confiança ou limitações.
```

---

## Fase 6 — Exemplos, testes e casos extremos

Objetivo:

```text
Provar que a skill funciona em setores e situações diferentes antes de considerar completa.
```

Entregas:

```text
examples/cmig4_example_input.json
examples/cmig4_example_output.md
examples/bbas3_example_input.json
examples/bbas3_example_output.md
examples/vale3_example_input.json
examples/vale3_example_output.md
examples/lren3_example_input.json
examples/lren3_example_output.md
examples/no_profit_example_input.json
examples/high_extraordinary_yield_example_input.json
Testes automatizados do fluxo
```

Critérios de aceite:

```text
Empresa pagadora de dividendos usa Bazin, DDM, yield seguro, preço teto e yield on cost.
Banco usa P/VP, ROE, payout e lucro residual.
Commodity normaliza lucro e exige margem maior.
Empresa sem lucro não aplica Graham nem P/L mecanicamente.
Dividend yield extraordinário não entra como recorrente.
Pipeline completa roda do input ao relatório validado.
```

---

## Ordem recomendada de implementação

```text
1. Schemas faltantes.
2. calculate_indicators.py.
3. Refatoração do calculate_valuation.py.
4. Preço teto, desconto e margem dinâmica.
5. Sensibilidade e cenários.
6. Normalização e qualidade do lucro.
7. Coleta automática inicial: mercado, CVM, B3 e macro.
8. Parsers e build_valuation_dataset.py.
9. Regras setoriais, pares e riscos.
10. Score, veredito e relatório avançado.
11. Exemplos setoriais.
12. Testes automatizados e validação final.
```

---

## Definição de pronto da skill completa

A skill só será considerada completa quando:

```text
Conseguir partir de um ticker simples.
Identificar a empresa corretamente.
Coletar dados públicos com rastreabilidade.
Validar e normalizar os dados.
Calcular indicadores e valuation multi-método.
Gerar cenários, sensibilidade, preço teto e preço teto projetivo.
Analisar dividendos, qualidade do lucro, endividamento, riscos e pares.
Gerar score de qualidade e score de oportunidade.
Entregar Markdown e JSON final.
Declarar confiança e limitações.
Passar nos testes de elétrica, banco, commodity, varejo, empresa sem lucro e dividend yield extraordinário.
```

---

# 39. Plano para atingir 90%+ do planning.md

Estado atual:

```text
Beta funcional.
Roda valuation com JSON estruturado.
Roda coleta automática para alguns tickers mapeados.
Baixa DFP estruturada da CVM.
Gera relatório validável para casos compatíveis, como CMIG4.
```

Meta desta etapa:

```text
Chegar a 90%+ do planning.md para empresas líquidas e cobertas por dados públicos estruturados.
O alvo não é perfeição para 100% das companhias da B3, mas cobertura robusta para os principais setores e tickers líquidos.
```

## Critério objetivo de 90%+

A skill deve conseguir, partindo apenas de um ticker:

```text
1. Resolver empresa, código CVM, CNPJ, setor, classe da ação e site de RI.
2. Coletar cotação e dividendos.
3. Baixar DFP e ITR da CVM.
4. Extrair DRE, balanço, DFC, composição de capital e TTM.
5. Normalizar lucro, FCF, dividendos e número de ações.
6. Detectar itens não recorrentes por textos de releases/notas quando disponíveis.
7. Calcular indicadores, cenários, valuation, sensibilidade, preço teto e preço teto projetivo.
8. Aplicar regras setoriais para elétrica, banco, seguradora, commodity, varejo, saneamento e holding.
9. Montar pares automaticamente para os setores principais.
10. Gerar relatório Markdown e JSON final.
11. Declarar fontes, limitações, dados faltantes e confiança.
12. Passar em testes online para pelo menos 12 tickers reais.
```

## Fora do escopo dos 90%

Estes itens ficam para a versão 100%:

```text
OCR avançado de PDF escaneado.
SOTP totalmente automatizado para qualquer holding complexa.
NAV automático para todos os ativos reais.
Cobertura perfeita de empresas ilíquidas, sem DFP consistente ou com estrutura atípica.
Modelos bancários com todos os detalhes regulatórios quando o dado não estiver estruturado.
```

---

## Fase 39.1 — Resolver qualquer ticker líquido da B3

Problema atual:

```text
A resolução depende de mapa local em KNOWN_B3_COMPANIES.
```

Entregas:

```text
scripts/collectors/b3_instruments_collector.py
scripts/storage/ticker_registry.py
schemas/ticker_registry.schema.json
references/ticker_resolution.md
```

Implementação:

```text
Criar registry local versionável com ticker, nome, CNPJ, código CVM, setor, subsetor, segmento, classe e RI.
Atualizar registry por fonte B3/CVM quando rede estiver disponível.
Usar fallback por mapa local apenas quando fonte oficial falhar.
Separar ticker de companhia, pois uma empresa pode ter ON, PN e UNIT.
```

Aceite:

```text
Resolver automaticamente pelo menos:
CMIG4, TAEE11, BBAS3, ITUB4, BBDC4, BBSE3, VALE3, PETR4, LREN3, MGLU3, SAPR11, SBSP3, ITSA4, BRAP4.
```

Prioridade:

```text
Alta.
Sem isso, a skill não escala para ticker simples.
```

---

## Fase 39.2 — CVM estruturada completa: DFP + ITR + TTM

Problema atual:

```text
A pipeline baixa DFP e extrai alguns campos anuais.
Ainda não usa ITR nem calcula TTM.
```

Entregas:

```text
scripts/collectors/cvm_itr_collector.py
scripts/parsers/cvm_itr_parser.py
scripts/parsers/cvm_capital_parser.py
scripts/parsers/cvm_financial_mapper.py
scripts/pipeline/build_ttm.py
```

Implementação:

```text
Expandir parser CVM para DFP e ITR.
Separar anual, trimestral, acumulado e TTM.
Extrair receita, EBIT, lucro, caixa, dívida, PL, FCO, CAPEX, FCF e ações.
Tratar contas diferentes para bancos/seguradoras.
Guardar account mapping por setor em references/cvm_account_mapping.md.
```

Aceite:

```text
Gerar histórico anual de 5 anos.
Gerar TTM quando ITR existir.
Não misturar acumulado trimestral com anual.
Marcar campo como nao_encontrado quando conta não existir.
```

Prioridade:

```text
Alta.
É a base do valuation automático confiável.
```

---

## Fase 39.3 — Dividendos oficiais e recorrência

Problema atual:

```text
Dividendos vêm de fonte auxiliar e podem não separar ordinário, JCP e extraordinário.
```

Entregas:

```text
scripts/collectors/dividend_collector.py
scripts/normalizers/dividend_recurrence_classifier.py
schemas/dividend_events.schema.json
references/dividend_policy.md
```

Implementação:

```text
Buscar proventos em fonte B3/CVM/RI quando disponível.
Usar Yahoo apenas como fallback auxiliar.
Classificar dividendo, JCP, restituição, amortização e extraordinário.
Normalizar por split/grupamento.
Calcular DPA recorrente, DPA reportado, payout ajustado e yield seguro.
```

Aceite:

```text
Bazin nunca usa evento extraordinário.
Yield seguro deve ser menor ou igual ao yield recorrente ajustado.
Relatório mostra origem dos dividendos e limitações.
```

Prioridade:

```text
Alta.
Sem isso, análises focadas em dividendos ainda ficam frágeis.
```

---

## Fase 39.4 — RI crawler e documentos públicos

Problema atual:

```text
ri_crawler.py apenas lista links de uma URL informada.
```

Entregas:

```text
scripts/collectors/ri_site_resolver.py
scripts/collectors/ri_document_collector.py
scripts/parsers/pdf_text_parser.py com extração real
scripts/parsers/pdf_table_parser.py com extração real opcional
scripts/parsers/release_parser.py melhorado
schemas/document_registry.schema.json
```

Implementação:

```text
Descobrir site de RI pelo cadastro CVM, registry ou busca fallback.
Baixar releases, apresentações, fatos relevantes e guidance.
Classificar documentos por tipo, ano e trimestre.
Extrair texto de PDF com biblioteca disponível.
Extrair tabelas quando dependência estiver instalada; senão marcar limitação.
```

Aceite:

```text
Para pelo menos CMIG4, BBAS3, VALE3 e LREN3, encontrar documentos de RI ou registrar falha rastreável.
Extrair texto suficiente para detectar riscos, guidance e itens não recorrentes.
```

Prioridade:

```text
Média/Alta.
Importante para qualidade do lucro, riscos e premissas.
```

---

## Fase 39.5 — Normalização avançada e qualidade do lucro

Problema atual:

```text
Normalização existe, mas ainda é simples.
```

Entregas:

```text
scripts/normalizers/non_recurring_normalizer.py completo
scripts/normalizers/cyclical_earnings_normalizer.py
scripts/normalizers/cash_earnings_reconciler.py
scripts/normalizers/share_adjustment_normalizer.py
references/earnings_quality_rules.md
```

Implementação:

```text
Separar lucro reportado, lucro ajustado, FCF reportado e FCF ajustado.
Detectar venda de ativo, impairment, reversão, crédito tributário, provisão e efeito cambial.
Comparar lucro com FCO e FCF.
Normalizar lucro cíclico para commodities.
Detectar ROE distorcido por PL baixo.
```

Aceite:

```text
Empresa com lucro positivo e FCF negativo gera alerta.
Dividend yield extraordinário é excluído.
Commodity não usa pico de ciclo como base recorrente.
Qualidade do lucro vira alta, média ou baixa com justificativa.
```

Prioridade:

```text
Alta.
É o principal diferencial de qualidade do valuation.
```

---

## Fase 39.6 — Regras setoriais executáveis

Problema atual:

```text
As regras setoriais estão documentadas, mas ainda pouco executáveis.
```

Entregas:

```text
scripts/sector_models/base.py
scripts/sector_models/banks.py
scripts/sector_models/utilities.py
scripts/sector_models/commodities.py
scripts/sector_models/retail.py
scripts/sector_models/insurance.py
scripts/sector_models/holdings.py
references/sector_model_weights.md
```

Implementação:

```text
Definir pesos por setor para cada método.
Bancos: P/VP, ROE, payout e lucro residual.
Elétricas: DDM, Bazin, EV/EBITDA, concessões e CAPEX regulatório.
Commodities: EBITDA/lucro normalizado e margem maior.
Varejo: capital de giro, caixa, dívida e juros.
Seguradoras: P/VP, ROE e lucro recorrente.
Holdings: SOTP quando dados existirem; senão desconto de holding declarado.
```

Aceite:

```text
O valor justo consolidado muda conforme setor.
O relatório explica quais métodos receberam maior peso.
EV/EBITDA não domina banco.
Commodity recebe margem de segurança maior.
```

Prioridade:

```text
Alta.
Sem isso, a skill calcula, mas não pensa setorialmente.
```

---

## Fase 39.7 — Pares automáticos e múltiplos comparativos

Problema atual:

```text
Pares só funcionam quando fornecidos no input.
```

Entregas:

```text
references/peer_groups.json
scripts/collectors/peer_group_collector.py
scripts/calculate_peer_multiples.py
schemas/peer_comparison.schema.json
```

Implementação:

```text
Criar peer groups iniciais por setor.
Coletar múltiplos dos pares pela própria pipeline quando possível.
Usar cache para evitar baixar os mesmos dados repetidamente.
Calcular desconto/prêmio relativo.
```

Aceite:

```text
CMIG4 compara com TAEE11, EGIE3, CPFE3 ou pares disponíveis.
BBAS3 compara com ITUB4, BBDC4, SANB11 quando disponíveis.
VALE3 compara com PETR4/CSNA3/GGBR4 apenas com ressalva de setor.
Relatório mostra múltiplos da empresa, média dos pares e desconto/prêmio.
```

Prioridade:

```text
Média/Alta.
Necessário para o planning, mas depende da robustez da coleta.
```

---

## Fase 39.8 — Relatório final com fonte, premissa e confiança

Problema atual:

```text
O relatório tem as seções obrigatórias, mas pode melhorar rastreabilidade e premissas.
```

Entregas:

```text
templates/full_report.md atualizado
scripts/generate_report.py com tabelas estruturadas
scripts/validate_output.py com validação de fontes e premissas
schemas/report_sections.schema.json
```

Implementação:

```text
Adicionar tabela de fontes por dado crítico.
Adicionar tabela de premissas ano a ano.
Adicionar explicação de pesos por método.
Adicionar bloco "dados não encontrados".
Adicionar bloco "dados estimados/inferidos".
Adicionar confiança por método e confiança geral.
```

Aceite:

```text
Relatório não pode passar se faltar preço justo, preço teto, preço teto projetivo, fontes, riscos, premissas e limitações.
Relatório precisa explicar por que o veredito foi gerado.
```

Prioridade:

```text
Média.
O motor precisa vir antes, mas o relatório é o produto final.
```

---

## Fase 39.9 — Testes online reais e forward-testing

Problema atual:

```text
Há testes locais; faltam testes online reais por setor.
```

Entregas:

```text
tests/run_online_collection_flow.py
tests/fixtures/expected_minimums.json
tests/run_sector_acceptance.py
```

Implementação:

```text
Testar coleta online real para 12 tickers.
Validar mínimo de anos financeiros, preço atual, ações, fontes e relatório.
Separar testes online dos testes offline.
Usar cache para reduzir instabilidade.
Forward-test com prompts reais usando a skill.
```

Tickers mínimos:

```text
CMIG4
TAEE11
BBAS3
ITUB4
BBSE3
VALE3
PETR4
LREN3
MGLU3
SAPR11
SBSP3
ITSA4
```

Aceite:

```text
Pelo menos 10 de 12 tickers geram relatório validável automaticamente.
Os 2 que falharem precisam falhar com motivo rastreável, não com exceção.
```

Prioridade:

```text
Alta para declarar 90%+.
Sem teste online multissetorial, a cobertura é presumida.
```

---

## Sequência recomendada de implementação

```text
1. Resolver ticker registry.
2. Expandir CVM DFP + ITR + TTM.
3. Implementar dividendos oficiais/recorrentes.
4. Implementar normalização avançada.
5. Implementar regras setoriais executáveis.
6. Implementar RI crawler/document registry.
7. Implementar pares automáticos.
8. Melhorar relatório e validação.
9. Criar testes online por setor.
10. Forward-test com prompts reais.
```

---

## Marcos de progresso

Marco 70%:

```text
Ticker simples funciona para 5 empresas mapeadas.
DFP anual funciona.
Relatório validável é gerado.
```

Marco 80%:

```text
Ticker registry cobre 12 empresas.
ITR/TTM funciona para empresas compatíveis.
Dividendos oficiais ou fallback rastreável.
Regras setoriais executáveis para elétrica, banco e commodity.
```

Marco 90%:

```text
10 de 12 tickers reais geram relatório automaticamente.
Relatório inclui fontes, premissas, riscos, dados faltantes e confiança.
Pares automáticos funcionam para pelo menos elétrica, banco e commodity.
Normalização avançada detecta não recorrentes em releases quando documentos forem encontrados.
```

Marco 95%:

```text
RI crawler encontra e processa documentos principais.
Setores adicionais cobertos: seguradoras, varejo, saneamento e holdings.
Testes online rodam com cache e critérios mínimos por setor.
```

---

## Ajustes de skill necessários

Para seguir as regras do skill-creator:

```text
Manter SKILL.md enxuto.
Mover detalhes longos para references/.
Manter scripts determinísticos para coleta, parsing, normalização, valuation e validação.
Evitar README, guia de instalação ou documentação duplicada.
Validar com quick_validate.py após cada fase.
Forward-testar antes de declarar 90%+.
```
