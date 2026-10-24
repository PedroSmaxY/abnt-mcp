# Especificação do Manifesto Científico SDD (`abnt.spec.json` & `SPEC.md`)

> **Status:** CANÔNICO (`v1.0.0`)
> **Escopo:** Definição do contrato de dados e regras de auditoria para **Escrita Acadêmica Orientada a Especificações (Spec-Driven Academic Writing)** no `abnt-mcp`.

---

## 1. Propósito Científico

Trabalhos acadêmicos frequentemente sofrem de **desvio de escopo metodológico**: o pesquisador declara objetivos específicos na Introdução que não são desenvolvidos nas seções intermediárias ou não são respondidos nas Considerações Finais.

Para solucionar esse problema de forma determinística e auditável por LLMs, o `abnt-mcp` introduz o manifesto **`abnt.spec.json`** (acompanhado de sua representação legível **`SPEC.md`**) na raiz do projeto acadêmico do usuário.

---

## 2. Arquitetura do Manifesto em 3 Camadas

O schema é validado pelo modelo Pydantic `ResearchSpec` em `src/abnt_mcp/models.py`:

### Camada 1: Perfil Normativo e Institucional (`NormativeProfile`)
Define sob qual regime normativo e padrão institucional (aprendido via PDF de exemplo da faculdade ou configurado manualmente) o projeto deve ser validado:
- `document_type`: `"tcc"` | `"dissertacao"` | `"tese"` | `"artigo"` (padrão: `"tcc"`).
- `standard`: `"ABNT_14724"` (monografias completas) | `"ABNT_6022"` (artigos científicos periódicos).
- `institution`: Nome da universidade, faculdade ou periódico (opcional).
- `course`: Curso de graduação ou programa de pós-graduação (opcional).
- `department`: Centro, instituto, faculdade ou departamento (opcional).
- `advisor`: Nome do(a) professor(a) orientador(a) (opcional).
- `city`: Cidade/Local da instituição exibida no rodapé da Capa e Folha de Rosto (ex.: `"Rio de Janeiro"`, `"Curitiba - PR"`).
- `cover_header_lines`: Linhas superiores da capa na ordem institucional exata (ex.: `["UNIVERSIDADE...", "CENTRO...", "CURSO..."]`).
- `has_cover_logo`: Indica se a capa institucional exige brasão/logotipo (`bool`, padrão: `false`).
- `cover_logo_path`: Caminho relativo da imagem do logotipo copiada ou extraída para o projeto (ex.: `"figuras/logo_instituicao.png"`).
- `preamble_text`: Preâmbulo institucional completo da Folha de Rosto (opcional).
- `required_pre_textual`: Lista de elementos pré-textuais exigidos pela instituição além da NBR 14724 (ex.: `["ficha catalografica", "folha de aprovacao", "dedicatoria", "agradecimentos", "epigrafe", "lista de ilustracoes", "lista de tabelas", "lista de quadros", "lista de abreviaturas"]`). Quando presente, `scaffold_academic_project` injeta dinamicamente todos os blocos correspondentes na ordem oficial da ABNT NBR 14724 nos templates `typst`, `latex` e `markdown`, preservando estritamente as invariantes `NBR14724-R02` (sem numeração visível nas folhas pré-textuais) e `NBR6024-R01` (sem ponto após o número da seção).
- `conclusion_label`: Rótulo adotado pela instituição para a seção final (`"Conclusão"` ou `"Considerações Finais"`).
- `inferred_from_pdf`: Indica se os padrões institucionais foram extraídos automaticamente de um PDF modelo (`bool`, padrão: `false`).
- `emphasis_style`: `"bold"` | `"italic"` para títulos nas referências (NBR 6023:2018).
- `min_references`: Quantidade mínima de obras exigidas no arquivo `.bib` (padrão: `15` para TCC, `5` para artigos).
- `min_scientific_tone_score`: Índice mínimo de rigor científico e impessoalidade exigido (`0` a `100`, padrão: `80`).

