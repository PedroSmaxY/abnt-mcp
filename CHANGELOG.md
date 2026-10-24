# Changelog

Todas as alterações relevantes, evoluções normativas (ABNT/IBGE) e novas interfaces MCP deste projeto são obrigatoriamente documentadas neste arquivo.

O formato baseia-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e este projeto adere ao [Versionamento Semântico (SemVer)](https://semver.org/lang/pt-BR/) governado por **Desenvolvimento Orientado a Especificações (*Spec-Driven Development* — SDD)**.

> **Regra de Governança SDD:** Nenhuma alteração em `src/` ou `specs/` pode ser mesclada à `main` sem o respectivo registro neste `CHANGELOG.md`. O teste automatizado `test_sdd_release_version_changelog_and_privacy_invariants` em `tests/test_sdd.py` e a pipeline de CI validam esta paridade.

---

## [Unreleased]

### Adicionado
- Padronização automatizada de Releases (`.github/workflows/release.yml` e `.github/release.yml`) com validação de paridade de versão, build `uv build`, teste de fumaça `uvx` e publicação via PyPI Trusted Publishing (OIDC).
- Trava automatizada de integridade de versão, `CHANGELOG.md` e privacidade de metadados PEP 621 (`test_sdd_release_version_changelog_and_privacy_invariants` em `tests/test_sdd.py`).

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
