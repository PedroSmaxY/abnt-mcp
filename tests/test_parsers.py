"""Testes para os módulos de parsing (citações, BibTeX, PDF)."""

from pathlib import Path
import io
import pytest
from pypdf import PdfWriter

from abnt_mcp.parsers.citations import (
    extract_citations_from_latex,
    extract_citations_from_markdown,
    extract_citations_from_typst,
    detect_uppercase_citations,
    detect_redundant_typst_citation_parens,
    fix_redundant_typst_citation_parens,
    extract_citations_from_project,
)
from abnt_mcp.parsers.bibtex import (
    clean_latex_accents,
    extract_bib_keys_and_dois,
    sanitize_bibtex_string,
    append_entry_if_absent,
    normalize_abnt_month,
)
from abnt_mcp.parsers.pdf_reader import extract_pdf_section


def test_extract_citations_from_latex():
    latex_text = r"""
    Conforme \citeonline{silva2020}, os métodos são eficientes.
    Outros estudos confirmam isso \cite{souza2021, santos2022}.
    Citando uma obra anterior \apud[p. 15]{freire1968}{almeida2019}.
    % Linha comentada com \cite{falsa_chave}
    """
    citations = extract_citations_from_latex(latex_text)
    keys = [c[0] for c in citations]
    assert "silva2020" in keys
    assert "souza2021" in keys
    assert "santos2022" in keys
    assert "freire1968" in keys
    assert "falsa_chave" not in keys  # ignorado por estar em comentário


def test_extract_citations_from_markdown():
    md_text = """
    Segundo [@pereira2023, p. 45], o resultado foi satisfatório.
    Vários autores abordam o assunto [@artigo1; @artigo2].
    Conforme @lima2024 demonstrou recentemente no texto.
    """
    citations = extract_citations_from_markdown(md_text)
    keys = [c[0] for c in citations]
    assert "pereira2023" in keys
    assert "artigo1" in keys
    assert "artigo2" in keys
    assert "lima2024" in keys


def test_extract_citations_from_typst():
    typst_text = """
    Conforme @melo2023 os dados são consistentes.
    // Comentário @falso_typst
    Outra citação @castro2021 aqui.
    """
    citations = extract_citations_from_typst(typst_text)
    keys = [c[0] for c in citations]
    assert "melo2023" in keys
    assert "castro2021" in keys
    assert "falso_typst" not in keys


def test_detect_uppercase_citations():
    text = "O aprendizado foi rápido (SILVA, 2021, p. 10) e também (SANTOS; COSTA, 2022)."
    violations = detect_uppercase_citations(text)
    assert len(violations) == 2
    assert "SILVA" in violations[0]["found"]
    assert "Silva" in violations[0]["suggested"]


def test_detect_and_fix_redundant_typst_citation_parens():
    """Valida detecção e autofix de parênteses duplos em citações Typst (NBR10520-R05)."""
    typst_code = """
    Como apontado em (@silva2023), os resultados mostram consistência.
    Outros autores (@santos2022; @lima2021) corroboram a mesma tese.
    Já esta citação está correta @pereira2020.
    // Comentário (@ignorado2020)
    """
    violations = detect_redundant_typst_citation_parens(typst_code)
    assert len(violations) == 2
    assert violations[0]["found"] == "(@silva2023)"
    assert violations[0]["suggested"] == "@silva2023"
    assert violations[1]["found"] == "(@santos2022; @lima2021)"
    assert violations[1]["suggested"] == "@santos2022 @lima2021"

    fixed, count = fix_redundant_typst_citation_parens(typst_code)
    assert count == 2
    assert "(@silva2023)" not in fixed
    assert "@silva2023" in fixed
    assert "@santos2022 @lima2021" in fixed


def test_clean_latex_accents():
    raw = r"Metodologia avan\c{c}ada com intelig\^encia artificial e ci\^encia."
    cleaned = clean_latex_accents(raw)
    assert "avançada" in cleaned
    assert "inteligência" in cleaned
    assert "ciência" in cleaned


def test_normalize_abnt_month():
    assert normalize_abnt_month("mai.") == "maio"
    assert normalize_abnt_month("may") == "maio"
    assert normalize_abnt_month("jan") == "jan."
    assert normalize_abnt_month("01") == "jan."
    assert normalize_abnt_month("dezembro") == "dez."


def test_sanitize_bibtex_string(sample_bib_content):
    cleaned, warnings = sanitize_bibtex_string(sample_bib_content)
    assert "maio" in cleaned.lower()
    assert len(warnings) > 0


def test_append_entry_if_absent(tmp_path: Path):
    bib_file = tmp_path / "referencias.bib"
    entry1 = "@article{key1, title = {Título 1}, year = {2023}, doi = {10.1234/test1}}\n"
    res1 = append_entry_if_absent(bib_file, entry1)
    assert res1["inserted"] is True
    assert res1["status"] == "created"

    # Tentativa de duplicar mesmo DOI
    entry_dup_doi = "@article{key_diff, title = {Título Diferente}, year = {2024}, doi = {10.1234/test1}}\n"
    res2 = append_entry_if_absent(bib_file, entry_dup_doi)
    assert res2["inserted"] is False
    assert res2["status"] == "duplicate_doi"

    # Inserção de chave coincidente com DOI diferente
    entry_same_key = "@article{key1, title = {Outro}, year = {2025}, doi = {10.1234/novo}}\n"
    res3 = append_entry_if_absent(bib_file, entry_same_key)
    assert res3["inserted"] is True
    assert "key1_new" in bib_file.read_text(encoding="utf-8")


def test_pdf_reader(tmp_path: Path):
    pdf_file = tmp_path / "teste.pdf"
    writer = PdfWriter()
    page1 = writer.add_blank_page(width=595, height=842)
    # pypdf blank page
    with open(pdf_file, "wb") as f:
        writer.write(f)

    data = extract_pdf_section(pdf_file)
    assert data["total_pages"] == 1
    assert data["is_scanned"] is True
