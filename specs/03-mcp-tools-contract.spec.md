# Contrato de Interfaces FastMCP (Tools, Prompts & Resources)

> **Status:** CANÔNICO (`v1.0.0`)
> **Escopo:** Especificação formal de todas as ferramentas (`@mcp.tool`), prompts (`@mcp.prompt`) e recursos (`@mcp.resource`) expostos em `src/abnt_mcp/server.py`.
> **Regra de Governança SDD:** Toda inclusão, renomeação ou remoção de interface em `src/abnt_mcp/server.py` obriga a atualização imediata deste contrato. O teste `test_sdd_anti_drift_mcp_surface` em `tests/test_sdd.py` valida esta paridade automaticamente.

---

## 1. Ferramentas Operacionais (`@mcp.tool`)

| Nome da Tool | Pilar / Módulo | Entrada Principal | Contrato de Saída (`dict` / `list`) |
| :--- | :--- | :--- | :--- |
| `search_academic_papers` | `pillars/advisory.py` | `query: str`, `source: "all"\|"crossref"\|"scielo"`, `limit: int = 5` | Lista de `AcademicPaper` (`title`, `authors`, `year`, `journal`, `doi`, `url`, `abstract`, `source`) |
| `fetch_bibtex_by_doi` | `pillars/advisory.py` | `doi: str`, `bib_file: str \| None = None` | `success`, `doi`, `bibtex`, `saved_to_file`, `file_status` |
| `validate_citations` | `pillars/diagnostics.py` | `project_path: str`, `bib_path: str \| None = None` | `CitationValidationResult` (`total_citations_in_text`, `total_references_in_bib`, `orphan_citations`, `unused_references`, `uppercase_violations`, `diagnostics`, `is_consistent`) |
| `check_structure` | `pillars/diagnostics.py` | `project_path: str`, `standard: str = "ABNT_14724"` | `StructureCheckResult` (`standard`, `is_valid`, `compliance_score`, `missing_mandatory`, `elements_found`, `section_warnings`, `rule_violations`, `diagnostics`, `recommendations`) |
| `audit_illustrations_and_tables` | `pillars/diagnostics.py` | `project_path: str` | `IllustrationAuditResult` (`is_valid`, `total_figures`, `total_tables`, `total_quadros`, `unreferenced_items`, `missing_sources`, `broken_image_paths`, `numbering_issues`, `quadro_vs_tabela_warnings`, `diagnostics`) |
| `compile_tcc` | `pillars/compiler.py` | `project_path: str`, `engine: "auto"\|"latex"\|"typst"\|"markdown" = "auto"` | `success`, `engine_used`, `pdf_path`, `errors`, `warnings`, `message` |
| `read_pdf_section` | `parsers/pdf_reader.py` | `pdf_path: str`, `pages: list[int] \| None`, `start_page: int \| None`, `end_page: int \| None` | `pdf_path`, `total_pages_in_pdf`, `extracted_pages`, `word_count`, `text`, `pages_detail` |
| `clean_bibtex_file` | `pillars/advisory.py` | `bib_path: str`, `output_path: str \| None = None` | `success`, `input_file`, `output_file`, `backup_path`, `corrections_made`, `total_corrections`, `message` |
| `format_citation` | `pillars/writing.py` | `authors: list[str]`, `year: str\|int`, `page: str\|None`, `style`, `quote_type`, `quote_text`, `target_format` | `citation_call`, `formatted_snippet`, `rule_applied`, `notes` |
| `format_reference` | `pillars/writing.py` | `entry_type`, `title`, `year`, `subtitle`, `authors`, `edition`, `city`, `publisher`, `journal_name`, ... | `entry_type`, `markdown`, `latex`, `plain_text`, `rule` |
| `analyze_tone` | `pillars/diagnostics.py` | `text: str` | `ToneAnalysisResult` (`score`, `is_acceptable`, `total_words`, `issues_count`, `issues`, `diagnostics`, `summary`, `suggested_rewrites`) |
| `generate_academic_resumo` | `pillars/writing.py` | `context`, `objective`, `methodology`, `results`, `conclusion`, `keywords`, `language` | `language`, `word_count`, `is_length_valid`, `formatted_text`, `latex_snippet`, `markdown_snippet` |
| `format_figure` | `pillars/writing.py` | `image_path`, `caption`, `source: str \| None = None` (default dinâmico por ano corrente), `figure_number`, `target_format` | `figure_number`, `in_text_call_suggestion`, `selected_snippet`, `markdown`, `latex`, `typst`, `abnt_rules_applied` |
| `format_table` | `pillars/writing.py` | `title`, `headers`, `rows`, `source: str \| None = None` (default dinâmico por ano corrente), `table_number`, `category` | `category`, `number`, `in_text_call_suggestion`, `normative_difference`, `markdown`, `latex`, `typst` |
| `init_research_spec` | `pillars/spec.py` | `project_path: str`, `title: str`, `research_problem: str`, `general_objective: str`, `specific_objectives: list[dict]`, `methodology_summary: str`, `document_type: str = "tcc"`, `author: str \| None = None`, `institution: str \| None = None`, `course: str \| None = None`, `advisor: str \| None = None`, `min_references: int \| None = None`, `planned_chapters: list[dict] \| None = None`, `sample_pdf_path: str \| None = None`, `logo_path: str \| None = None` | `success`, `spec_json_path`, `spec_md_path`, `spec` (`ResearchSpec` serializado), `inferred_institutional_profile`, `message` |
| `scaffold_academic_project` | `pillars/spec.py` | `project_path: str`, `title: str`, `author: str`, `document_type: "tcc"\|"dissertacao"\|"tese"\|"artigo" = "tcc"`, `format: "typst"\|"latex"\|"markdown" = "typst"`, `institution: str \| None = None`, `course: str \| None = None`, `advisor: str \| None = None`, `research_problem: str \| None = None`, `general_objective: str \| None = None`, `specific_objectives: list[dict] \| None = None`, `methodology_summary: str \| None = None`, `sample_pdf_path: str \| None = None`, `logo_path: str \| None = None`, `overwrite: bool = False` | `ProjectScaffoldResult` (`success`, `project_path`, `format`, `main_file`, `bib_file`, `spec_json_path`, `spec_md_path`, `cover_logo_path`, `created_files`, `inferred_institutional_profile`, `message`) |
| `audit_research_spec` | `pillars/spec.py` | `project_path: str`, `spec_path: str \| None = None` | `SpecAuditResult` (`is_compliant`, `submission_readiness`, `spec_compliance_score`, `document_type`, `standard_applied`, `institutional_compliance`, `illustrations_summary`, `objectives_audit`, `chapters_audit`, `normative_issues`, `diagnostics`, `recommendations`, `saved_report_paths`) |
| `simulate_banca` | `pillars/advisory.py` | `project_path: str` | `veredito`, `nota_global`, `pontuacao_por_eixo`, `estrutura_abnt`, `redacao`, `perguntas_da_banca`, `principais_recomendacoes`, `spec_alignment` |

