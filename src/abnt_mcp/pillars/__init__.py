"""Os 4 Pilares do ABNT Copilot MCP."""

from abnt_mcp.pillars.diagnostics import (
    check_project_structure,
    audit_citations_and_references,
    analyze_scientific_tone,
)
from abnt_mcp.pillars.writing import (
    format_citation_abnt,
    format_reference_abnt,
    generate_abnt_resumo,
    reformulate_to_impersonal,
)
from abnt_mcp.pillars.compiler import (
    compile_project,
    lint_latex_source,
    parse_latex_log_for_errors,
)
from abnt_mcp.pillars.advisory import (
    search_academic_literature,
    fetch_bibtex_by_doi_service,
    clean_bibtex_file_service,
    simulate_banca_examination,
)

__all__ = [
    "check_project_structure",
    "audit_citations_and_references",
    "analyze_scientific_tone",
    "format_citation_abnt",
    "format_reference_abnt",
    "generate_abnt_resumo",
    "reformulate_to_impersonal",
    "compile_project",
    "lint_latex_source",
    "parse_latex_log_for_errors",
    "search_academic_literature",
    "fetch_bibtex_by_doi_service",
    "clean_bibtex_file_service",
    "simulate_banca_examination",
]
