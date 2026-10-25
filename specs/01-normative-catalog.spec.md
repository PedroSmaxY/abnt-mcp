# Catálogo Normativo Executável (ABNT & IBGE)

> **Status:** CANÔNICO (`v1.0.0`)
> **Escopo:** Mapeamento formal entre as cláusulas das normas técnicas brasileiras (ABNT NBR e IBGE), os identificadores canônicos (`NORMATIVE_RULES` em `src/abnt_mcp/config.py`) e os módulos validadores do `abnt-mcp`.
> **Regra de Governança SDD:** Nenhuma regra normativa pode ser criada, alterada ou removida no código-fonte sem a atualização simultânea deste catálogo. O teste automatizado `test_sdd_anti_drift_normative_rules` em `tests/test_sdd.py` valida esta sincronia em CI/CD.

---

## 1. Matriz de Rastreabilidade de Regras Canônicas (`NORMATIVE_RULES`)

| ID Canônico | Norma Técnica | Cláusula / Item | Título da Regra | Severidade Padrão | Módulo Validador |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NBR14724-R01` | ABNT NBR 14724:2011 | Seção 4.2 | Elementos obrigatórios de monografias (Capa, Folha de Rosto, Resumo, Abstract, Sumário, Introdução, Desenvolvimento, Conclusão e Referências) | `error` | `pillars/diagnostics.py` |
| `NBR14724-R02` | ABNT NBR 14724:2011 | Seção 5.3 | Paginação física: contagem sequencial iniciada na Folha de Rosto, vedada numeração impressa em elementos pré-textuais e numeração arábica visível a partir da primeira folha textual | `critical` | `parsers/pdf_reader.py` |
| `NBR14724-R03` | ABNT NBR 14724:2011 | Seção 5.8 | Ilustrações: identificação na parte superior (`Figura X – Título`), chamada textual prévia obrigatória e indicação de fonte na parte inferior imediatamente acoplada ao elemento visual | `warning` | `pillars/writing.py` & `pillars/diagnostics.py` |
| `NBR14724-R04` | ABNT NBR 14724:2011 | Seção 5.9 | Equações e fórmulas: destacadas do texto, centralizadas, numeradas sequencialmente com algarismos arábicos entre parênteses à margem direita, e oração explicativa de variáveis ("onde...") com recuo zero e entrelinha simples | `warning` | `pillars/writing.py` |
| `NBR6022-R01` | ABNT NBR 6022:2018 | Seção 5 | Estrutura de artigo técnico-científico periódico: elementos pré-textuais contínuos (título, autoria, resumo, abstract), textuais (introdução, desenvolvimento, considerações finais) e pós-textuais (referências), dispensando capa, folha de rosto e sumário | `error` | `pillars/diagnostics.py` |
| `NBR10520-R01` | ABNT NBR 10520:2023 | Seção 4.2 | Sistema autor-data entre parênteses com grafia em caixa mista `(Silva, 2023)` — revogação expressa do padrão em CAIXA ALTA `(SILVA, 2023)` da edição de 2002 | `error` | `parsers/citations.py` |
| `NBR10520-R02` | ABNT NBR 10520:2023 | Seção 7.1 | Consistência cruzada estrita entre chamadas de citação no texto e entradas declaradas na lista de referências (`.bib`) | `error` | `pillars/diagnostics.py` |
| `NBR10520-R03` | ABNT NBR 10520:2023 | Seções 5.2 / 5.3 | Distinção tipográfica entre citação direta curta (até 3 linhas, entre aspas duplas no corpo do parágrafo, ponto final após a indicação da fonte) e direta longa (mais de 3 linhas, recuo de 4 cm, fonte menor, espaçamento simples e sem aspas) | `error` | `pillars/writing.py` |
| `NBR6023-R01` | ABNT NBR 6023:2018 | Anexo A (A.1) | Abreviatura padronizada dos meses em língua portuguesa nos três primeiros caracteres seguidos de ponto, exceto `maio` que deve ser grafado por extenso e sem ponto | `warning` | `parsers/bibtex.py` |
| `NBR6023-R02` | ABNT NBR 6023:2018 | Seção 6.2 | Alinhamento das referências exclusivamente à margem esquerda e destaque tipográfico (negrito ou itálico) restrito ao título principal, vedado no subtítulo | `error` | `pillars/writing.py` |
| `NBR6024-R01` | ABNT NBR 6024:2012 | Seção 4.1 | Numeração progressiva das seções: emprego de algarismos arábicos separados por ponto entre níveis, sem ponto final após o último algarismo antes do título (`1.1 Seção` e nunca `1.1. Seção`) | `warning` | `pillars/diagnostics.py` |
| `NBR6027-R01` | ABNT NBR 6027:2012 | Seção 4 | Sumário: enumeração exclusivamente a partir dos elementos textuais e pós-textuais; elementos pré-textuais não podem constar no sumário | `error` | `templates/` & `pillars/diagnostics.py` |
| `NBR6028-R01` | ABNT NBR 6028:2021 | Seção 3.3 | Resumo documental: parágrafo único contínuo na voz ativa e 3ª pessoa do singular, extensão de 150 a 500 palavras (trabalhos acadêmicos) ou 100 a 250 palavras (artigos), seguido de palavras-chave separadas por ponto e vírgula | `warning` | `pillars/writing.py` |
| `IBGE1993-R01` | Normas Tabulares IBGE (1993) | Seção 3.1 | Representação tabular: Tabelas (dados numéricos/estatísticos) possuem apenas linhas horizontais no topo, cabeçalho e base, com laterais esquerda e direita e linhas verticais internas abertas; Quadros (dados textuais/qualitativos) possuem todas as bordas fechadas em moldura | `error` | `pillars/writing.py` & `pillars/diagnostics.py` |

---

## 2. Invariantes Normativas Inegociáveis

1. **Proibição de CAIXA ALTA entre parênteses (`NBR10520-R01`):** Nenhum template, exemplo, prompt ou formatador pode gerar `(AUTOR, ANO)`. Apenas `(Autor, ano)` é válido segundo a ABNT NBR 10520:2023.
2. **Proibição de ponto após indicativo de seção (`NBR6024-R01`):** Títulos de seção seguem estritamente `<indicativo> <espaço> <Título>` (ex.: `2.1 Metodologia`).
3. **Invariante de Paginação (`NBR14724-R02`):** A capa nunca é contada; a contagem inicia na folha de rosto; números de página só são impressos a partir da primeira folha textual (Introdução), no canto superior direito.
4. **Abreviatura do mês de maio (`NBR6023-R01`):** O termo `mai.` com ponto é inválido; a única forma admitida em português pela NBR 6023:2018 é `maio`.

---

## 3. Modelo Unificado de Diagnóstico (`DiagnosticItem`)

Para garantir transparência científica e evitar que análises heurísticas sejam confundidas com exigências estritas da ABNT, todos os validadores emitem instâncias de `DiagnosticItem` (`src/abnt_mcp/models.py`) contendo:

- `rule_id`: Identificador canônico da regra (`NORMATIVE_RULES`, ex.: `NBR10520-R01`) ou código heurístico/institucional (`HEURISTIC-TONE-01`, `INST-PROFILE-01`).
- `nature`:
  - `"normative"`: Exigência formal de norma ABNT ou IBGE vigente.
  - `"heuristic"`: Recomendação estilística/editorial ou inferência textual que requer discernimento do autor.
  - `"institutional"`: Diretriz específica da universidade/periódico definida em `NormativeProfile`.
- `severity`: `"info"` | `"warning"` | `"error"` | `"critical"`.
- `confidence`: `"high"` | `"medium"` | `"low"`.
- `human_review_required`: `bool` (`False` para regras determinísticas exatas; `True` para análises heurísticas de linguagem e semântica).
