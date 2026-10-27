"""Módulos de parsing de documentos, citações, BibTeX e PDFs."""

from abnt_mcp.parsers.citations import (
    extract_citations_from_latex,
    extract_citations_from_markdown,
    extract_citations_from_typst,
    extract_citations_from_project,
    detect_uppercase_citations,
    detect_redundant_typst_citation_parens,
    fix_redundant_typst_citation_parens,
)
from abnt_mcp.parsers.bibtex import (
    clean_latex_accents,
    extract_bib_keys_and_dois,
    sanitize_bibtex_string,
    append_entry_if_absent,
    normalize_abnt_month,
)
from abnt_mcp.parsers.pdf_reader import extract_pdf_section, audit_pdf_pagination

__all__ = [
    "extract_citations_from_latex",
    "extract_citations_from_markdown",
    "extract_citations_from_typst",
    "extract_citations_from_project",
    "detect_uppercase_citations",
    "detect_redundant_typst_citation_parens",
    "fix_redundant_typst_citation_parens",
    "clean_latex_accents",
    "extract_bib_keys_and_dois",
    "sanitize_bibtex_string",
    "append_entry_if_absent",
    "normalize_abnt_month",
    "extract_pdf_section",
    "audit_pdf_pagination",
]
