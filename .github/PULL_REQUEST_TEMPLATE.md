## 1. Resumo Executivo e Motivação Normativa / Técnica

<!-- Descreva de forma clara e objetiva o propósito deste Pull Request. Caso envolva alguma norma técnica (ABNT NBR 14724, 10520:2023, 6023:2018, 6022, 6024, 6028 ou IBGE), indique a norma e a seção correspondente. -->

- **Issue Relacionada:** Closes #
- **Natureza da Alteração:** `[ ] spec` | `[ ] feat` | `[ ] fix` | `[ ] refactor` | `[ ] docs` | `[ ] test`

---

## 2. Matriz de Rastreabilidade SDD (*Spec-Driven Development*)

> **Regra Obrigatória (`AGENTS.md` / `CONTRIBUTING.md`):** Nenhuma regra normativa, schema ou interface MCP pode ser alterada no código sem a atualização simultânea da especificação correspondente em `specs/`.

| Artefato de Especificação (`specs/`) | ID Canônico (`NORMATIVE_RULES`) ou Interface MCP | Módulo(s) Alterado(s) | Teste(s) de Validação (`tests/`) |
| :--- | :--- | :--- | :--- |
| Ex.: `specs/01-normative-catalog.spec.md` | Ex.: `NBR10520-R01` / `audit_research_spec` | Ex.: `pillars/spec.py` | Ex.: `tests/test_sdd.py` |

---

## 3. Checklist de Conformidade SDD e Qualidade

- [ ] **Sincronia de Specs (`Spec-Sync`):** Atualizei os arquivos em `specs/` (`01-normative-catalog.spec.md`, `02-research-spec-schema.spec.md` e/ou `03-mcp-tools-contract.spec.md`) antes ou junto com o código.
- [ ] **Invariantes Normativas Preservadas:** Verifiquei que a alteração não reintroduz padrões revogados (como autoria em CAIXA ALTA entre parênteses da antiga NBR 10520:2002, ponto após seção da NBR 6024 ou `mai.` com ponto da NBR 6023).
- [ ] **Tipagem e Schemas:** Modelos Pydantic em `src/abnt_mcp/models.py` e `NORMATIVE_RULES` em `src/abnt_mcp/config.py` estão devidamente tipados e sincronizados.
- [ ] **Testes e Trava Anti-Drift:** Executei `uv run pytest -v --cov=abnt_mcp` localmente e todos os testes (incluindo `tests/test_sdd.py`) passaram sem regressões.
- [ ] **Registro no `CHANGELOG.md`:** Documentei todas as alterações deste PR em `CHANGELOG.md` (sob `## [Unreleased]` ou na versão correspondente).
- [ ] **Documentação:** Atualizei `README.md` / docstrings caso novas interfaces MCP tenham sido adicionadas.
