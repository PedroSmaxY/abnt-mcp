"""Modelos de dados Pydantic para validações e tipagem do ABNT Copilot MCP."""

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class Author(BaseModel):
    """Representação estruturada de autor."""
    first_name: str = Field(default="", description="Prenome(s) do autor (ex: 'Maria Aparecida')")
    last_name: str = Field(..., description="Sobrenome do autor (ex: 'Silva')")


class CitationInput(BaseModel):
    """Parâmetros de formatação de citação conforme a NBR 10520:2023."""
    authors: list[str] = Field(
        ...,
        description="Lista de sobrenomes dos autores (ex: ['Silva', 'Santos'])",
        min_length=1
    )
    year: str | int = Field(..., description="Ano da publicação (ex: 2023)")
    page: str | None = Field(
        default=None,
        description="Página ou localizador (ex: '45', '12-15', 'local. 340')"
    )
    style: Literal["in_parentheses", "in_text"] = Field(
        default="in_parentheses",
        description="in_parentheses: (Silva, 2023, p. 10) | in_text: Silva (2023, p. 10)"
    )
    quote_type: Literal["direct_short", "direct_long", "indirect"] = Field(
        default="indirect",
        description="Tipo de citação: direta curta (<=3 linhas), direta longa (>3 linhas) ou indireta"
    )
    quote_text: str | None = Field(
        default=None,
        description="Texto citado na íntegra (necessário para citações diretas)"
    )
    target_format: Literal["markdown", "latex", "typst", "text"] = Field(
        default="markdown",
        description="Formato de saída gerado"
    )


class ReferenceInput(BaseModel):
    """Parâmetros para referência bibliográfica conforme a NBR 6023:2018."""
    entry_type: Literal[
        "book", "book_chapter", "journal_article", "website",
        "thesis", "legislation", "conference", "software"
    ] = Field(..., description="Tipo de documento referenciado")
    title: str = Field(..., description="Título principal da obra (receberá destaque)")
    subtitle: str | None = Field(default=None, description="Subtítulo (não recebe destaque)")
    authors: list[Author] | None = Field(default=None, description="Lista de autores")
    edition: str | None = Field(default=None, description="Ex: '3. ed.'")
    city: str | None = Field(default=None, description="Cidade de publicação")
    publisher: str | None = Field(default=None, description="Editora ou instituição")
    year: str | int = Field(..., description="Ano de publicação")
    journal_name: str | None = Field(default=None, description="Nome da revista ou periódico")
    volume: str | None = Field(default=None, description="Volume do periódico")
    number: str | None = Field(default=None, description="Número/fascículo do periódico")
    pages: str | None = Field(default=None, description="Páginas (ex: '45-60')")
    url: str | None = Field(default=None, description="Endereço eletrônico")
    access_date: str | None = Field(default=None, description="Data de acesso (ex: '24 out. 2026')")
    degree: str | None = Field(default=None, description="Grau acadêmico para teses/dissertações")
    institution: str | None = Field(default=None, description="Instituição de ensino para teses")
    emphasis_style: Literal["bold", "italic"] = Field(
        default="bold",
        description="Estilo de destaque do título (negrito ou itálico)"
    )


class DiagnosticItem(BaseModel):
    """Modelo unificado de diagnóstico (diferencia regra normativa estrita de heurística editorial)."""
    rule_id: str = Field(..., description="ID canônico (ex: 'NBR10520-R01') ou código heurístico ('HEURISTIC-TONE-01')")
    nature: Literal["normative", "heuristic", "institutional"] = Field(
        default="normative",
        description="Natureza do diagnóstico: normative (ABNT/IBGE), heuristic (editorial/IA) ou institutional"
    )
    severity: Literal["info", "warning", "error", "critical"] = "warning"
    confidence: Literal["high", "medium", "low"] = "high"
    message: str
    suggestion: str = ""
    file: str | None = None
    line: int | None = None
    human_review_required: bool = False


class ToneIssue(BaseModel):
    """Registro de inadequação de tom científico."""
    category: Literal["first_person", "value_judgment", "colloquialism", "ungrounded_paragraph"]
    term: str
    context: str
    line_number: int | None = None
    suggestion: str


