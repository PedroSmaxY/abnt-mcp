# Protocolo Técnico-Científico de Colaboração e Governança SDD (`CONTRIBUTING.md`)

**Diretrizes Formais para Engenharia Orientada a Especificações, Conformidade Normativa (ABNT/IBGE) e Submissão de Contribuições ao `abnt-mcp`**

---

## 1. Fundamentação e Paradigma de Engenharia

O **ABNT Copilot MCP** (`abnt-mcp`) constitui uma infraestrutura programática de validação, formatação e compilação documental submetida ao rigor estrito das normas técnicas brasileiras emanadas pela **Associação Brasileira de Normas Técnicas (ABNT)** e pelo **Instituto Brasileiro de Geografia e Estatística (IBGE)**.

Diferentemente de projetos de software convencionais nos quais os requisitos são informais ou mutáveis, neste ecossistema **a especificação normativa precede a implementação**. Por essa razão, o repositório adota formalmente a metodologia de **Desenvolvimento Orientado a Especificações (*Spec-Driven Development* — SDD)** tanto para colaboradores humanos quanto para agentes autônomos de Inteligência Artificial (conforme regido em [AGENTS.md](AGENTS.md) e [CLAUDE.md](CLAUDE.md)).

---

## 2. Ciclo de Vida SDD (*Spec-First Workflow*)

Nenhuma modificação de comportamento normativo, esquema de dados ou superfície de protocolo MCP pode ser introduzida diretamente no código-fonte sem antes percorrer as quatro etapas do ciclo SDD:

```text
[1. Especificação em specs/] ──► [2. Catálogo & Schema (config/models)] ──► [3. Implementação no Pilar/Server] ──► [4. Teste Anti-Drift & Cobertura]
```

### 2.1. Etapa 1: Atualização da Especificação (`specs/`)
Toda proposta de alteração ou implementação deve iniciar pela edição (ou adição) do contrato correspondente no diretório `specs/`:
- **Regras da ABNT ou do IBGE:** Documentar a cláusula em `specs/01-normative-catalog.spec.md`, atribuindo um identificador canônico único no formato `<NORMA>-R<NN>` (ex.: `NBR10520-R01`, `NBR14724-R02`, `IBGE1993-R01`), acompanhado do ano de vigência e seção/item oficial da norma.
- **Manifesto Científico do Pesquisador (`abnt.spec.json`):** Documentar alterações nas 3 camadas do schema em `specs/02-research-spec-schema.spec.md`.
- **Superfície do Protocolo FastMCP:** Documentar qualquer nova `@mcp.tool`, `@mcp.prompt` ou `@mcp.resource` (ou alteração de assinatura) em `specs/03-mcp-tools-contract.spec.md`.

### 2.2. Etapa 2: Sincronização de Catálogo e Tipagem (`config.py` e `models.py`)
- Registrar o identificador canônico no dicionário `NORMATIVE_RULES` em `src/abnt_mcp/config.py`.
- Declarar ou atualizar os esquemas de validação estrita com `pydantic>=2.0` em `src/abnt_mcp/models.py`.

### 2.3. Etapa 3: Implementação Modular nos Pilares (`src/abnt_mcp/pillars/`)
A arquitetura deve preservar o desacoplamento entre responsabilidades:
- `pillars/diagnostics.py`: Auditoria estrutural (NBR 14724 e NBR 6022), consistência cruzada `.bib` e análise de impessoalidade/tom científico.
- `pillars/writing.py`: Geração e formatação normativa (NBR 10520:2023, NBR 6023:2018, NBR 6028:2021, ilustrações e tabelas IBGE).
- `pillars/compiler.py`: Compilação multi-engine (`typst` nativo em Rust, `pdflatex`/`latexmk` com `abnTeX2` e `pandoc`).
- `pillars/advisory.py`: Integração com APIs científicas (Crossref, SciELO, `doi.org`) e Simulador de Banca Examinadora.
- `pillars/spec.py`: Motor de Escrita Acadêmica Orientada a Especificação (`abnt.spec.json` / `SPEC.md`).

### 2.4. Etapa 4: Verificação Automatizada e Trava Anti-Drift (`tests/`)
O repositório possui uma trava automatizada em `tests/test_sdd.py` que verifica em tempo de execução se todas as regras declaradas em `NORMATIVE_RULES` e todas as interfaces registradas em `server.py` estão presentes nos arquivos de `specs/`. Caso uma contribuição modifique o código sem atualizar `specs/`, a esteira de integração contínua (**GitHub Actions CI/CD**) rejeitará a submissão automaticamente.

