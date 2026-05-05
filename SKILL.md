---
name: valuation-br-stock
description: Analise fundamentalista e valuation de acoes brasileiras da B3 com preco justo, preco teto, preco teto projetivo, margem de seguranca, dividendos, DCF, Graham, Bazin, Peter Lynch, DDM, multiplos, reverse DCF, riscos e qualidade do lucro. Use quando o usuario pedir valuation de empresas brasileiras, analise de dividendos, comparacao de metodos, ou um relatorio estruturado em Markdown e JSON para tickers da B3 como CMIG4, BBAS3, TAEE11, VALE3 ou PETR4.
---

# Valuation BR Stock

Execute uma esteira de analise fundamentalista para acoes da B3. Priorize qualidade das premissas, rastreabilidade das fontes e honestidade sobre limites da analise.

## Use This Skill

Use esta skill quando o pedido envolver:

- valuation completo de uma acao brasileira
- preco justo, preco teto ou preco teto projetivo
- analise de dividendos, yield seguro ou yield on cost
- comparacao entre Graham, Bazin, DDM, DCF e multiplos
- diagnostico de qualidade do lucro, endividamento e riscos

Nao use esta skill para:

- recomendacao direta de compra ou venda
- day trade, analise tecnica ou timing de curto prazo
- ativos fora da B3 sem adaptar fontes, moeda e regras setoriais

## Workflow

Execute nesta ordem:

1. Identifique ticker, empresa, setor, classe da acao e horizonte pedido.
2. Classifique as entradas como `oficial`, `auxiliar`, `estimada`, `inferida` ou `nao encontrada`.
3. Valide cobertura historica, consistencia do numero de acoes, lucro, patrimonio, caixa e dividendos.
4. Normalize lucro, dividendos e fluxo de caixa antes de valorar.
5. Calcule indicadores e diagnostico fundamentalista.
6. Monte cenarios `conservative`, `base` e `optimistic`.
7. Rode valuation multi-metodo.
8. Gere preco justo, preco teto atual, preco teto projetivo, sensibilidade e veredito.
9. Entregue Markdown e JSON estruturado.

Para uso em CLIs de IA como Codex:

- trate o output JSON como artefato primario para validacao e regressao
- quando o usuario fixar cotacao, lucro projetado, FCL projetado ou margem, preserve esses overrides na analise
- prefira testes deterministas com fixtures locais para medir qualidade metodologica sem depender da rede

## Default Assumptions

Se o usuario nao informar premissas, assuma:

- horizonte de projecao: automatico por porte
  - `large_cap`: 3 anos
  - `small_cap`: 5 anos
- required return: `0.12`
- margem de seguranca minima: `0.20`
- yields Bazin: `0.06`, `0.08`, `0.10`, `0.12`
- cenarios: conservador, base e otimista
- crescimento terminal: conservador e inferior ao crescimento nominal agressivo de longo prazo
- crescimento de lucro e FCL:
- projete o ano corrente com taxa conservadora ou com override informado
  - do ano 2 em diante, faça convergencia gradual para inflacao de `5%` por padrao, sem colapsar todos os cenarios no mesmo ritmo
- taxa esperada de crescimento por Peter Lynch: `ROE * (1 - payout)`

Revise defaults usando [references/assumptions_policy.md](references/assumptions_policy.md) e [references/sector_rules.md](references/sector_rules.md).

## Source Policy

Priorize nesta ordem:

1. CVM
2. B3
3. RI da empresa
4. Banco Central, IBGE e outras fontes macro oficiais
5. provedores auxiliares de mercado
6. agregadores

Se um numero relevante vier de fonte auxiliar, tente confirmar em fonte oficial antes de tratá-lo como definitivo. Leia [references/data_sources.md](references/data_sources.md) quando precisar justificar confiabilidade.

## Normalization Rules

- Separe `reported` de `adjusted`.
- Exclua dividendos extraordinarios das medias recorrentes.
- Ajuste splits, grupamentos e mudancas relevantes no numero de acoes.
- Nao trate um ano excepcional de commodity ou venda de ativo como base recorrente.
- Sinalize baixa confiabilidade quando o valuation depender de muitas inferencias.
- Nunca invente dividendos a partir de payout arbitrario ou percentual fixo do lucro.
- Se faltarem dividendos ano a ano, so use media anual observada em anos com fonte.
- Se o numero de acoes por periodo nao puder ser reconciliado por fonte ou input estruturado confiavel, bloqueie valuation completo.