---

## 2. Prompts Orientados (`@mcp.prompt`)

| Nome do Prompt | Parâmetros | Objetivo |
| :--- | :--- | :--- |
| `revisar_capitulo` | `texto: str`, `foco: str = "geral"` | Parecer técnico de revisão acadêmica com nota de rigor científico e reescrita impessoal |
| `formatar_citacao` | `trecho: str`, `autor: str`, `ano: str`, `pagina: str = ""`, `tipo: str = "direta_curta"` | Snippets prontos de citação conforme ABNT NBR 10520:2023 em Markdown, LaTeX e Typst |
| `simular_banca` | `projeto_path: str` | Instrução estruturada para arguição de banca examinadora |

---

## 3. Recursos Canônicos (`@mcp.resource`)

| URI do Resource | Função em `server.py` | Conteúdo |
| :--- | :--- | :--- |
| `abnt://guia/citacoes` | `resource_guia_citacoes` | Guia completo da ABNT NBR 10520:2023 |
| `abnt://guia/estrutura` | `resource_guia_estrutura` | Guia e checklist da ABNT NBR 14724:2011 e NBR 6024:2012 |
| `abnt://guia/referencias` | `resource_guia_referencias` | Matriz tipológica da ABNT NBR 6023:2018 |
| `abnt://guia/sdd` | `resource_guia_sdd` | Guia de Escrita Acadêmica Orientada a Especificação (SDD) e catálogo de regras |
| `abnt://template/latex` | `resource_template_latex` | Template funcional em LaTeX (abnTeX2) |
| `abnt://template/typst` | `resource_template_typst` | Template funcional em Typst com paginação NBR 14724 |
| `abnt://template/markdown` | `resource_template_markdown` | Template funcional para Pandoc Markdown |
| `abnt://template/spec` | `resource_template_spec` | Template JSON/Markdown do manifesto `abnt.spec.json` |
