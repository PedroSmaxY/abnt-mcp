# Changelog

Todas as alterações relevantes, evoluções normativas (ABNT/IBGE) e novas interfaces MCP deste projeto são obrigatoriamente documentadas neste arquivo.

O formato baseia-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e este projeto adere ao [Versionamento Semântico (SemVer)](https://semver.org/lang/pt-BR/) governado por **Desenvolvimento Orientado a Especificações (*Spec-Driven Development* — SDD)**.

> **Regra de Governança SDD:** Nenhuma alteração em `src/` ou `specs/` pode ser mesclada à `main` sem o respectivo registro neste `CHANGELOG.md`. O teste automatizado `test_sdd_release_version_changelog_and_privacy_invariants` em `tests/test_sdd.py` e a pipeline de CI validam esta paridade.

---

## [Unreleased]

### Adicionado
- **Nova Regra Normativa `NBR14724-R04` e Ferramenta `format_equation` (ABNT NBR 14724 item 5.9):**
  - Cadastro da regra `NBR14724-R04` no catálogo normativo (`specs/01-normative-catalog.spec.md` e `config.py`).
  - Implementação da ferramenta FastMCP `@mcp.tool format_equation` (`server.py`, `pillars/writing.py`, `models.py`), gerando snippets prontos para Typst, LaTeX e Markdown.
  - Formatação com centralização da equação, numeração consecutiva entre parênteses alinhada à margem direita e definição de variáveis iniciada por "onde:" sem recuo de parágrafo (`first-line-indent: 0cm`) por constituir continuação sintática da sentença matemática.
- **Calibração Matemática do Espaçamento Entrelinhas (ABNT NBR 14724 item 5.2):**
  - Calibração analítica da distância baseline-to-baseline (20,685 pt no Word 1,5) implementando `leading: 1.061em` no corpo do texto e `leading: 0.49em` para espaçamento simples (Folha de Rosto, Folha de Aprovação, Resumo e Abstract) em `spec.py` e `templates/typst.py`.
- **Respiro Normativo dos Títulos de Seção (ABNT NBR 14724 item 5.2.2):**
  - Ajuste dos espaçamentos verticais de headings: títulos primários com `v(1.0cm)` antes e `v(0.8cm)` depois (respiro de 1 linha de 1,5), e secundários com `v(0.8cm)` antes e `v(0.6cm)` depois em `spec.py` e `templates/typst.py`.
- **Diagramação e Blindagem Anti-Órfãos para Figuras e Tabelas (ABNT NBR 14724 item 5.8):**
  - Adição de `#show figure: set block(spacing: 1.2cm)` e `#show figure.caption: set text(size: 10pt)` nos templates Typst.
  - Envolvimento dos snippets Typst emitidos por `format_figure_abnt` e `format_table_abnt` em `#block(breakable: false)` para impedir quebras de página entre a ilustração/tabela e sua respectiva fonte.
- **Suporte a Cidade/Local Dinâmica no Perfil e Rodapé (`models.py`, `pdf_reader.py` e `spec.py`):**
  - Adicionado campo `city: str | None` no modelo `NormativeProfile`.
  - Extração automática da cidade/local das últimas linhas da Capa (linha adjacente ao ano de publicação) em `infer_institutional_profile_from_pdf`.
  - Substituição do texto fixo `"BRASIL"` na Capa e Folha de Rosto por `{(spec.profile.city or 'CIDADE - UF').upper()}` em Typst, LaTeX e Markdown.
- **Lista de Siglas com Diagramação Fluida em `#grid` (`spec.py` e `typst.py`):**
  - Substituição da tabela de siglas de vão fixo (`2.5cm`) por `#grid(columns: (auto, 1fr), column-gutter: 1.2em, row-gutter: 1em, ...)` com travessão (`--`), adaptando-se harmonicamente à largura de cada sigla conforme a ABNT NBR 14724.
- **Listas Pré-Textuais Reativas no Typst (`src/abnt_mcp/pillars/spec.py` e `src/abnt_mcp/templates/typst.py`):**
  - Implementação de blocos reativos com introspecção `#context query(figure.where(...))` para Lista de Ilustrações (`kind: image`), Lista de Tabelas (`kind: table`) e Lista de Quadros (`kind: "quadro"`). As listas materializam-se automaticamente apenas se o documento contiver itens correspondentes, com pontilhado e número de página exato, prevenindo páginas em branco ou listas vazias com títulos órfãos (ABNT NBR 14724 itens 5.6 e 5.7).
- **Invariantes de Diagramação ABNT no Typst (`spec.py` e `typst.py`):**
  - Quebra obrigatória de página em seções primárias via `#show heading.where(level: 1): it => { pagebreak(weak: true); v(1.5cm); it; v(1.5cm) }` (NBR 14724 item 5.2.1), impedindo que capítulos como Conclusão sejam colados no final do capítulo anterior.
  - Posicionamento de identificação (legenda) de figuras, tabelas e quadros sempre no topo via `#show figure: set figure.caption(position: top)` (NBR 14724 item 5.8 e Normas Tabulares do IBGE de 1993).
  - Recuo de primeiro parágrafo ABNT de 1,25 cm forçado em todos os parágrafos inclusive após headings com `#set par(first-line-indent: (amount: 1.25cm, all: true))`.
  - Calibração do entrelinhas 1,5 real ABNT para Typst com `#set par(leading: 0.75em)`.
- **Suporte Nativo a Quadros no Typst (`src/abnt_mcp/pillars/writing.py`):**
  - O utilitário `format_table_abnt` agora emite `kind: "quadro"` e `supplement: [Quadro]` no snippet Typst quando `category == "quadro"`, diferenciando a numeração e a legenda de Quadros em relação a Tabelas.
- **Injeção Dinâmica de Elementos Pré-Textuais Institucionais no Scaffold (`src/abnt_mcp/pillars/spec.py`):**
  - Implementação do gerador `_render_dynamic_pre_textual` que injeta automaticamente os 9 elementos pré-textuais do catálogo (`ficha catalografica`, `folha de aprovacao`, `dedicatoria`, `agradecimentos`, `epigrafe`, `lista de ilustracoes`, `lista de tabelas`, `lista de quadros` e `lista de abreviaturas`) nos esqueletos `typst`, `latex` e `markdown` gerados por `scaffold_academic_project`, respeitando a ordem canônica da ABNT NBR 14724:2011 e blindando contra numeração de página visível nas folhas pré-textuais (`NBR14724-R02`).
- **Paridade de Detecção Pré-Textual (`src/abnt_mcp/pillars/diagnostics.py`):**
  - Inclusão de `"ficha catalografica"` e `"lista de quadros"` em `OPTIONAL_ELEMENTS` e `ELEMENT_PATTERNS` para paridade integral entre `check_structure`, `extract_institutional_pattern_from_pdf` e `audit_research_spec`.

### Corrigido
- **Correção Estrutural das Bordas da Tabela IBGE (`src/abnt_mcp/pillars/writing.py`):**
  - Substituição da regra anterior de stroke por coordenadas de célula que zerava as bordas da coluna 0 pelo stroke canônico das Normas Tabulares do IBGE (1993 / `IBGE1993-R01`): linhas horizontais no topo (`0.8pt`), abaixo do cabeçalho (`0.5pt`) e fechamento da base (`0.8pt`), com laterais e divisórias verticais internas abertas (`left: none, right: none`).
- **Eliminação de Vão Excessivo entre Ilustrações/Tabelas e a "Fonte:" (`src/abnt_mcp/pillars/spec.py`, `src/abnt_mcp/templates/typst.py` e `src/abnt_mcp/pillars/writing.py`):**
  - Remoção de `#show figure: set block(spacing: 1.2cm)` do preâmbulo geral que afastava a indicação de `Fonte:` da imagem/tabela.
  - Transferência do respiro normativo de 1,2 cm para o contêiner envoltório `#block(spacing: 1.2cm, breakable: false)` e acoplamento imediato da linha de fonte com `#v(0.2cm)` (ABNT NBR 14724 item 5.8).
- **Legenda Compacta pós-Equação (`src/abnt_mcp/pillars/writing.py`):**
  - Estruturação da oração explicativa de variáveis introduzida por "onde:" em fonte 10pt, entrelinha simples (`leading: 0.49em`) e recuo suave dos itens com `#h(0.5cm)` (ABNT NBR 14724 item 5.9 e `NBR14724-R04`).
- **Lista de Siglas Direta sem Grid Artificial (`src/abnt_mcp/pillars/spec.py`):**
  - Substituição do `#grid` de 2 colunas por linhas diretas alinhadas à esquerda com recuo zero e travessão colado (`*SIGLA* -- Descrição \`), eliminando vãos horizontais excessivos.
- **Blindagem Anti-Contaminação do Cabeçalho da Capa (`src/abnt_mcp/parsers/pdf_reader.py`):**
  - Remoção da captura genérica por caixa alta em `infer_institutional_profile_from_pdf` que incluía erroneamente nomes de autores e títulos em caixa alta no cabeçalho da universidade, restringindo a detecção a palavras-chave estritamente institucionais e interrompendo a leitura imediatamente caso linhas não institucionais sejam encontradas.
- **Delimitação da Varredura Pré-Textual em PDFs (`src/abnt_mcp/parsers/pdf_reader.py`):**
  - Interrupção da busca por elementos pré-textuais em `extract_institutional_pattern_from_pdf` assim que o `Sumário` ou a primeira seção textual (`Introdução`) é atingida, evitando falsos-positivos quando termos como `"Lista de Tabelas"` são mencionados no corpo do texto.

### Alterado
- Refatoração do `CLAUDE.md` para atuar como apontador canônico direto para o `AGENTS.md` (Fonte Única da Verdade para governança SDD e regras normativas), mantendo apenas comandos rápidos de desenvolvimento e eliminando duplicação de regras.

---

## [0.2.0] - 2026-10-24

### Adicionado
- **Arquitetura Spec-Driven Development (`PR #1`):**
  - Diretório `specs/` contendo a Fonte Única da Verdade: `01-normative-catalog.spec.md` (13 cláusulas canônicas `NORMATIVE_RULES`), `02-research-spec-schema.spec.md` (`ResearchSpec` em 3 camadas) e `03-mcp-tools-contract.spec.md`.
  - Motor SDD (`src/abnt_mcp/pillars/spec.py`) com geração e leitura de `abnt.spec.json` e `SPEC.md`.
  - Ferramentas MCP `init_research_spec`, `audit_research_spec` e `simulate_banca`, além dos recursos `abnt://guia/sdd` e `abnt://template/spec`.
  - Suporte nativo ao perfil de Artigos Científicos Periódicos segundo a **ABNT NBR 6022:2018** (`NBR6022-R01`).
  - Documentos de governança técnica e instruções para agentes de IA: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` e templates estruturados em `.github/ISSUE_TEMPLATE/`.
- **Segurança de I/O, Ano Dinâmico e Backup de `.bib` (`PR #2`):**
  - Utilitários `get_current_year()`, `get_default_author_source()` e `validate_safe_path()` (prevenção de *Path Traversal*) em `src/abnt_mcp/config.py`.
  - Criação automática de backup em `.abnt-mcp/backups/<nome>.bib.bak` antes de higienizar arquivos BibTeX em `clean_bibtex_file`.
- **Modelo Unificado de Diagnóstico (`PR #3`):**
  - Modelo `DiagnosticItem` em `src/abnt_mcp/models.py` diferenciando regras normativas (`nature="normative"`, `human_review_required=False`), diretrizes institucionais (`nature="institutional"`) e heurísticas editoriais (`nature="heuristic"`, `human_review_required=True`).
- **Scaffolding de Projetos e Aprendizado de Padrão/Logo Institucional via PDF (`PR #4`):**
  - Ferramenta MCP `scaffold_academic_project` para inicialização completa de projetos em `typst`, `latex` e `markdown` com proteção `overwrite=False`.
  - Extrator `extract_institutional_pattern_from_pdf` em `src/abnt_mcp/parsers/pdf_reader.py` capaz de aprender cabeçalho da capa, preâmbulo, orientador, elementos pré-textuais exigidos, rótulo de conclusão e extrair automaticamente o brasão/logotipo (`/XObject /Image`) da Capa (Página 1) para `figuras/logo_instituicao.png` usando apenas a biblioteca padrão.
- **Auditoria de Figuras, Tabelas e Quadros (`PR #5`):**
  - Ferramenta MCP `audit_illustrations_and_tables` (`audit_project_illustrations_and_tables` em `src/abnt_mcp/pillars/diagnostics.py`) validando chamada prévia no texto (`NBR14724-R03`), presença obrigatória de `Fonte:` (`NBR14724-R03`), existência física de imagens, sequência numérica e distinção conceitual entre `Tabela` e `Quadro` (`IBGE1993-R01`).
- **Auditoria SDD Integrada, Prontidão de Entrega e Relatórios Persistentes (`PR #6`):**
  - Evolução de `audit_research_spec` com indicador `submission_readiness` (`"READY"`, `"READY_WITH_WARNINGS"`, `"NOT_READY"`), validação das regras institucionais (`INST-PROFILE-*`) e geração automática de `.abnt-mcp/last-audit.json` e `.abnt-mcp/relatorio-conformidade.md`.

### Alterado
- Substituição de anos fixos (`"2026"`) em `format_figure` e `format_table` por obtenção dinâmica do ano corrente (`get_current_year()`).
- Remoção de campo de e-mail pessoal em `authors` no `pyproject.toml` (prevenção de spam conforme PEP 621) e adição de links oficiais em `[project.urls]`.

---

## [0.1.0] - 2026-10-24

### Adicionado
- Lançamento fundacional do servidor FastMCP `abnt-mcp` estruturado em 4 pilares (`diagnostics`, `writing`, `compiler`, `advisory`).
- Validação estrutural ABNT NBR 14724:2011 e auditoria forense de paginação em PDF (`audit_pdf_pagination`).
- Formatação e validação de citações conforme ABNT NBR 10520:2023 (autoria em caixa mista entre parênteses) e referências conforme ABNT NBR 6023:2018.
- Compilação multi-engine (`typst` nativo em Rust, `pdflatex`/`latexmk` com `abnTeX2` e `pandoc`).
- Integração com APIs científicas abertas Crossref, SciELO e resolução de BibTeX por DOI.