class ToneAnalysisResult(BaseModel):
    """Resultado da análise de tom e rigor científico."""
    score: int = Field(..., ge=0, le=100, description="Nota de rigor científico (0 a 100)")
    is_acceptable: bool = Field(..., description="Se o texto atende ao padrão científico")
    total_words: int
    issues_count: int
    issues: list[ToneIssue]
    diagnostics: list[DiagnosticItem] = Field(
        default_factory=list,
        description="Diagnósticos unificados marcados como heuristic (requerem revisão humana)"
    )
    summary: str
    suggested_rewrites: list[dict[str, str]]


class StructureCheckResult(BaseModel):
    """Resultado da validação estrutural da NBR 14724 / NBR 6022."""
    standard: str = "NBR 14724:2011"
    is_valid: bool
    compliance_score: int = Field(..., ge=0, le=100)
    document_type: str = "TCC/Monografia/Dissertação"
    missing_mandatory: list[str]
    optional_elements_present: list[str]
    elements_found: list[str]
    section_warnings: list[str]
    rule_violations: list[dict[str, str]] = Field(
        default_factory=list,
        description="Lista de violações rastreáveis por ID canônico (ex: NBR14724-R01)"
    )
    diagnostics: list[DiagnosticItem] = Field(
        default_factory=list,
        description="Lista de diagnósticos unificados"
    )
    recommendations: list[str]


class CitationValidationResult(BaseModel):
    """Resultado da validação de citações vs referências."""
    total_citations_in_text: int
    total_references_in_bib: int
    orphan_citations: list[dict[str, str | int]] = Field(
        description="Citações presentes no texto mas ausentes no .bib"
    )
    unused_references: list[str] = Field(
        description="Chaves do .bib que nunca foram citadas no texto"
    )
    uppercase_violations: list[dict[str, str | int]] = Field(
        description="Citações em caixa alta no texto violando a NBR 10520:2023"
    )
    diagnostics: list[DiagnosticItem] = Field(
        default_factory=list,
        description="Lista de diagnósticos normativos de citações e referências"
    )
    is_consistent: bool


class IllustrationAuditResult(BaseModel):
    """Resultado da auditoria de figuras, tabelas e quadros (NBR 14724 item 5.8 e IBGE 1993)."""
    is_valid: bool
    total_figures: int = 0
    total_tables: int = 0
    total_quadros: int = 0
    unreferenced_items: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ilustrações, tabelas ou quadros declarados sem chamada prévia no texto"
    )
    missing_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Itens sem indicação obrigatória de 'Fonte:' na parte inferior"
    )
    broken_image_paths: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Caminhos de arquivos de imagem referenciados que não existem no disco"
    )
    numbering_issues: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Numeração fora de ordem sequencial ou duplicada"
    )
    quadro_vs_tabela_warnings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Alertas de confusão conceitual entre Tabela (quantitativo) e Quadro (qualitativo)"
    )
    diagnostics: list[DiagnosticItem] = Field(
        default_factory=list,
        description="Lista de diagnósticos unificados"
    )


class AcademicPaper(BaseModel):
    """Metadados de um artigo científico retornado por APIs de busca."""
    title: str
    authors: list[str]
    year: str | int | None = None
    journal: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    source: str


# ==============================================================================
# MODELOS DE SPEC-DRIVEN ACADEMIC WRITING (SDD)
# ==============================================================================

class NormativeProfile(BaseModel):
    """Camada 1: Perfil normativo e institucional da especificação acadêmica."""
    document_type: Literal["tcc", "dissertacao", "tese", "artigo"] = "tcc"
    standard: Literal["ABNT_14724", "ABNT_6022"] = "ABNT_14724"
    institution: str | None = None
    course: str | None = None
    department: str | None = None
    advisor: str | None = None
    city: str | None = Field(
        default=None,
        description="Cidade/Local da instituição exibida no rodapé da Capa e Folha de Rosto"
    )
    cover_header_lines: list[str] = Field(
        default_factory=list,
        description="Linhas superiores do cabeçalho da capa na ordem institucional"
    )
    has_cover_logo: bool = Field(
        default=False,
        description="Se a capa institucional utiliza logotipo/brasão"
    )
    cover_logo_path: str | None = Field(
        default=None,
        description="Caminho relativo da imagem da logo da instituição no projeto"
    )
    preamble_text: str | None = Field(
        default=None,
        description="Preâmbulo institucional completo da Folha de Rosto"
    )
    required_pre_textual: list[str] = Field(
        default_factory=list,
        description="Elementos pré-textuais adicionais exigidos pela instituição"
    )
    conclusion_label: str = Field(
        default="Conclusão",
        description="Rótulo adotado para a seção conclusiva ('Conclusão' ou 'Considerações Finais')"
    )
    inferred_from_pdf: bool = Field(
        default=False,
        description="Se os padrões institucionais foram extraídos automaticamente de um PDF modelo"
    )
    emphasis_style: Literal["bold", "italic"] = "bold"
    min_references: int = Field(default=15, ge=1)
    min_scientific_tone_score: int = Field(default=80, ge=0, le=100)


