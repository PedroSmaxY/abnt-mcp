"""Modelos de dados Pydantic para validações e tipagem do ABNT Copilot MCP."""

from __future__ import annotations
from typing import Literal
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
    is_consistent: bool


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
    """Camada 1: Perfil normativo da especificação acadêmica."""
    document_type: Literal["tcc", "dissertacao", "tese", "artigo"] = "tcc"
    standard: Literal["ABNT_14724", "ABNT_6022"] = "ABNT_14724"
    institution: str | None = None
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
    spec_compliance_score: int = Field(..., ge=0, le=100)
    structure_score: int = Field(..., ge=0, le=100)
    objectives_fulfillment_rate: int = Field(..., ge=0, le=100)
    tone_score: int = Field(..., ge=0, le=100)
    references_count: int
    min_references_required: int
    objectives_audit: list[ObjectiveAuditItem]
    chapters_audit: list[ChapterAuditItem]
    normative_issues: list[dict[str, str]]
    recommendations: list[str]
