# CLAUDE.md — Instruções para Claude Code

> **Atenção:** Este repositório é estritamente regido pelo paradigma **Spec-Driven Development (SDD)**.
> A Fonte Única da Verdade para governança, regras operacionais, invariantes normativas da ABNT/IBGE, fluxo de 4 etapas e padrões de branch/commit/PR está centralizada em **[AGENTS.md](AGENTS.md)**.

---

## 1. Diretriz Mandatória
Ao iniciar qualquer tarefa ou proposta de alteração neste repositório:
1. **Leia obrigatoriamente o arquivo [AGENTS.md](AGENTS.md)** para compreender as regras inegociáveis, catálogo normativo e a trava anti-drift.
2. Toda alteração em código ou regras exige atualizar os arquivos correspondentes em `specs/` antes ou junto com o código.
3. Toda alteração em `src/`, `specs/` ou `pyproject.toml` deve ser obrigatoriamente registrada em `CHANGELOG.md` (sob `## [Unreleased]`).

---

## 2. Comandos Essenciais de Desenvolvimento

```bash
# Sincronizar dependências com uv
uv sync --all-extras

# Executar suíte completa de testes e cobertura com trava anti-drift SDD
uv run pytest -v --cov=abnt_mcp --cov-report=term-missing

# Testar a CLI do servidor FastMCP
uv run abnt-mcp --help
```
