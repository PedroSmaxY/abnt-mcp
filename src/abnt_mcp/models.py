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
    """Resultado da validação estrutural da NBR 14724."""
    standard: str = "NBR 14724:2011"
    is_valid: bool
    compliance_score: int = Field(..., ge=0, le=100)
    document_type: str = "TCC/Monografia/Dissertação"
    missing_mandatory: list[str]
    optional_elements_present: list[str]
    elements_found: list[str]
    section_warnings: list[str]
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
