"""Testes para o Pilar 2: Redigir & Reformular."""

from abnt_mcp.models import CitationInput, ReferenceInput, Author
from abnt_mcp.pillars.writing import (
    format_citation_abnt,
    format_reference_abnt,
    generate_abnt_resumo,
    reformulate_to_impersonal,
)


def test_format_citation_one_author_nbr10520_2023():
    # Deve usar caixa mista/baixa e NUNCA caixa alta!
    data = CitationInput(
        authors=["SILVA"],
        year=2023,
        page="15",
        style="in_parentheses",
        quote_type="indirect",
    )
    res = format_citation_abnt(data)
    assert res["formatted"] == "(Silva, 2023, p. 15)"
    assert "SILVA" not in res["formatted"]


def test_format_citation_two_authors():
    data_parentheses = CitationInput(
        authors=["silva", "santos"],
        year=2023,
        style="in_parentheses",
    )
    res_p = format_citation_abnt(data_parentheses)
    assert res_p["formatted"] == "(Silva; Santos, 2023)"

    data_inline = CitationInput(
        authors=["silva", "santos"],
        year=2023,
        style="in_text",
    )
    res_i = format_citation_abnt(data_inline)
    assert res_i["formatted"] == "Silva e Santos (2023)"


def test_format_citation_four_or_more_authors():
    data = CitationInput(
        authors=["Silva", "Santos", "Costa", "Oliveira"],
        year=2023,
        style="in_parentheses",
    )
    res = format_citation_abnt(data)
    assert res["formatted"] == "(Silva et al., 2023)"


def test_format_citation_direct_short():
    data = CitationInput(
        authors=["Pereira"],
        year=2024,
        page="10",
        quote_type="direct_short",
        quote_text="O protocolo MCP conecta dados a agentes.",
        style="in_parentheses",
    )
    res = format_citation_abnt(data)
    # Ponto final deve vir após os parênteses
    assert res["formatted"] == "“O protocolo MCP conecta dados a agentes.” (Pereira, 2024, p. 10)."


def test_format_citation_direct_long():
    text = "Citação extensa que ultrapassa três linhas inteiras no documento impresso necessitando de recuo de quatro centímetros e fonte de tamanho dez."
    data = CitationInput(
        authors=["Pereira"],
        year=2024,
        page="112",
        quote_type="direct_long",
        quote_text=text,
        target_format="latex",
    )
    res = format_citation_abnt(data)
    assert r"\begin{citacao}" in res["formatted"]
    assert "(Pereira, 2024, p. 112)." in res["formatted"]
    assert "“" not in res["formatted"]  # Sem aspas em citação longa


def test_format_reference_book_title_emphasis_only():
    # Apenas o título principal recebe destaque; o subtítulo NÃO recebe
    ref_data = ReferenceInput(
        entry_type="book",
        title="Metodologia da Pesquisa Científica",
        subtitle="guia prático para universitários",
        authors=[Author(first_name="Maria Aparecida", last_name="Silva")],
        edition="3. ed.",
        city="São Paulo",
        publisher="Atlas",
        year=2021,
    )
    res = format_reference_abnt(ref_data)
    formatted = res["formatted_reference"]
    assert "SILVA, Maria Aparecida." in formatted
    assert "**Metodologia da Pesquisa Científica**: guia prático para universitários." in formatted
    assert "São Paulo: Atlas, 2021." in formatted


def test_format_reference_article():
    ref_data = ReferenceInput(
        entry_type="journal_article",
        title="Modelos de Linguagem e Raciocínio",
        journal_name="Revista de Informática Aplicada",
        volume="12",
        number="3",
        pages="100-115",
        year=2023,
        authors=[
            Author(first_name="João", last_name="Alves"),
            Author(first_name="Beatriz", last_name="Lima")
        ]
    )
    res = format_reference_abnt(ref_data)
    formatted = res["formatted_reference"]
    assert "ALVES, João; LIMA, Beatriz." in formatted
    assert "**Revista de Informática Aplicada**" in formatted


def test_generate_abnt_resumo():
    res = generate_abnt_resumo(
        context="A inteligência artificial tem proporcionado novos métodos de automação documental no meio acadêmico contemporâneo.",
        objective="analisar a efetividade da aplicação do protocolo MCP na elaboração de trabalhos de conclusão de curso segundo a ABNT",
        methodology="uma pesquisa quantitativa e qualitativa com cinquenta documentos acadêmicos submetidos a validação cruzada",
        results="uma redução de noventa por cento nos erros de citação órfã e inconsistências de numeração progressiva de seções",
        conclusion="a utilização de assistentes integrados eleva a conformidade normativa e diminui retrabalhos dos orientandos",
        keywords=["Inteligência Artificial", "Normas ABNT", "Model Context Protocol", "Escrita Científica"],
        language="pt"
    )
    assert "**RESUMO**" in res["formatted_text"]
    assert "**Palavras-chave:**" in res["keywords_line"]
    assert ";" in res["keywords_line"]
    assert res["keywords_line"].endswith(".")
    assert res["word_count"] > 50


def test_reformulate_to_impersonal():
    text = "Nós analisamos os dados e eu fiz um script que achamos muito bom."
    res = reformulate_to_impersonal(text)
    assert "analisou-se" in res["reformulated"].lower()
    assert "realizou-se" in res["reformulated"].lower()
    assert res["changes_count"] >= 2