Regras detalhadas:

- [references/data_quality_policy.md](references/data_quality_policy.md)
- [references/risk_rules.md](references/risk_rules.md)
- [references/sector_rules.md](references/sector_rules.md)

## Method Selection

Sempre considere:

- Graham
- Bazin
- Peter Lynch
- DDM/Gordon
- DCF FCFE
- DCF FCFF
- multiplos comparativos
- reverse DCF

Adicione quando aplicavel:

- lucro residual para bancos, seguradoras e financeiras
- SOTP para holdings e conglomerados
- NAV ou regras setoriais especificas
- FCL como ancora principal para empresas intensivas em capital e com geracao de caixa mais informativa que o lucro contabil, como papel e celulose, utilities operacionais e negocios industriais/regulados

Consulte [references/valuation_methods.md](references/valuation_methods.md) e [references/formulas.md](references/formulas.md).

## Quality Gates

Antes de concluir:

- declare `skill_version` e `engine_version` no Markdown e no JSON final
- declare `valuation_status` como `complete` ou `partial`
- declare `confidence`
- liste dados faltantes e inferencias
- explique premissas por ano
- mostre riscos que alteram desconto, crescimento ou payout
- mostre payout medio de 5 e 10 anos quando houver historico suficiente
- mostre ROE atual, ROE projetado e crescimento esperado por Peter Lynch
- nao esconda conflito entre metodos
- trate `preco teto projetivo` como preco presente de entrada, nao como alvo futuro bruto

Se os dados forem insuficientes, entregue analise parcial e diga explicitamente o que faltou.

## Output Contract

O relatorio em Markdown deve seguir [references/output_template.md](references/output_template.md). O JSON deve respeitar:

- [schemas/valuation_input.schema.json](schemas/valuation_input.schema.json)
- [schemas/valuation_output.schema.json](schemas/valuation_output.schema.json)
- [schemas/report.schema.json](schemas/report.schema.json)

Use os scripts quando houver dados estruturados:

- `scripts/analyze_ticker.py`
- `scripts/normalize_financials.py`
- `scripts/detect_non_recurring_items.py`
- `scripts/calculate_indicators.py`
- `scripts/calculate_valuation.py`
- `scripts/calculate_sensitivity.py`
- `scripts/generate_report.py`
- `scripts/validate_output.py`

Use a pipeline quando o usuario pedir coleta automatica:

- `scripts/analyze_ticker.py` para executar ticker -> coleta -> valuation -> relatorio
- `scripts/pipeline/run_collection_pipeline.py`
- `scripts/pipeline/build_valuation_dataset.py`
- `scripts/pipeline/build_ttm.py`
- `scripts/pipeline/validate_collected_data.py`

Use coletores/parsers conforme a fonte:

- resolucao de ticker: `scripts/collectors/company_resolver.py`, `scripts/storage/ticker_registry.py`
- CVM: `scripts/fetch_cvm_data.py`, `scripts/parsers/cvm_statement_parser.py`, `scripts/parsers/cvm_itr_parser.py`, `scripts/parsers/cvm_capital_parser.py`
- B3/cadastro: `scripts/fetch_b3_data.py`, `scripts/collectors/b3_instruments_collector.py`
- mercado e dividendos: `scripts/fetch_market_data.py`, `scripts/fetch_dividend_data.py`
- dividendos oficiais e reconciliacao: `scripts/collectors/dividends/official_dividend_collector.py`, `scripts/collectors/dividends/cvm_ipe_dividend_collector.py`, `scripts/collectors/dividends/b3_cash_dividend_form_collector.py`, `scripts/collectors/dividends/ri_dividend_collector.py`, `scripts/collectors/dividends/dividend_reconciler.py`
- macro: `scripts/fetch_macro_data.py`
- pares: `scripts/collectors/peer_group_collector.py`, `scripts/calculate_peer_multiples.py`
- RI/PDF/releases: `scripts/collectors/ri_site_resolver.py`, `scripts/collectors/ri_document_collector.py`, `scripts/collectors/ri_crawler.py`, `scripts/parsers/release_parser.py`, `scripts/extract_pdf_tables.py`
- qualidade do lucro e custo de capital: `scripts/quality/quality_of_earnings.py`, `scripts/valuation/discount_rate_builder.py`, `scripts/valuation/method_role_selector.py`, `scripts/valuation/validate_valuation_sanity.py`

