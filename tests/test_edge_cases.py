"""Testes aprofundados e de casos de borda para garantia de qualidade máxima."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from abnt_mcp.models import CitationInput, ReferenceInput, Author
from abnt_mcp.pillars.writing import (
    format_citation_abnt,
    format_reference_abnt,
    generate_abnt_resumo,
    format_figure_abnt,
    format_table_abnt,
)
from abnt_mcp.pillars.diagnostics import (
    check_project_structure,
    audit_citations_and_references,
    analyze_scientific_tone,
)
from abnt_mcp.pillars.compiler import (
    compile_project,
    convert_markdown_to_typst,
)
from abnt_mcp.pillars.advisory import (
    search_academic_literature,
    fetch_bibtex_by_doi_service,
    clean_bibtex_file_service,
)
from abnt_mcp.parsers.pdf_reader import extract_pdf_section
from abnt_mcp.parsers.bibtex import append_entry_if_absent, sanitize_bibtex_string
from abnt_mcp.server import (
    check_structure,
    validate_citations,
    compile_tcc,
    read_pdf_section,
    clean_bibtex_file,
    format_citation,
    format_reference,
    format_figure,
    format_table,
    analyze_tone,
    generate_academic_resumo,
    search_academic_papers,
    fetch_bibtex_by_doi,
)


# ==============================================================================
# 1. CASOS DE BORDA: WRITING & FORMATTING
# ==============================================================================

def test_format_citation_empty_author():
    data = CitationInput(authors=[" "], year=2024, style="in_parentheses")
    res = format_citation_abnt(data)
    assert "Autor Desconhecido" in res["formatted"]


def test_format_citation_three_authors_in_text():
    data = CitationInput(
        authors=["Silva", "Santos", "Costa"],
        year=2023,
        style="in_text",
        quote_type="indirect"
    )
    res = format_citation_abnt(data)
    assert res["formatted"] == "Silva, Santos e Costa (2023)"


def test_format_citation_three_authors_in_parentheses():
    data = CitationInput(
        authors=["Silva", "Santos", "Costa"],
        year=2023,
        style="in_parentheses",
        quote_type="indirect"
    )
    res = format_citation_abnt(data)
    assert res["formatted"] == "(Silva; Santos; Costa, 2023)"


def test_format_citation_locators():
    # Teste de localizador de e-book e legislação
    data_ebook = CitationInput(authors=["Dongo-Montoya"], year=2009, page="local. 264")
    res_ebook = format_citation_abnt(data_ebook)
    assert "(Dongo-Montoya, 2009, local. 264)" == res_ebook["formatted"]

    data_lei = CitationInput(authors=["Brasil"], year=1998, page="art. 49")
    res_lei = format_citation_abnt(data_lei)
    assert "(Brasil, 1998, art. 49)" == res_lei["formatted"]


def test_format_reference_thesis_and_website():
    ref_thesis = ReferenceInput(
        entry_type="thesis",
        title="Agentes Autônomos",
        subtitle="arquitetura e protocolos",
        year=2024,
        degree="Dissertação (Mestrado em Ciência da Computação)",
        institution="Universidade Federal",
        city="Curitiba",
        authors=[Author(first_name="Lucas", last_name="Ferreira")],
        emphasis_style="italic"
    )
    res_t = format_reference_abnt(ref_thesis)
    assert "*Agentes Autônomos*: arquitetura e protocolos." in res_t["formatted_reference"]
    assert "Dissertação (Mestrado em Ciência da Computação)" in res_t["formatted_reference"]

    ref_web = ReferenceInput(
        entry_type="website",
        title="Portal de Normas",
        year=2026,
        url="https://exemplo.org",
        access_date="24 out. 2026",
    )
    res_w = format_reference_abnt(ref_web)
    assert "Disponível em: <https://exemplo.org>" in res_w["formatted_reference"]
    assert "Acesso em: 24 out. 2026" in res_w["formatted_reference"]


def test_generate_abnt_resumo_english_and_length():
    # Teste em inglês
    res_en = generate_abnt_resumo(
        context="Context description in academic English.",
        objective="investigate the effects",
        methodology="empirical methodology with multiple cases",
        results="significant improvement",
        conclusion="the method is valid",
        keywords=["AI", "ABNT", "MCP"],
        language="en"
    )
    assert "**ABSTRACT**" in res_en["formatted_text"]
    assert "**Keywords:** AI; ABNT; MCP." in res_en["keywords_line"]

    # Teste de alerta de extensão insuficiente (<150 palavras)
    assert res_en["is_length_compliant"] is False
    assert "Atenção: O resumo contém" in res_en["message"]


def test_format_figure_windows_path_conversion():
    res = format_figure_abnt(
        image_path="C:\\Users\\pedro\\Images\\fluxo.png",
        caption="Diagrama de Sequência",
        source="Autor (2026).",
        figure_number="2.1"
    )
    # No LaTeX, o caminho deve usar barras normais para não corromper
    assert "C:/Users/pedro/Images/fluxo.png" in res["snippets"]["latex"]
    assert "Figura 2.1 – Diagrama de Sequência" in res["snippets"]["markdown"]


def test_format_table_versus_quadro():
    headers = ["Elemento", "Propriedade", "Status"]
    rows = [["Item 1", "Valor", "Ativo"], ["Item 2", "Valor 2", "Inativo"]]
    
    # Tabela (IBGE)
    tab = format_table_abnt("Estatística de Testes", headers, rows, category="tabela")
    assert tab["is_table"] is True
    assert "Tabela 1 – Estatística de Testes" in tab["snippets"]["markdown"]

    # Quadro (ABNT)
    quad = format_table_abnt("Glossário", headers, rows, category="quadro", table_number="3")
    assert quad["is_table"] is False
    assert "Quadro 3 – Glossário" in quad["snippets"]["markdown"]


# ==============================================================================
# 2. CASOS DE BORDA: DIAGNÓSTICO E AUDITORIA
# ==============================================================================

def test_check_project_structure_not_found():
    with pytest.raises(FileNotFoundError):
        check_project_structure("caminho_inexistente_12345")


def test_check_project_structure_on_pdf_file():
    pdf_path = Path(r"C:\Users\pedro\Documents\Normas_ABNT\exemplo_tcc\TCC_UTFPR_Fronchetti_ABNT_Correto.pdf")
    if pdf_path.exists():
        res = check_project_structure(pdf_path)
        assert res.is_valid is True
        assert res.compliance_score >= 80


def test_analyze_scientific_tone_ungrounded_long_paragraph():
    long_para = (
        "O avanço tecnológico contemporâneo estabeleceu uma multiplicidade de transformações estruturais "
        "nos mais diversos setores da sociedade da informação contemporânea. Novas ferramentas digitais emergem "
        "diariamente promovendo impactos profundos e alterando padrões consolidados sem qualquer questionamento crítico "
        "por parte dos agentes envolvidos no processo produtivo globalizado, gerando transformações substantivas e "
        "ampliando a complexidade dos ecossistemas industriais modernos de forma irreversível e ampla. "
        "Nesse sentido, constata-se a premência de investigar as variáveis determinantes desse fenômeno multifacetado, "
        "considerando as implicações metodológicas e operacionais observadas na prática corrente da engenharia."
    )
    res = analyze_scientific_tone(long_para)
    categories = [i.category for i in res.issues]
    assert "ungrounded_paragraph" in categories


# ==============================================================================
# 3. CASOS DE BORDA: COMPILADOR
# ==============================================================================

def test_compile_project_errors(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        compile_project(tmp_path / "nao_existe")

    empty_dir = tmp_path / "vazio"
    empty_dir.mkdir()
    res = compile_project(empty_dir, engine="auto")
    assert res["success"] is False
    assert "Nenhum arquivo" in res["error"]

    res_unknown = compile_project(empty_dir, engine="engine_invalido")
    assert res_unknown["success"] is False


def test_compile_project_markdown_direct_to_pdf(tmp_path: Path):
    # Compilação Markdown diretamente para PDF via Typst embutido
    md_file = tmp_path / "documento.md"
    md_file.write_text(
        "---\ntitle: 'Teste Acadêmico'\nauthor: 'Pesquisador'\n---\n\n# 1 Introdução\n\nTexto de introdução.\n",
        encoding="utf-8"
    )
    res = compile_project(md_file, engine="typst")
    assert res["success"] is True
    assert res["pdf_generated"] is not None
    assert Path(res["pdf_generated"]).exists()


def test_convert_markdown_to_typst():
    md_text = """---
