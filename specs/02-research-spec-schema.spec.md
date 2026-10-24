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

### Camada 1: Perfil Normativo (`NormativeProfile`)
Define sob qual regime normativo o projeto deve ser validado:
- `document_type`: `"tcc"` | `"dissertacao"` | `"tese"` | `"artigo"` (padrão: `"tcc"`).
- `standard`: `"ABNT_14724"` (monografias completas) | `"ABNT_6022"` (artigos científicos periódicos).
- `institution`: Nome da universidade, faculdade ou periódico (opcional).
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

1. **Verificação da Camada 1 (Perfil Normativo):**
   - Executa `check_project_structure` respeitando `profile.standard` (`ABNT_14724` ou `ABNT_6022`).
   - Executa `audit_citations_and_references` e verifica se `total_references_in_bib >= profile.min_references`.
   - Executa `analyze_scientific_tone` e verifica se `score >= profile.min_scientific_tone_score`.
2. **Verificação da Camada 2 (Cobertura dos Objetivos Específicos):**
   - Segmenta o texto do documento em: (a) Introdução, (b) Desenvolvimento/Corpo e (c) Conclusão/Considerações Finais.
   - Para cada `SpecificObjective` (`OBJ-XX`):
     - Extrai os termos de `keywords` (ou palavras substantivas >= 5 caracteres de `description` caso `keywords` esteja vazio).
     - Verifica presença no Desenvolvimento (`covered_in_body: bool`) e na Conclusão (`answered_in_conclusion: bool`).
     - Classifica o status do objetivo como `"fulfilled"` (presente no corpo e respondido na conclusão), `"partial"` (presente apenas no corpo ou apenas citado superficialmente) ou `"missing"` (ausente).
3. **Verificação da Camada 3 (Capítulos Planejados):**
   - Confere se cada capítulo listado em `planned_chapters` está presente no manuscrito.
4. **Cálculo do `spec_compliance_score` (0 a 100):**
   - Média ponderada entre: Conformidade Normativa Estrutural (35%), Cobertura de Objetivos Específicos (40%), Aderência aos Capítulos Planejados (15%) e Rigor/Referências (10%).