### Camada 2: Matriz Científica Rastreável (`SpecificObjective`)
Garante a rastreabilidade ponta a ponta entre **Problema de Pesquisa -> Objetivo Geral -> Objetivos Específicos -> Desenvolvimento -> Conclusão**:
- `research_problem`: Pergunta científica norteadora do trabalho.
- `general_objective`: Objetivo geral do manuscrito.
- `methodology_summary`: Síntese da abordagem metodológica, instrumentos e procedimentos.
- `specific_objectives`: Lista de objetos `SpecificObjective` contendo:
  - `id`: Código canônico do objetivo (ex.: `"OBJ-01"`, `"OBJ-02"`).
  - `description`: Enunciado formal iniciado por verbo no infinitivo.
  - `keywords`: Lista de termos/conceitos técnicos que comprovam a discussão e resolução do objetivo.
  - `target_section`: Seção ou capítulo previsto para desenvolver o objetivo (opcional).

### Camada 3: Estrutura de Capítulos Planejados (`PlannedChapter`)
Define o esqueleto estrutural esperado do manuscrito:
- `number`: Indicativo numérico progressivo conforme a NBR 6024 (ex.: `"1"`, `"2"`, `"2.1"`).
- `title`: Título planejado da seção.
- `min_words`: Extensão mínima planejada em palavras (padrão: `200`).
- `min_citations`: Quantidade mínima esperada de citações fundamentando a seção (padrão: `1`).

---

## 3. Exemplo Canônico de `abnt.spec.json`

```json
{
  "spec_version": "1.0",
  "title": "Auditoria Automatizada de Trabalhos Acadêmicos via Model Context Protocol",
  "author": "Pedro Henrique da Silva Novais",
  "research_problem": "Como mitigar alucinações normativas de LLMs na redação de manuscritos segundo as normas da ABNT?",
  "general_objective": "Desenvolver e validar uma arquitetura orientada a especificações via MCP para garantia de conformidade com as normas ABNT e IBGE.",
  "methodology_summary": "Pesquisa aplicada de desenvolvimento tecnológico experimental com validação empírica automatizada via suíte de testes.",
  "profile": {
    "document_type": "tcc",
    "standard": "ABNT_14724",
    "institution": "Universidade Federal",
    "city": "Rio de Janeiro",
    "emphasis_style": "bold",
    "min_references": 15,
    "min_scientific_tone_score": 80
  },
  "specific_objectives": [
    {
      "id": "OBJ-01",
      "description": "Mapear as regras vigentes das normas ABNT NBR 14724, 10520:2023 e 6023:2018 em um catálogo executável.",
      "keywords": ["10520", "6023", "14724", "catálogo", "normas"],
      "target_section": "Fundamentação Teórica"
    },
    {
      "id": "OBJ-02",
      "description": "Implementar motores de validação estrutural e compilação nativa em Typst e LaTeX.",
      "keywords": ["typst", "latex", "compilação", "paginação"],
      "target_section": "Metodologia"
    }
  ],
  "planned_chapters": [
    { "number": "1", "title": "Introdução", "min_words": 300, "min_citations": 2 },
    { "number": "2", "title": "Fundamentação Teórica", "min_words": 800, "min_citations": 5 },
    { "number": "3", "title": "Metodologia", "min_words": 500, "min_citations": 2 },
    { "number": "4", "title": "Resultados e Discussão", "min_words": 600, "min_citations": 2 },
    { "number": "5", "title": "Conclusão", "min_words": 300, "min_citations": 0 }
  ]
}
```

---

## 4. Algoritmo de Auditoria SDD (`audit_project_against_spec`)

1. **Verificação da Camada 1 (Perfil Normativo, Institucional e Ilustrações):**
   - Executa `check_project_structure` respeitando `profile.standard` (`ABNT_14724` ou `ABNT_6022`).
   - Executa `audit_citations_and_references` e verifica se `total_references_in_bib >= profile.min_references`.
   - Executa `audit_project_illustrations_and_tables` verificando chamada prévia, `Fonte:`, imagens existentes e distinção `Tabela` vs `Quadro`.
   - Executa `analyze_scientific_tone` e verifica se `score >= profile.min_scientific_tone_score`.
   - Audita as regras institucionais de `NormativeProfile` (`required_pre_textual`, `has_cover_logo` / `cover_logo_path`, `conclusion_label`), emitindo diagnósticos com `nature="institutional"`.