title: "Meu Trabalho"
author: "Pesquisador"
---

# 1 Introdução
Texto de introdução com [@chave2024] e link <https://github.com>.

## 1.1 Objetivos
Objetivos específicos.
"""
    typ = convert_markdown_to_typst(md_text)
    assert '= 1 Introdução' in typ
    assert '== 1.1 Objetivos' in typ
    assert '@chave2024' in typ
    assert '<https://github.com>' not in typ  # limpo para evitar unclosed label


# ==============================================================================
# 4. CASOS DE BORDA: ADVISORY & BIBTEX
# ==============================================================================

def test_search_academic_literature_empty():
    assert search_academic_literature("") == []
    assert search_academic_literature("   ") == []


@patch("requests.get")
def test_search_academic_literature_network_error(mock_get):
    mock_get.side_effect = Exception("Falha de conexão")
    res = search_academic_literature("computação", source="all")
    assert res == []


@patch("requests.get")
def test_fetch_bibtex_by_doi_network_error(mock_get):
    mock_get.side_effect = Exception("Erro de rede")
    res = fetch_bibtex_by_doi_service("10.1234/test")
    assert res["success"] is False
    assert "Erro ao obter BibTeX" in res["error"]


def test_clean_bibtex_file_service_not_found():
    with pytest.raises(FileNotFoundError):
        clean_bibtex_file_service("arquivo_inexistente.bib")


def test_sanitize_bibtex_missing_fields():
    raw_bib = """
    @article{artigo_incompleto,
        title = {Título Sem Autor e Sem Periódico},
        year = {2024}
    }
    @book{livro_incompleto,
        title = {Livro Sem Autor e Sem Editora},
        year = {2023}
    }
    """
    cleaned, warnings = sanitize_bibtex_string(raw_bib)
    assert len(warnings) >= 2


# ==============================================================================
# 5. CASOS DE BORDA: FASTMCP TOOL CALLS
# ==============================================================================

def test_fastmcp_server_direct_tool_wrappers(tmp_path: Path):
    # Testa invocação das ferramentas registradas
    res_struct = check_structure(str(tmp_path))
    assert "compliance_score" in res_struct

    res_cite = validate_citations(str(tmp_path))
    assert "is_consistent" in res_cite

    res_tone = analyze_tone("Texto acadêmico impessoal devidamente fundamentado.")
    assert res_tone["score"] >= 80

    res_fig = format_figure("img.png", "Legenda", figure_number=1)
    assert "snippets" in res_fig

    res_tab = format_table("Título", ["A", "B"], [["1", "2"]], category="tabela")
    assert "snippets" in res_tab

    res_resumo = generate_academic_resumo(
        context="Contexto.", objective="objetivo.", methodology="método.",
        results="resultados.", conclusion="conclusão.", keywords=["A", "B", "C"]
    )
    assert "formatted_text" in res_resumo


# ==============================================================================
# 6. CASOS DE BORDA: AUDITORIA DE PAGINAÇÃO ABNT NBR 14724 (ITEM 5.3)
# ==============================================================================

def test_audit_pdf_pagination_compliant_tcc():
    pdf_path = Path(r"C:\Users\pedro\Documents\Normas_ABNT\exemplo_tcc\TCC_UTFPR_Fronchetti_ABNT_Correto.pdf")
    if pdf_path.exists():
        from abnt_mcp.parsers.pdf_reader import audit_pdf_pagination
        res = audit_pdf_pagination(pdf_path)
        assert res["is_compliant"] is True
        assert len(res["issues"]) == 0
        assert res["first_textual_page_pdf"] == 6


def test_audit_pdf_pagination_detects_pretextual_number(tmp_path: Path):
    import typst
    from abnt_mcp.parsers.pdf_reader import audit_pdf_pagination

    # Gera documento com número '2' impresso indevidamente no Sumário (pré-textual)
    typ_content = """
    #set page(paper: "a4", margin: (top: 3cm, left: 3cm, bottom: 2cm, right: 2cm), header: none)
    Capa
    #pagebreak()
    #counter(page).update(1)
    Folha de Rosto
    #pagebreak()
    // Erro proposital: ativa numeração no Sumário
    #set page(header: context { align(right)[#counter(page).get().first()] })
    #outline(title: [SUMÁRIO])
    #pagebreak()
    = 1 Introdução
    Texto da introdução.
    """
    typ_file = tmp_path / "bad_pretext.typ"
    pdf_file = tmp_path / "bad_pretext.pdf"
    typ_file.write_text(typ_content, encoding="utf-8")
    typst.compile(typ_file, output=str(pdf_file))

    res = audit_pdf_pagination(pdf_file)
    assert res["is_compliant"] is False
    issue_types = [i["type"] for i in res["issues"]]
    assert "pretextual_number_visible" in issue_types


def test_audit_pdf_pagination_detects_capa_counted(tmp_path: Path):
    import typst
    from abnt_mcp.parsers.pdf_reader import audit_pdf_pagination
    from abnt_mcp.pillars.diagnostics import check_project_structure

    # Gera documento onde a Capa foi contada como página 1 (sem o counter update na folha de rosto)
    typ_content = """
    #set page(paper: "a4", margin: (top: 3cm, left: 3cm, bottom: 2cm, right: 2cm), header: none)
    Capa
    #pagebreak()
    Folha de Rosto
    #pagebreak()
    Resumo
    #pagebreak()
    #outline(title: [SUMÁRIO])
    #pagebreak()
    // Ativa cabeçalho mas com offset porque a capa foi contada
    #set page(header: context { align(right)[#counter(page).get().first()] })
    = 1 Introdução
    Texto da introdução.
    """
    typ_file = tmp_path / "bad_capa_count.typ"
    pdf_file = tmp_path / "bad_capa_count.pdf"
    typ_file.write_text(typ_content, encoding="utf-8")
    typst.compile(typ_file, output=str(pdf_file))

    res = audit_pdf_pagination(pdf_file)
    assert res["is_compliant"] is False
    issue_types = [i["type"] for i in res["issues"]]
    assert "capa_counted_in_pagination" in issue_types

    # Validação via check_project_structure: deve penalizar e reprovar
    struct_res = check_project_structure(pdf_file)
    assert struct_res.is_valid is False
    assert any("[Paginação NBR 14724]" in w for w in struct_res.section_warnings)

