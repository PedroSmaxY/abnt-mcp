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


def test_format_figure():
    from abnt_mcp.pillars.writing import format_figure_abnt
    res = format_figure_abnt(
        image_path="images/diagrama.png",
        caption="Arquitetura do Modelo",
        source="Dados da pesquisa (2026).",
        figure_number=1,
    )
    assert res["standard"] == "ABNT NBR 14724:2011"
    assert "Figura 1 – Arquitetura do Modelo" in res["snippets"]["markdown"]
    assert "\\caption{Arquitetura do Modelo}" in res["snippets"]["latex"]
    assert "images/diagrama.png" in res["snippets"]["latex"]
    assert "Fonte: Dados da pesquisa (2026)." in res["snippets"]["markdown"]
    # Blindagem contra órfãos e respiro de 1.2cm com acoplamento da fonte
    assert "#block(spacing: 1.2cm, breakable: false)" in res["snippets"]["typst"]
    assert "#v(0.2cm)" in res["snippets"]["typst"]


def test_format_table_and_quadro():
    from abnt_mcp.pillars.writing import format_table_abnt
    # Tabela (IBGE: laterais abertas e linhas horizontais no topo, cabeçalho e base)
    res_tab = format_table_abnt(
        title="Distribuição Amostral",
        headers=["Categoria", "Quantidade"],
        rows=[["A", "10"], ["B", "20"]],
        source="IBGE (2022).",
        table_number=1,
        category="tabela",
    )
    assert res_tab["is_table"] is True
    assert "Tabela 1 – Distribuição Amostral" in res_tab["snippets"]["markdown"]
    assert "\\toprule" in res_tab["snippets"]["latex"]
    assert 'kind: "quadro"' not in res_tab["snippets"]["typst"]
    assert "#block(spacing: 1.2cm, breakable: false)" in res_tab["snippets"]["typst"]
    assert "left: none" in res_tab["snippets"]["typst"]
    assert "right: none" in res_tab["snippets"]["typst"]
    assert "top: if y == 0 { 0.8pt }" in res_tab["snippets"]["typst"]
    assert "bottom: if y == 2 { 0.8pt }" in res_tab["snippets"]["typst"]
    assert "#v(0.2cm)" in res_tab["snippets"]["typst"]

    # Quadro (ABNT: bordas fechadas)
    res_quad = format_table_abnt(
        title="Comparativo Conceitual",
        headers=["Conceito", "Definição"],
        rows=[["MCP", "Protocolo"], ["LLM", "Modelo"]],
        source="Autor (2026).",
        table_number=1,
        category="quadro",
    )
    assert res_quad["is_table"] is False
    assert "Quadro 1 – Comparativo Conceitual" in res_quad["snippets"]["markdown"]
    assert "\\hline" in res_quad["snippets"]["latex"]
    assert 'kind: "quadro"' in res_quad["snippets"]["typst"]
    assert "supplement: [Quadro]" in res_quad["snippets"]["typst"]
    assert "#block(spacing: 1.2cm, breakable: false)" in res_quad["snippets"]["typst"]
    assert "stroke: 0.5pt" in res_quad["snippets"]["typst"]
    assert "#v(0.2cm)" in res_quad["snippets"]["typst"]


def test_format_equation_nbr14724_r04():
    """Valida NBR14724-R04: equações centralizadas, numeradas à direita e variáveis sem recuo."""
    from abnt_mcp.pillars.writing import format_equation_abnt
    from abnt_mcp.server import format_equation

    # 1. Equação com lista de variáveis
    res = format_equation_abnt(
        expression="E = m c^2",
        equation_number=1,
        variable_definitions=[
            "E é a energia (Joules);",
            "m é a massa do corpo (quilogramas);",
            "c é a velocidade da luz no vácuo (m/s)."
        ],
        label="eq:energia",
        target_format="typst"
    )

    assert res["rule_id"] == "NBR14724-R04"
    assert res["standard"] == "ABNT NBR 14724:2011"
    assert res["equation_number"] == 1
    assert "Conforme apresentado na Equação (1)" in res["text_call_example"]

    # Typst: #block(spacing: 1.2cm, breakable: false), $ E = m c^2 $ <eq:energia>, e first-line-indent: 0cm na frase explicativa
    typ_code = res["snippets"]["typst"]
    assert "#block(spacing: 1.2cm, breakable: false)" in typ_code
    assert "$ E = m c^2 $ <eq:energia>" in typ_code
    assert "first-line-indent: 0cm" in typ_code
    assert "leading: 0.49em" in typ_code
    assert "#text(size: 10pt)" in typ_code
    assert "onde:\\" in typ_code
    assert "#h(0.5cm) E é a energia (Joules);" in typ_code

    # LaTeX: \begin{equation}, \noindent onde:, e \item
    tex_code = res["snippets"]["latex"]
    assert "\\begin{equation}" in tex_code
    assert "E = m c^2" in tex_code
    assert "\\label{eq:energia}" in tex_code
    assert "\\noindent onde:" in tex_code
    assert "\\item E é a energia (Joules);" in tex_code

    # Markdown: $$ ... \tag{1} $$ e <p style="text-indent: 0;">onde:</p>
    md_code = res["snippets"]["markdown"]
    assert "$$\nE = m c^2 \\tag{1}\n$$" in md_code
    assert 'style="text-indent: 0;"' in md_code

    # 2. Teste via wrapper de tool no FastMCP
    tool_res = format_equation(
        expression="f(x) = a x + b",
        equation_number=2,
        variable_definitions="onde:\na é o coeficiente angular;\nb é o coeficiente linear.",
        target_format="typst"
    )
    assert tool_res["rule_id"] == "NBR14724-R04"
    assert tool_res["selected_snippet"] == tool_res["snippets"]["typst"]
    assert "$ f(x) = a x + b $ <eq:equacao2>" in tool_res["snippets"]["typst"]
    assert "a é o coeficiente angular;" in tool_res["snippets"]["typst"]