2. **Verificação da Camada 2 (Cobertura dos Objetivos Específicos):**
   - Segmenta o texto do documento em: (a) Introdução, (b) Desenvolvimento/Corpo e (c) Conclusão/Considerações Finais.
   - Para cada `SpecificObjective` (`OBJ-XX`):
     - Extrai os termos de `keywords` (ou palavras substantivas >= 5 caracteres de `description` caso `keywords` esteja vazio).
     - Verifica presença no Desenvolvimento (`covered_in_body: bool`) e na Conclusão (`answered_in_conclusion: bool`).
     - Classifica o status do objetivo como `"fulfilled"` (presente no corpo e respondido na conclusão), `"partial"` (presente apenas no corpo ou apenas citado superficialmente) ou `"missing"` (ausente).
3. **Verificação da Camada 3 (Capítulos Planejados):**
   - Confere se cada capítulo listado em `planned_chapters` está presente no manuscrito.
4. **Cálculo do `spec_compliance_score` (0 a 100), `submission_readiness` e Persistência de Relatórios:**
   - Média ponderada entre: Conformidade Normativa Estrutural (35%), Cobertura de Objetivos Específicos (40%), Aderência aos Capítulos Planejados (15%) e Rigor/Referências (10%).
   - Calcula `submission_readiness`: `"READY"`, `"READY_WITH_WARNINGS"` ou `"NOT_READY"` (jamais `"READY"` quando houver erro normativo/institucional ou objetivo específico não atendido).
   - Persiste automaticamente `.abnt-mcp/last-audit.json` e `.abnt-mcp/relatorio-conformidade.md` no diretório do projeto.

---

## 5. Invariantes de Diagramação e Reatividade do Motor Typst

Para geração de projetos e compilação em formato Typst (`scaffold_academic_project` e `abnt://template/typst`), os templates devem observar estritamente:

1. **Quebra de Página em Capítulos Primários (`NBR14724` item 5.2.1):**
   - Títulos primários (`level: 1`) iniciam obrigatoriamente em folha distinta via `#show heading.where(level: 1): it => { pagebreak(weak: true); ... }`.
2. **Posição de Legendas (`NBR14724` item 5.8 / `IBGE 1993`):**
   - Identificação de ilustrações, tabelas e quadros posicionada no topo via `#show figure: set figure.caption(position: top)`. A fonte permanece indicada na base.
3. **Recuo de Parágrafos ABNT:**
   - Recuo obrigatório de 1,25 cm em todos os parágrafos de texto, inclusive no primeiro parágrafo após cada título, via `#set par(..., first-line-indent: (amount: 1.25cm, all: true))`.
4. **Espaçamento Entrelinhas Calibrado:**
   - Entrelinhas 1,5 real ABNT configurado no Typst como `#set par(leading: 0.75em)` (evitando valores literais `leading: 1.5em` que quadruplicam o entrelinhas tipográfico).
5. **Listas Pré-Textuais Reativas por Introspecção (`context query(...)`):**
   - As listas de Ilustrações (`figure.where(kind: image)`), Tabelas (`figure.where(kind: table)`) e Quadros (`figure.where(kind: "quadro")`) são geradas de forma condicional/reativa: só aparecem no PDF se houver itens presentes no texto, evitando páginas em branco ou listas vazias com títulos órfãos.
6. **Lista de Abreviaturas e Siglas com Diagramação Fluida (`#grid`):**
   - A Lista de Siglas utiliza `#grid(columns: (auto, 1fr), column-gutter: 1.2em, row-gutter: 1em, ...)` com travessão (`--`), adaptando-se dinamicamente à largura de cada sigla sem criar vãos horizontais excessivos e rígidos.