class SpecificObjective(BaseModel):
    """Camada 2: Objetivo específico rastreável na matriz científica."""
    id: str = Field(..., description="Identificador canônico, ex: 'OBJ-01'")
    description: str = Field(..., description="Enunciado formal do objetivo específico")
    keywords: list[str] = Field(
        default_factory=list,
        description="Termos/conceitos-chave que comprovam discussão e resolução do objetivo"
    )
    target_section: str | None = Field(
        default=None,
        description="Seção ou capítulo responsável por desenvolver este objetivo"
    )


class PlannedChapter(BaseModel):
    """Camada 3: Capítulo ou seção planejada na estrutura do manuscrito."""
    number: str = Field(..., description="Indicativo numérico (ex: '1', '2', '2.1')")
    title: str = Field(..., description="Título planejado do capítulo/seção")
    min_words: int = Field(default=200, ge=0)
    min_citations: int = Field(default=1, ge=0)


class ResearchSpec(BaseModel):
    """Manifesto de Especificação Científica (abnt.spec.json)."""
    spec_version: str = "1.0"
    title: str
    author: str | None = None
    research_problem: str = Field(..., description="Pergunta de partida / problema de pesquisa")
    general_objective: str = Field(..., description="Objetivo geral do estudo")
    methodology_summary: str = Field(..., description="Abordagem, método e procedimentos")
    specific_objectives: list[SpecificObjective] = Field(..., min_length=1)
    profile: NormativeProfile = Field(default_factory=NormativeProfile)
    planned_chapters: list[PlannedChapter] = Field(default_factory=list)


class ObjectiveAuditItem(BaseModel):
    """Resultado de auditoria individual de um objetivo específico (OBJ-XX)."""
    id: str
    description: str
    status: Literal["fulfilled", "partial", "missing"]
    covered_in_body: bool
    answered_in_conclusion: bool
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    feedback: str


class ChapterAuditItem(BaseModel):
    """Resultado de auditoria de um capítulo planejado."""
    number: str
    title: str
    found_in_document: bool
    feedback: str


class SpecAuditResult(BaseModel):
    """Relatório consolidado de auditoria orientada a especificação (SDD)."""
    spec_path: str
    title: str
    document_type: str
    standard_applied: str
    is_compliant: bool
    submission_readiness: Literal["READY", "READY_WITH_WARNINGS", "NOT_READY"] = "NOT_READY"
    spec_compliance_score: int = Field(..., ge=0, le=100)
    structure_score: int = Field(..., ge=0, le=100)
    objectives_fulfillment_rate: int = Field(..., ge=0, le=100)
    tone_score: int = Field(..., ge=0, le=100)
    references_count: int
    min_references_required: int
    institutional_compliance: dict[str, Any] = Field(
        default_factory=dict,
        description="Status de conformidade com as exigências específicas da universidade/periódico"
    )
    illustrations_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Resumo da auditoria de figuras, tabelas e quadros"
    )
    objectives_audit: list[ObjectiveAuditItem]
    chapters_audit: list[ChapterAuditItem]
    normative_issues: list[dict[str, str]]
    diagnostics: list[DiagnosticItem] = Field(
        default_factory=list,
        description="Lista consolidada de diagnósticos (normativos, institucionais e heurísticos)"
    )
    recommendations: list[str]
    saved_report_paths: dict[str, str] = Field(
        default_factory=dict,
        description="Caminhos dos relatórios persistidos em .abnt-mcp/ (JSON e Markdown)"
    )


class ProjectScaffoldResult(BaseModel):
    """Resultado do scaffolding estrutural de um projeto acadêmico SDD."""
    success: bool
    project_path: str
    format: Literal["typst", "latex", "markdown"]
    main_file: str
    bib_file: str
    spec_json_path: str
    spec_md_path: str
    cover_logo_path: str | None = None
    created_files: list[str] = Field(default_factory=list)
    inferred_institutional_profile: dict[str, Any] | None = None
    message: str
