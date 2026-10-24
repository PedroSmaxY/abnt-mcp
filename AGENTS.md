# AGENTS.md — Diretrizes Operacionais e Governança SDD para Agentes de IA

> **Atenção Agente Autônomo (Antigravity, Claude Code, Cursor, GitHub Copilot, Codex):**
> Este repositório opera estritamente sob o paradigma **Spec-Driven Development (SDD — Desenvolvimento Orientado a Especificações)**. Toda e qualquer proposta de alteração, refatoração, correção normativa ou nova funcionalidade **DEVE obrigatoriamente atualizar ou criar as especificações em `specs/` antes ou simultaneamente à modificação do código-fonte**.

---

## 1. Regra de Ouro: Sincronização Obrigatória de Specs (`Spec-Sync`)

1. **`specs/` é a Fonte Única da Verdade:**
   - `specs/01-normative-catalog.spec.md`: Catálogo de regras normativas ABNT e IBGE (`NORMATIVE_RULES` em `src/abnt_mcp/config.py`).
   - `specs/02-research-spec-schema.spec.md`: Contrato do manifesto `abnt.spec.json` e `SPEC.md` (`ResearchSpec` em `src/abnt_mcp/models.py`).
   - `specs/03-mcp-tools-contract.spec.md`: Contrato formal de todas as `@mcp.tool`, `@mcp.prompt` e `@mcp.resource` expostas em `src/abnt_mcp/server.py`.
2. **Proibição de Drift (Desvio entre Spec e Código):**
   - **Ao propor uma alteração (Plano/RFC):** Sempre inclua no plano quais arquivos de `specs/` serão atualizados e quais IDs de regra (`NBRXXXX-RXX`) serão criados ou modificados.
   - **Ao implementar uma alteração:** Atualize `specs/` em sincronia estrita com `src/abnt_mcp/`.
   - **Trava Automatizada de CI/CD:** A suíte `tests/test_sdd.py` possui testes anti-drift (`test_sdd_anti_drift_normative_rules` e `test_sdd_anti_drift_mcp_surface`) que falham imediatamente caso qualquer regra em `NORMATIVE_RULES` ou qualquer interface em `server.py` não esteja documentada em `specs/`.

---

## 2. Fluxo de Trabalho Obrigatório em 4 Etapas

Sempre que receber uma tarefa neste repositório, execute rigorosamente esta sequência:

1. **Etapa 1 — Especificar (`specs/`):**
   - Consulte e atualize o arquivo correspondente em `specs/` (`01-normative-catalog.spec.md`, `02-research-spec-schema.spec.md` ou `03-mcp-tools-contract.spec.md`).
2. **Etapa 2 — Tipar e Catalogar (`config.py` & `models.py`):**
   - Registre ou atualize o identificador canônico em `NORMATIVE_RULES` (`src/abnt_mcp/config.py`) e os modelos Pydantic em `src/abnt_mcp/models.py`.
3. **Etapa 3 — Implementar nos Pilares e Servidor (`pillars/`, `parsers/`, `server.py`):**
   - Implemente a lógica mantendo a separação modular dos 4 pilares + motor SDD (`diagnostics.py`, `writing.py`, `compiler.py`, `advisory.py`, `spec.py`).
4. **Etapa 4 — Verificar com Testes Rastreáveis (`tests/`):**
   - Adicione testes cobrindo a nova cláusula/funcionalidade e execute:
     ```bash
     uv run pytest -v --cov=abnt_mcp --cov-report=term-missing
     ```

---

## 3. Invariantes Normativas Inegociáveis (ABNT & IBGE)

Jamais gere código, templates, prompts ou testes que violem estas regras vigentes:

- **`NBR10520-R01` (ABNT NBR 10520:2023):** Autores citados **dentro de parênteses** utilizam exclusivamente **caixa mista** `(Silva, 2023)` ou `(Silva; Santos, 2023)`. O padrão antigo em CAIXA ALTA `(SILVA, 2023)` da norma revogada de 2002 é estritamente proibido.
- **`NBR10520-R03` (ABNT NBR 10520:2023):** Citações diretas curtas (até 3 linhas) ficam no parágrafo entre aspas duplas com o ponto final **após** os parênteses; citações diretas longas (> 3 linhas) usam recuo de 4 cm, fonte 10, espaçamento simples e **sem aspas**.
- **`NBR14724-R02` (ABNT NBR 14724:2011, item 5.3):** A Capa não é contada; a contagem sequencial inicia na Folha de Rosto; nenhum elemento pré-textual pode exibir número de página impresso; a numeração arábica aparece apenas a partir da Introdução, no canto superior direito.
- **`NBR6022-R01` (ABNT NBR 6022:2018):** Artigos científicos periódicos não exigem capa, folha de rosto nem sumário.
- **`NBR6023-R01` & `NBR6023-R02` (ABNT NBR 6023:2018):** Referências alinhadas exclusivamente à margem esquerda; destaque tipográfico (negrito ou itálico) aplicado **apenas ao título principal** (nunca ao subtítulo); mês de maio grafado por extenso (`maio`, nunca `mai.`).
- **`NBR6024-R01` (ABNT NBR 6024:2012):** Não há ponto final após o indicativo numérico de seção (`1.1 Metodologia` e nunca `1.1. Metodologia`).
- **`IBGE1993-R01` (Normas Tabulares IBGE, 1993):** **Tabelas** (dados quantitativos) têm bordas laterais esquerda e direita **abertas**; **Quadros** (dados conceituais/textuais) têm todas as bordas **fechadas**.

---

## 4. Padrão de Commits, Branches e Pull Requests

- **Branches:** `spec/<escopo>`, `feat/<escopo>`, `fix/<rule-id>`, `docs/<escopo>`, `test/<escopo>`.
- **Commits Semânticos:**
  - `spec(nbr10520): adicionar cláusula NBR10520-R04 ao catálogo`
  - `feat(spec): implementar auditoria de objetivos específicos em abnt.spec.json`
  - `fix(NBR14724-R02): corrigir detecção de paginação em elementos pré-textuais`
- **Pull Requests:** Preencha integralmente o template `.github/PULL_REQUEST_TEMPLATE.md`, preenchendo a tabela de rastreabilidade (`Spec Atualizada` -> `Rule ID / Tool` -> `Teste`).
