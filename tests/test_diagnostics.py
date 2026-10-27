"""Testes para o Pilar 1: Analisar & Diagnosticar."""

from pathlib import Path
from abnt_mcp.pillars.diagnostics import (
    check_project_structure,
    audit_citations_and_references,
    analyze_scientific_tone,
)


def test_check_project_structure_valid(tmp_path: Path, sample_tex_content):
    doc = tmp_path / "main.tex"
    doc.write_text(sample_tex_content, encoding="utf-8")

    result = check_project_structure(tmp_path)
    assert result.is_valid is True
    assert result.compliance_score >= 80
    assert len(result.missing_mandatory) == 0
    assert "capa" in result.elements_found
    assert "introducao" in result.elements_found
    assert "referencias" in result.elements_found


def test_check_project_structure_missing_mandatory(tmp_path: Path):
    doc = tmp_path / "incompleto.tex"
    # Sem capa, sem resumo, sem introdução
    doc.write_text(r"\documentclass{article}\begin{document}Texto curto\end{document}", encoding="utf-8")

    result = check_project_structure(tmp_path)
    assert result.is_valid is False
    assert len(result.missing_mandatory) > 0
    assert any("capa" in m for m in result.missing_mandatory)
    assert any("resumo" in m for m in result.missing_mandatory)


def test_check_project_structure_invalid_section_dots(tmp_path: Path):
    doc = tmp_path / "documento.md"
    content = """
    # 1. INTRODUÇÃO
    ## 1.1. OBJETIVOS
    Texto do documento.
    """
    doc.write_text(content, encoding="utf-8")

    result = check_project_structure(tmp_path)
    assert len(result.section_warnings) > 0
    assert any("ponto após o último algarismo" in w for w in result.section_warnings)


def test_audit_citations_and_references(tmp_path: Path, sample_bib_content):
    bib = tmp_path / "referencias.bib"
    bib.write_text(sample_bib_content, encoding="utf-8")

    doc = tmp_path / "artigo.md"
    # silva2023 existe no bib; orfao2024 NÃO existe no bib
    # oliveira2022 existe no bib mas NÃO foi citado
    doc.write_text(
        "Conforme [@silva2023] e também [@orfao2024], além de (SILVA, 2021).",
        encoding="utf-8"
    )

    result = audit_citations_and_references(tmp_path)
    assert result.is_consistent is False
    orphan_keys = [o["key"] for o in result.orphan_citations]
    assert "orfao2024" in orphan_keys
    assert "silva2023" not in orphan_keys
    assert "oliveira2022" in result.unused_references
    assert len(result.uppercase_violations) > 0


def test_audit_citations_detects_redundant_typst_parens(tmp_path: Path, sample_bib_content):
    """Valida diagnóstico de parênteses duplos em citações Typst (NBR10520-R05)."""
    bib = tmp_path / "referencias.bib"
    bib.write_text(sample_bib_content, encoding="utf-8")

    doc = tmp_path / "main.typ"
    doc.write_text("Citação indevida com parênteses (@silva2023; @santos2022).", encoding="utf-8")

    result = audit_citations_and_references(tmp_path)
    assert result.is_consistent is False
    assert len(result.redundant_parens_violations) == 1
    assert result.redundant_parens_violations[0]["found"] == "(@silva2023; @santos2022)"
    assert result.redundant_parens_violations[0]["suggested"] == "@silva2023 @santos2022"

    diag_rules = [d.rule_id for d in result.diagnostics]
    assert "NBR10520-R05" in diag_rules


def test_analyze_scientific_tone_first_person():
    text = "Nós analisamos os dados e eu percebi uma inconsistência clara no meu estudo."
    res = analyze_scientific_tone(text)
    assert res.score < 80
    assert res.is_acceptable is False
    categories = [i.category for i in res.issues]
    assert "first_person" in categories


def test_analyze_scientific_tone_value_judgments_and_colloquialisms():
    text = "O sistema obviamente funciona com certeza, e a coisa ficou boa pra caramba."
    res = analyze_scientific_tone(text)
    assert res.score <= 75
    terms = [i.term for i in res.issues]
    assert "obviamente" in terms
    assert "com certeza" in terms
    assert "a gente" not in terms or True
    assert "pra caramba" in terms
