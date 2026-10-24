# ABNT Copilot MCP

**Servidor Model Context Protocol para Padronização, Auditoria e Conformidade Documental Acadêmica (ABNT/IBGE)**

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-4.1.3-green)](https://gofastmcp.com)
[![ABNT Standard](https://img.shields.io/badge/ABNT-NBR%2014724%20%7C%2010520%20%7C%206023%20%7C%206022-darkred)](https://www.abnt.org.br/)
[![License: MIT](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-69%20passed-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-83%25-brightgreen)](tests/)
[![CI/CD](https://github.com/PedroSmaxY/abnt-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/PedroSmaxY/abnt-mcp/actions/workflows/ci.yml)

---

## 1. Apresentação e Justificativa Científica

A elaboração de manuscritos técnico-científicos no Brasil — compreendendo Trabalhos de Conclusão de Curso (TCC), dissertações de mestrado, teses de doutorado e artigos para periódicos — exige estrita consonância com o arcabouço normativo estabelecido pela **Associação Brasileira de Normas Técnicas (ABNT)** e pelas diretrizes de representação tabular do **Instituto Brasileiro de Geografia e Estatística (IBGE)**.

Apesar da ampla disseminação de Grandes Modelos de Linguagem (LLMs) como assistentes na pesquisa acadêmica, observa-se uma taxa reincidente de desvios normativos e alucinações estruturais, tais como:

1. **Persistência de padrões revogados:** Utilização de autoria em CAIXA ALTA dentro de parênteses, prática formalmente extinta pela atualização da **ABNT NBR 10520:2023**;
2. **Inconsistências bibliográficas cruzadas:** Citações órfãs no corpo do texto e obras listadas nas referências finais que jamais foram citadas;
3. **Ausência de distinção tipográfica entre Tabelas e Quadros:** Violação sistemática das Normas Tabulares do IBGE (1993), que estabelecem o fechamento aberto para dados quantitativos e fechado para representações conceituais;
4. **Desvios de impessoalidade:** Frequente introdução de pronomes em primeira pessoa e asserções opinativas desprovidas de respaldo empírico ou bibliográfico.

O **ABNT Copilot MCP** (`abnt-mcp`) implementa uma camada de infraestrutura via **Model Context Protocol (MCP)**, dotando ambientes de desenvolvimento, clientes de IA e pesquisadores de mecanismos programáticos de auditoria, formatação formal, consulta em bases científicas indexadas e compilação direta para PDF.

---

## 2. Marco Regulatório e Normas Contempladas

O servidor foi arquitetado sob auditoria estrita das seguintes normas vigentes:

| Norma / Documento | Ano / Edição | Escopo no Servidor MCP |
| :--- | :--- | :--- |
| **ABNT NBR 14724** | 2011 (Em vigor) | Estrutura completa de trabalhos acadêmicos (elementos pré-textuais, textuais e pós-textuais), tipografia, paginação (3-3-2-2) e ilustrações. |
| **ABNT NBR 6022** | 2018 | Estrutura de artigos científicos em publicações periódicas (dispensa capa, folha de rosto e sumário; exige elementos textuais contínuos). |
| **ABNT NBR 10520** | **2023** (Edição Vigente) | Sistema autor-data em caixa mista `(Silva, 2023)`, citações diretas curtas (<=3 linhas) e longas (recuo de 4 cm, corpo 10, entrelinhas simples). |
| **ABNT NBR 6023** | 2018 (Errata 2020) | Referências bibliográficas alinhadas à esquerda, destaque gráfico exclusivo no título principal e abreviatura padronizada de meses (`maio` sem ponto). |
| **ABNT NBR 6024** | 2012 | Numeração progressiva das seções de um documento; erradicação de ponto final após o indicativo numérico (`1.1` e nunca `1.1.`). |
| **ABNT NBR 6027** | 2012 | Apresentação e ordenação estrita de sumários a partir dos elementos textuais. |
| **ABNT NBR 6028** | 2021 | Resumos documentais em parágrafo único (150 a 500 palavras) e representação de palavras-chave separadas por ponto e vírgula. |
| **Normas IBGE** | 1993 | Normas de apresentação tabular (distinção física entre tabelas abertas e quadros fechados). |

---

## 3. Arquitetura dos Pilares e Motor SDD (*Spec-Driven Development*)

O núcleo do sistema opera segregado em pilares modulares governados por especificações canônicas (`specs/`):

```
abnt-mcp/
├── specs/               # Especificações SDD Canônicas (Normas, Schema e Contratos MCP)
├── src/abnt_mcp/
│   └── pillars/
│       ├── diagnostics.py   # Pilar 1: Análise Estrutural (14724/6022), Tom Científico e Auditoria
│       ├── writing.py       # Pilar 2: Citações 2023, Referências 6023, Resumos e Figuras
│       ├── compiler.py      # Pilar 3: Compilação Multi-engine (Typst Rust Nativo e LaTeX)
│       ├── advisory.py      # Pilar 4: Crossref, SciELO, BibTeX por DOI e Simulação de Banca
│       └── spec.py          # Motor SDD: Manifesto Científico abnt.spec.json / SPEC.md
```

### Pilar 1: Analisar & Diagnosticar
- **Validação Estrutural (NBR 14724 e NBR 6022):** Valida a hierarquia documental para monografias (NBR 14724) e artigos científicos periódicos (NBR 6022), emitindo diagnósticos rastreáveis por IDs canônicos (`NBR14724-R01`, `NBR14724-R02`, `NBR6022-R01`, `NBR6024-R01`). Analisa fontes `.tex`, `.md`, `.typ` e arquivos compilados `.pdf`.
- **Auditoria Cruzada Citações vs. Referências:** Identifica chaves órfãs no texto e entradas inertes no arquivo `.bib`, compatível com chamadas LaTeX (`\cite`, `\citeonline`, `\apud`, `\citep`), Markdown (`[@ref]`, `@ref`) e Typst (`@ref`).
- **Análise de Impessoalidade e Rigor:** Detecta pronomes de primeira pessoa, adjetivação hiperbólica, coloquialismos e parágrafos sem fundamentação.

### Pilar 2: Redigir & Reformular
- **Formatador de Citações (NBR 10520:2023):** Assegura autoria em caixa baixa-alta dentro de parênteses `(Silva; Santos, 2023)` e posicionamento do ponto final após os parênteses da indicação da fonte.
- **Formatador de Figuras e Ilustrações (NBR 14724):** Gera a chamada textual obrigatória, identificação superior (`Figura X – Título`) e fonte no rodapé (`Fonte: Elaborado pelo autor (Ano).`).
- **Diferenciação Tabular IBGE:** Implementa a abertura lateral em Tabelas (dados numéricos) e fechamento em moldura para Quadros (dados conceituais).
- **Gerador de Resumo (NBR 6028:2021):** Síntese em parágrafo único de 150 a 500 palavras estruturada em contexto, objetivo, metodologia, resultados e conclusão.

### Pilar 3: Testar & Compilar
- **Motor Tipográfico Nativo Embutido:** Compilação ultra-rápida via biblioteca nativa em Rust (`typst`), entregando arquivos `.pdf` diretamente sem demandar a instalação de distribuições externas de LaTeX no sistema operacional.
- **Ciclo Completo abnTeX2:** Suporte ao ciclo multi-pass (`pdflatex -> bibtex -> pdflatex -> pdflatex`) ou `latexmk` para resolução irrestrita de referências cruzadas `[?]`.
- **Linter de Sintaxe Pré-compilação:** Mapeamento de ambientes desbalanceados (`\begin{...}` sem `\end{...}`) e caracteres especiais desprotegidos com identificação da linha exata.

### Pilar 4 & Motor SDD: Mentoria, Banca Examinadora e Especificação Científica
- **Escrita Acadêmica Orientada a Especificação (`abnt.spec.json` & `SPEC.md`):** Formaliza em 3 camadas o Perfil Normativo, a Matriz Científica (`OBJ-01`, `OBJ-02`...) e os Capítulos Planejados, auditando automaticamente se cada objetivo específico prometido na Introdução foi desenvolvido no texto e respondido na Conclusão.
- **Recuperação de Literatura Primária:** Consulta em tempo real às APIs abertas do **Crossref** e da rede **SciELO**, obtendo metadados completos (DOI, resumo, periódico e autores).
- **Consistência de BibTeX por DOI:** Obtenção automática de metadados oficiais diretamente de `doi.org` com deduplicação nativa.
- **Simulador de Banca Avaliadora:** Avaliação determinística do alinhamento entre os objetivos específicos da `abnt.spec.json` e os achados das Considerações Finais, formulando arguições personalizadas para objetivos pendentes.

---

## 4. Especificação Técnica das Interfaces MCP

O servidor expõe formalmente 16 ferramentas, 3 prompts orientados e 8 recursos canônicos sob a especificação do Model Context Protocol:

### 4.1. Ferramentas Operacionais (`@mcp.tool`)

| Identificador | Parâmetros de Entrada | Descrição Formal |
| :--- | :--- | :--- |
| `init_research_spec` | `project_path: str`, `title: str`, `research_problem: str`, `general_objective: str`, `specific_objectives: list`, `methodology_summary: str`, `document_type: str = "tcc"`, ... | Inicializa o manifesto científico SDD (`abnt.spec.json` e `SPEC.md`) em 3 camadas no projeto. |
| `audit_research_spec` | `project_path: str`, `spec_path: str?` | Audita o manuscrito contra `abnt.spec.json`, validando a entrega de cada objetivo específico (`OBJ-XX`) na Conclusão. |
| `simulate_banca` | `project_path: str` | Simula arguição de banca examinadora com notas por eixo e cobrança direta de objetivos específicos pendentes. |
| `check_structure` | `project_path: str`, `standard: str = "ABNT_14724"` | Analisa a conformidade dos elementos pré, textuais e pós-textuais (NBR 14724 e NBR 6022) de fontes ou PDFs. |
| `validate_citations` | `project_path: str`, `bib_path: str?` | Auditoria cruzada entre texto e referências, apontando citações órfãs e violações de caixa alta. |
| `analyze_tone` | `text: str` | Mensura o índice de rigor científico (0-100), sinalizando primeira pessoa e coloquialismos. |
| `format_citation` | `authors: list[str]`, `year: str\|int`, `style: str`, `quote_type: str`, `page: str?`, `quote_text: str?` | Formatação de citações diretas (curtas/longas) e indiretas sob a NBR 10520:2023. |
| `format_reference` | `entry_type: str`, `title: str`, `year: str\|int`, `authors: list?`, `journal_name: str?`, `publisher: str?`, ... | Elaboração de referências conforme NBR 6023:2018 com destaque exclusivo no título principal. |
| `format_figure` | `image_path: str`, `caption: str`, `source: str`, `figure_number: int\|str` | Gera snippets para inserção formal de ilustrações (topo, centro, base com fonte e chamada textual). |
| `format_table` | `title: str`, `headers: list[str]`, `rows: list[list[str]]`, `source: str`, `category: "tabela"\|"quadro"` | Formatação de tabelas (Normas IBGE, laterais abertas) ou quadros (ABNT, bordas fechadas). |
| `generate_academic_resumo` | `context: str`, `objective: str`, `methodology: str`, `results: str`, `conclusion: str`, `keywords: list[str]`, `language: "pt"\|"en"` | Redação de resumo ou abstract canônico contínuo (NBR 6028) com validação de extensão. |
| `search_academic_papers` | `query: str`, `source: "all"\|"crossref"\|"scielo"`, `limit: int = 5` | Recuperação de artigos indexados com DOI, resumo e metadados estruturados. |
| `fetch_bibtex_by_doi` | `doi: str`, `bib_file: str?` | Recupera a entrada BibTeX oficial via negociação de conteúdo e anexa ao `.bib` sem duplicatas. |
| `clean_bibtex_file` | `bib_path: str`, `output_path: str?` | Higienização de arquivos BibTeX, conversão para UTF-8 estrito e normalização de meses ABNT. |
| `compile_tcc` | `project_path: str`, `engine: "auto"\|"typst"\|"latex"\|"markdown"` | Compilação direta para PDF no padrão ABNT com diagnóstico de erros e indicação de linhas. |
| `read_pdf_section` | `pdf_path: str`, `pages: list[int]?`, `start_page: int?`, `end_page: int?` | Extração seletiva de texto e contagem lexical de documentos PDF para fins de auditoria. |

### 4.2. Prompts de Orientação e Revisão (`@mcp.prompt`)

- **`revisar_capitulo(texto, foco)`**: Instruções parametrizadas para parecer técnico contendo nota de rigor científico, diagnóstico de impessoalidade e proposta de reformulação.
- **`formatar_citacao(trecho, autor, ano, pagina, tipo)`**: Geração de blocos canônicos de citação para Markdown, LaTeX (`abntex2`) e Typst.
- **`simular_banca(projeto_path)`**: Análise de vulnerabilidades metodológicas, conformidade com a introdução e as principais perguntas de arguição para defesa oral.

### 4.3. Recursos Canônicos Integrados (`@mcp.resource`)

- `abnt://guia/citacoes`: Síntese executiva da ABNT NBR 10520:2023.
- `abnt://guia/estrutura`: Checklist completo da NBR 14724:2011 e NBR 6024:2012.
- `abnt://guia/referencias`: Matriz tipológica de referências bibliográficas da NBR 6023:2018.
- `abnt://guia/sdd`: Guia de Escrita Acadêmica Orientada a Especificações (SDD).
- `abnt://template/latex`: Template funcional completo para LaTeX configurado com abnTeX2.
- `abnt://template/typst`: Template funcional moderno em Typst com geometria física 3-3-2-2.
- `abnt://template/markdown`: Template Pandoc com cabeçalho YAML e metadados para CSL.
- `abnt://template/spec`: Template JSON em 3 camadas do manifesto `abnt.spec.json`.

---

## 5. Instalação e Execução

O servidor é compatível com Python `>=3.10` e preparado para execução direta através do gerenciador de ambientes [uv](https://docs.astral.sh/uv/):

### Execução Instantânea (Zero Configuração)
```bash
uvx abnt-mcp
```

### Instalação via Gerenciador de Pacotes
```bash
# Utilizando uv:
uv pip install abnt-mcp

# Utilizando pip tradicional:
pip install abnt-mcp

# Execução do servidor MCP (transporte stdio padrão):
abnt-mcp
```

---

## 6. Configuração nos Ambientes de Pesquisa

### Claude Desktop
Edite o arquivo de configuração do Claude Desktop (`claude_desktop_config.json`):
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS / Linux:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "abnt-mcp": {
      "command": "uvx",
      "args": ["abnt-mcp"]
    }
  }
}
```

### Cursor IDE
No diretório raiz da sua pesquisa ou globalmente nas preferências do Cursor, configure `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "abnt-mcp": {
      "command": "uvx",
      "args": ["abnt-mcp"]
    }
  }
}
```

### Google Antigravity / Gemini CLI
No arquivo de registro de servidores MCP (`mcp_config.json`):

```json
{
  "mcpServers": {
    "abnt-mcp": {
      "command": "uvx",
      "args": ["abnt-mcp"]
    }
  }
}
```

---

## 7. Garantia de Qualidade, Cobertura e CI/CD

A integridade do código-fonte e a fidelidade às normas técnicas são aferidas de forma contínua através de uma suíte automatizada no `pytest`, com auditoria de cobertura de código via `pytest-cov` e esteira de integração contínua (**GitHub Actions CI/CD**) multiplataforma.

### 7.1 Execução da Suíte de Testes

```bash
# Execução da suíte completa com análise de cobertura
uv run pytest -v --cov=abnt_mcp --cov-report=term-missing
```

```text
============================= 69 passed in 5.40s =============================
tests/test_advisory.py (4 testes)     -> Consulta Crossref/SciELO, DOI e Simulador de Banca
tests/test_compiler.py (4 testes)     -> Linter de ambientes, tratamento de logs e engines
tests/test_diagnostics.py (6 testes)  -> Estrutura NBR 14724, auditoria de citações e tom científico
tests/test_edge_cases.py (23 testes)  -> Casos de borda (paginação NBR 14724, autores compostos, localizadores, IBGE vs ABNT)
tests/test_parsers.py (9 testes)      -> Extratores LaTeX/MD/Typst, validação de caixa alta e extração de PDF
tests/test_sdd.py (6 testes)          -> Trava Anti-Drift SDD, NBR 6022, abnt.spec.json e objetivos na banca
tests/test_server.py (6 testes)       -> Registro e execução de tools, prompts e resources
tests/test_writing.py (11 testes)     -> Citações 2023, Referências 6023, Resumo, Figuras e Tabelas
```

### 7.2 Relatório de Cobertura de Código

A suíte assegura **83% de cobertura global** no núcleo do sistema:

| Módulo / Camada | Declarações | Cobertura | Escopo de Garantia |
| :--- | :---: | :---: | :--- |
| `abnt_mcp.config` | 14 | **100%** | Catálogo SDD (`NORMATIVE_RULES`), regexes normativas, meses ABNT e léxico |
| `abnt_mcp.models` | 130 | **100%** | Esquemas Pydantic e modelos de 3 camadas (`ResearchSpec`) |
| `abnt_mcp.parsers.citations` | 81 | **91%** | Extração e auditoria de citações em LaTeX, MD e Typst |
| `abnt_mcp.pillars.diagnostics` | 174 | **89%** | Validação NBR 14724 / NBR 6022, auditoria de `.bib`, tom científico e paginação |
| `abnt_mcp.pillars.writing` | 204 | **87%** | NBR 10520:2023, NBR 6023:2018, NBR 6028, tabelas IBGE e figuras |
| `abnt_mcp.server` | 110 | **85%** | Protocolo FastMCP (16 tools, 3 prompts, 8 resources) |
| `abnt_mcp.pillars.spec` | 159 | **82%** | Motor SDD (`abnt.spec.json`, `SPEC.md` e auditoria de objetivos específicos) |
| `abnt_mcp.pillars.advisory` | 146 | **81%** | Consultas Crossref, SciELO, BibTeX por DOI e banca integrada ao SDD |
| `abnt_mcp.parsers.bibtex` | 92 | **80%** | Sanitização, normalização e deduplicação de entradas |
| `abnt_mcp.parsers.pdf_reader` | 98 | **80%** | Auditoria forense de paginação NBR 14724 e extração de PDF |
| `abnt_mcp.pillars.compiler` | 222 | **66%** | Compilação nativa Typst, LaTeX abnTeX2 e Pandoc |
| **Total do Ecossistema** | **1464** | **83%** | **69 testes aprovados** |

### 7.3 Esteira de Integração Contínua (GitHub Actions)

A cada *push* ou *pull request* submetido à *branch* `main`, o pipeline automatizado (`.github/workflows/ci.yml`) valida o projeto em matriz cruzada:

- **Sistemas Operacionais:** Ubuntu Linux (`ubuntu-latest`) e Windows Server (`windows-latest`).
- **Versões do Interpretador Python:** 3.10, 3.11 e 3.12.
- **Validações Automatizadas:** Resolução determinística com `uv sync`, execução completa dos 69 testes (incluindo trava anti-drift SDD) com relatório XML de cobertura e teste de integridade da CLI (`abnt-mcp --help`).

---

## 8. Como Citar este Projeto

Caso utilize o **ABNT Copilot MCP** no desenvolvimento de sua pesquisa, dissertação, tese ou artigo científico, cite o repositório em conformidade com a **ABNT NBR 6023:2018**:

```text
NOVAIS, Pedro Henrique da Silva. ABNT Copilot MCP: servidor Model Context Protocol para padronização e conformidade acadêmica. Versão 0.1.0. GitHub, 2026. Disponível em: https://github.com/PedroSmaxY/abnt-mcp. Acesso em: 24 out. 2026.
```

Entrada BibTeX:
```bibtex
@software{novais2026abntmcp,
  author       = {Novais, Pedro Henrique da Silva},
  title        = {ABNT Copilot MCP: Servidor Model Context Protocol para Padronização e Conformidade Acadêmica},
  version      = {0.1.0},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/PedroSmaxY/abnt-mcp}
}
```

---

## 9. Governança SDD, Licença e Contribuições

Este projeto é disponibilizado sob a licença de código aberto **MIT** e regido por **Desenvolvimento Orientado a Especificações (*Spec-Driven Development* — SDD)**.

Antes de propor alterações ou submeter um *Pull Request*, consulte obrigatoriamente:
- **[CONTRIBUTING.md](CONTRIBUTING.md):** Protocolo técnico-científico de colaboração, convenção de *branches*, *commits* semânticos e matriz de rastreabilidade.
- **[AGENTS.md](AGENTS.md) & [CLAUDE.md](CLAUDE.md):** Diretrizes mandatórias de sincronização de especificações (`specs/`) para agentes de Inteligência Artificial.
- **[`specs/`](specs/):** Catálogo normativo canônico (`01-normative-catalog.spec.md`), especificação do manifesto científico (`02-research-spec-schema.spec.md`) e contratos de ferramentas MCP (`03-mcp-tools-contract.spec.md`).