Capacidade automatica atual:

- Para tickers mapeados em `references/ticker_registry.json`, a pipeline resolve empresa, codigo CVM, setor, classe, RI, DFP, ITR, cotacao, dividendos auxiliares, macro e pares setoriais mapeados.
- Para tickers B3 validos fora do registry local, a pipeline deve tentar resolucao auxiliar de perfil/codigo CVM e entao confirmar/enriquecer com CVM quando possivel.
- Quando a CVM/B3/RI ou provedor auxiliar falhar, o output deve manter dados parciais, marcar a fonte como `not_found` ou `auxiliar` e declarar a limitacao.
- Comparacao com pares e RI ainda dependem da disponibilidade de documentos e multiplos coletaveis; nao invente multiplos ausentes.
- Yahoo Finance nao deve ser usado por padrao. Consulte `config/defaults.json`; `allow_yahoo_fallback` fica `false` por default.
- Brapi gratuita e scraping de agregadores sao apenas fallback. Dividendos oficiais CVM/B3/RI devem vir antes e a reconciliacao final precisa registrar divergencias e confianca.

## Script Workflow

Quando os dados de entrada estiverem em JSON:

1. Valide contra `schemas/valuation_input.schema.json`.
2. Rode `normalize_financials.py`.
3. Rode `calculate_indicators.py`.
4. Rode `calculate_valuation.py` para diagnostico e metodos.
5. Rode `calculate_sensitivity.py` para matrizes de sensibilidade.
6. Rode `generate_report.py` para montar Markdown e JSON final.
7. Rode `validate_output.py` para conferir completude.

Quando o usuario informar apenas um ticker:

1. Rode `scripts/analyze_ticker.py <TICKER>`.
2. Grave os relatorios de suporte em `~/.valuation-stock-br/` por padrao:
   - `<ticker>-analysis.json`
   - `<ticker>-report.md` quando `ok=true`
   - `cache/` para documentos CVM/B3 baixados pela pipeline
3. Se `ok` for `true`, entregue o `report.markdown` e destaque as fontes/limitacoes.
4. Se `ok` for `false`, entregue o dataset parcial ou relatorio parcial, explique quais fontes falharam e solicite os dados faltantes.

Quando o usuario informar um caso de teste com premissas fechadas:

1. monte um fixture local com a cotacao fixada
2. aplique `projection_policy` e `projection_overrides` no input
3. valide:
   - setor escolhido
   - porte inferido (`large_cap` ou `small_cap`)
   - horizonte automatico
   - payout medio 5y e 10y
   - ROE projetado
   - crescimento por Peter Lynch
   - preco teto base
   - preco teto projetivo por lucro e por FCL quando ambos fizerem sentido

Politica de reutilizacao:

- Relatorios de suporte (`*-analysis.json` e `*-report.md`) sao sobrescritos a cada nova analise do mesmo ticker, para evitar entregar valuation antigo como se fosse atual.
- O cache bruto em `~/.valuation-stock-br/cache/` pode ser reutilizado quando o arquivo baixado ja existir, especialmente zips historicos da CVM.
- Para preservar uma analise antiga, copie ou renomeie o arquivo antes de executar novamente.

## Reporting Rules

- Sempre mostre a versao no `Resumo executivo` e em `Cotacao atual e visao geral`:
  - `Versao da skill: valuation-br-stock`
  - `Versao do motor: <calculation_metadata.engine_version ou nao informada>`
- Classifique a oportunidade como `Evitar`, `Cara`, `Justa`, `Interessante` ou `Atrativa com margem de seguranca`.
- Separe qualidade da empresa de atratividade do preco.
- Nao faca promessa de retorno.
- Nao chame dividendo extraordinario de recorrente.
- Nao use um unico metodo como verdade absoluta.

Veja exemplos em [references/examples.md](references/examples.md) e [examples/example_input.json](examples/example_input.json).