---

## 3. Padrão Geral de Branches, Commits e Pull Requests

### 3.1. Convenção de Nomenclatura de *Branches*
Utilize prefixos semânticos alinhados à natureza da intervenção:
- `spec/<escopo>`: Criação ou revisão de especificações formais em `specs/` (ex.: `spec/nbr-6022-artigos`).
- `feat/<pilar-ou-norma>`: Implementação de novas ferramentas ou regras especificadas (ex.: `feat/sdd-audit-engine`).
- `fix/<rule-id-ou-modulo>`: Correção de desvio normativo ou falha técnica (ex.: `fix/NBR14724-R02-pagination`).
- `docs/<escopo>`: Evolução de documentação técnica ou acadêmica (ex.: `docs/contributing-protocol`).
- `test/<escopo>`: Ampliação da cobertura de testes e casos de borda (ex.: `test/ibge-tabular-edges`).

### 3.2. Padrão de Mensagens de *Commit* (*Conventional Commits*)
As mensagens de *commit* devem ser redigidas de forma imperativa, clara e referenciar o escopo ou ID canônico:

```text
<tipo>(<escopo>): <descrição concisa e técnica>

[Corpo opcional detalhando a cláusula da NBR/IBGE e os arquivos de specs/ atualizados]
```

**Tipos admitidos:**
- `spec`: Alteração nas especificações canônicas dentro de `specs/`.
- `feat`: Nova funcionalidade ou regra normativa respaldada por spec.
- `fix`: Correção de bug técnico ou desvio de conformidade normativa.
- `refactor`: Refatoração interna sem alteração de contrato externo.
- `test`: Adição ou atualização de testes automatizados no `pytest`.
- `docs`: Atualização de `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md` ou docstrings.
- `ci`: Ajustes nos pipelines de integração contínua (`.github/workflows/`).

### 3.3. Padrão de Submissão de *Pull Requests* (PRs)
Todo *Pull Request* submetido à *branch* `main` deve preencher integralmente o modelo `.github/PULL_REQUEST_TEMPLATE.md`, apresentando obrigatoriamente:
1. **Justificativa Científica / Normativa:** Indicação explícita da norma (ex.: ABNT NBR 10520:2023, Seção 4.2) ou motivação arquitetural.
2. **Tabela de Rastreabilidade SDD:** Mapeamento entre o arquivo atualizado em `specs/`, o `Rule ID` ou `@mcp.tool` afetado e o teste correspondente em `tests/`.
3. **Conformidade Multiplataforma:** Aprovação integral na matriz do GitHub Actions (Ubuntu Linux e Windows Server sob Python 3.10, 3.11 e 3.12).

---

## 4. Configuração do Ambiente de Desenvolvimento e Auditoria Local

### 4.1. Requisitos de Ambiente
- Interpretador Python `>= 3.10` (`3.10`, `3.11` ou `3.12`).
- Gerenciador de pacotes e ambientes [uv](https://docs.astral.sh/uv/).

### 4.2. Instalação e Execução dos Testes
```bash
# 1. Clonar o repositório e sincronizar o ambiente determinístico
git clone https://github.com/PedroSmaxY/abnt-mcp.git
cd abnt-mcp
uv sync --extra dev

# 2. Executar a suíte completa com auditoria de cobertura e verificação SDD
uv run pytest -v --cov=abnt_mcp --cov-report=term-missing

# 3. Validar a interface de linha de comando do servidor
uv run abnt-mcp --help
```

---

## 5. Reporte de Problemas e Propostas via *Issues*

Para assegurar a reprodutibilidade e o rigor normativo na triagem de demandas, utilize exclusivamente os formulários estruturados disponibilizados pelo repositório:
1. **Desvio ou Atualização Normativa (`.github/ISSUE_TEMPLATE/normative_deviation.yml`):** Destinado a relatar divergências em relação às normas da ABNT ou do IBGE, exigindo a citação da norma, edição e item normativo.
2. **Proposta de Especificação SDD (`.github/ISSUE_TEMPLATE/feature_spec.yml`):** Destinado à proposição de novas ferramentas MCP, perfis institucionais ou ampliação do manifesto `abnt.spec.json`.
3. **Relato de Falha Técnica (`.github/ISSUE_TEMPLATE/bug_report.yml`):** Destinado a erros de execução, parsers de BibTeX/PDF ou motores de compilação (`typst`, `latex`, `markdown`).
