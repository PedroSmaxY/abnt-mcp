# CLAUDE.md — Guia de Engenharia SDD e Contexto Rápido do Repositório

Este projeto (**ABNT Copilot MCP** — `abnt-mcp`) segue **Spec-Driven Development (SDD)**.
Leia integralmente as diretrizes em [AGENTS.md](AGENTS.md) e as especificações em `specs/` antes de propor ou executar qualquer alteração.

---

## 1. Diretriz Mandatória para Propostas e Alterações

> **IMPORTANTE:** Sempre que você (Claude / Agente de IA) formular uma proposta de mudança arquitetural, alteração de regra ABNT/IBGE ou criação/modificação de tool MCP, **você deve obrigatoriamente propor e aplicar a atualização correspondente nos arquivos dentro de `specs/`**.

- Mudança ou adição de regra normativa ABNT/IBGE -> Atualizar `specs/01-normative-catalog.spec.md` + `NORMATIVE_RULES` em `src/abnt_mcp/config.py`.
- Mudança no manifesto `abnt.spec.json` / `SPEC.md` -> Atualizar `specs/02-research-spec-schema.spec.md` + `src/abnt_mcp/models.py` + `src/abnt_mcp/pillars/spec.py`.
- Mudança em `@mcp.tool`, `@mcp.prompt` ou `@mcp.resource` -> Atualizar `specs/03-mcp-tools-contract.spec.md` + `src/abnt_mcp/server.py`.

---

## 2. Comandos Essenciais de Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
uv sync --extra dev

# Executar suíte completa de testes (incluindo trava anti-drift SDD) e cobertura
uv run pytest -v --cov=abnt_mcp --cov-report=term-missing

# Verificar execução da CLI do servidor MCP
uv run abnt-mcp --help
```

---

## 3. Mapa de Arquitetura

- `specs/`: Especificações canônicas (Catálogo Normativo, Schema SDD e Contrato de Interfaces MCP).
- `src/abnt_mcp/config.py`: `NORMATIVE_RULES` (IDs canônicos `NBRXXXX-RXX`), regexes normativas, meses ABNT (`maio` sem ponto) e léxico de impessoalidade.
- `src/abnt_mcp/models.py`: Modelos Pydantic de entrada, saída e `ResearchSpec` (3 camadas).
- `src/abnt_mcp/pillars/`:
  - `diagnostics.py`: Pilar 1 — Validação estrutural (`ABNT_14724` e `ABNT_6022`), auditoria `.bib` e tom científico.
  - `writing.py`: Pilar 2 — Citações NBR 10520:2023, referências NBR 6023:2018, figuras, tabelas IBGE e resumos NBR 6028.
  - `compiler.py`: Pilar 3 — Compilação nativa via Rust `typst`, `pdflatex`/`latexmk` (`abnTeX2`) e `pandoc`.
  - `advisory.py`: Pilar 4 — Crossref, SciELO, BibTeX por DOI e Simulador de Banca Examinadora integrado ao SDD.
  - `spec.py`: Motor SDD — Inicialização, parsing e auditoria de `abnt.spec.json` e `SPEC.md`.
- `src/abnt_mcp/server.py`: Servidor FastMCP expondo 16 tools, 3 prompts e 8 resources.
