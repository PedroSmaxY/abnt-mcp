"""Pilar 2: Redigir & Reformular.

Formatador de Citações (NBR 10520:2023), Formatador de Referências (NBR 6023:2018),
Gerador de Resumo e Abstract (NBR 6028:2021) e Assistente de Escrita Impessoal.
"""

from __future__ import annotations
import re
from typing import Any
from abnt_mcp.config import ABNT_MONTHS
from abnt_mcp.models import CitationInput, ReferenceInput


def capitalize_author_name(name: str) -> str:
    """Capitaliza o sobrenome no padrão NBR 10520:2023 (apenas inicial maiúscula, tratando hífens)."""
    parts = name.strip().split()
    capitalized_parts = []
    for part in parts:
        if "-" in part:
            subparts = [sp.capitalize() for sp in part.split("-")]
            capitalized_parts.append("-".join(subparts))
        else:
            capitalized_parts.append(part.capitalize())
    return " ".join(capitalized_parts)


def format_citation_abnt(data: CitationInput) -> dict[str, Any]:
    """
    Gera a formatação exata da citação segundo a NBR 10520:2023.
    Garante ausência de CAIXA ALTA entre parênteses e pontuação correta.
    """
    authors = [capitalize_author_name(a) for a in data.authors if a.strip()]
    if not authors:
        authors = ["Autor Desconhecido"]

    # 1. Trata a lista de autores
    if len(authors) == 1:
        author_text_parentheses = authors[0]
        author_text_inline = authors[0]
    elif len(authors) == 2:
        author_text_parentheses = f"{authors[0]}; {authors[1]}"
        author_text_inline = f"{authors[0]} e {authors[1]}"
    elif len(authors) == 3:
        author_text_parentheses = f"{authors[0]}; {authors[1]}; {authors[2]}"
        author_text_inline = f"{authors[0]}, {authors[1]} e {authors[2]}"
    else:
        author_text_parentheses = f"{authors[0]} et al."
        author_text_inline = f"{authors[0]} et al."

    # 2. Localizador / Página
    page_str = ""
    if data.page:
        p_clean = data.page.strip()
        if p_clean.isdigit() or "-" in p_clean:
            page_str = f", p. {p_clean}"
        elif p_clean.lower().startswith("p."):
            page_str = f", {p_clean}"
        else:
            page_str = f", {p_clean}"

    call_parentheses = f"({author_text_parentheses}, {data.year}{page_str})"
    call_inline = f"{author_text_inline} ({data.year}{page_str})"

    # 3. Montagem do snippet conforme tipo e formato
    quote_text = (data.quote_text or "").strip()
    target_format = data.target_format.lower()

    if data.quote_type == "direct_short":
        # Citação direta curta (até 3 linhas)
        # Aspas duplas, ponto final APÓS parênteses
        if data.style == "in_parentheses":
            formatted = f'“{quote_text}” {call_parentheses}.'
        else:
            formatted = f'{call_inline}, “{quote_text}”.'

        latex_code = f'``{quote_text}\'\' {call_parentheses}.' if data.style == "in_parentheses" else f'{call_inline}, ``{quote_text}\'\'.'
        typst_code = f'"{quote_text}" {call_parentheses}.' if data.style == "in_parentheses" else f'{call_inline}, "{quote_text}".'

    elif data.quote_type == "direct_long":
        # Citação direta longa (> 3 linhas): recuo 4cm, fonte 10, entrelinhas simples, sem aspas
        if target_format == "latex":
            formatted = (
                f"\\begin{{citacao}}\n"
                f"{quote_text} {call_parentheses}.\n"
                f"\\end{{citacao}}"
            )
        elif target_format == "typst":
            formatted = (
                f"#block(inset: (left: 4cm))[\n"
                f"  #set text(size: 10pt)\n"
                f"  #set par(leading: 0.65em)\n"
                f"  {quote_text} {call_parentheses}.\n"
                f"]"
            )
        else:
            formatted = (
                f'<div style="margin-left: 4.0cm; font-size: 10pt; line-height: 1.0;">\n'
                f'{quote_text} {call_parentheses}.\n'
                f'</div>'
            )

        latex_code = (
            f"\\begin{{citacao}}\n"
            f"{quote_text} {call_parentheses}.\n"
            f"\\end{{citacao}}"
        )
        typst_code = (
            f"#block(inset: (left: 4cm))[\n"
            f"  #set text(size: 10pt)\n"
            f"  #set par(leading: 0.65em)\n"
            f"  {quote_text} {call_parentheses}.\n"
            f"]"
        )

    else:
        # Citação indireta (paráfrase)
        formatted = call_parentheses if data.style == "in_parentheses" else call_inline
        latex_code = formatted
        typst_code = formatted

    return {
        "standard": "NBR 10520:2023",
        "quote_type": data.quote_type,
        "style": data.style,
        "formatted": formatted,
        "variants": {
            "markdown": formatted if target_format == "markdown" else f'“{quote_text}” {call_parentheses}.',
            "latex": latex_code,
            "typst": typst_code,
        },
        "rule_highlights": [
            "Sobrenome em caixa mista/baixa (NBR 10520:2023 revogou a caixa alta nos parênteses).",
            "Ponto final sempre após o fechamento dos parênteses da indicação de autoria.",
            "Citações longas (>3 linhas) têm recuo de 4 cm, fonte 10, entrelinhas simples e dispensam aspas."
        ]
    }


def format_reference_abnt(data: ReferenceInput) -> dict[str, Any]:
    """
    Formata uma referência bibliográfica no rigor da ABNT NBR 6023:2018.
    Alinhamento à esquerda, destaque apenas no título principal (nunca subtítulo).
    """
    # 1. Trata autoria
    author_str = ""
    if data.authors and len(data.authors) > 0:
        formatted_authors: list[str] = []
        for a in data.authors:
            last = a.last_name.strip().upper()
            first = a.first_name.strip().title() if a.first_name else ""
            if first:
                formatted_authors.append(f"{last}, {first}")
            else:
                formatted_authors.append(last)

        if len(formatted_authors) <= 3:
            author_str = "; ".join(formatted_authors) + "."
        else:
            author_str = f"{formatted_authors[0]} et al."
    else:
        # Sem autor: primeira palavra do título em maiúsculas
        first_word = data.title.split()[0].upper()
        author_str = f"{first_word}."

    # 2. Título e subtítulo
    title_main = data.title.strip()
    subtitle_part = f": {data.subtitle.strip()}" if data.subtitle else ""

    # Destaque apenas no título principal
    is_bold = data.emphasis_style == "bold"
    if is_bold:
        title_md = f"**{title_main}**{subtitle_part}"
        title_latex = f"\\textbf{{{title_main}}}{subtitle_part}"
        title_typst = f"*{title_main}*{subtitle_part}"
    else:
        title_md = f"*{title_main}*{subtitle_part}"
        title_latex = f"\\textit{{{title_main}}}{subtitle_part}"
        title_typst = f"_{title_main}_{subtitle_part}"

    # 3. Montagem conforme tipo de entrada
    details_md: list[str] = []
    
    if data.entry_type == "book":
        if data.edition:
            details_md.append(f"{data.edition}.")
        city = data.city or "[S. l.]"
        pub = data.publisher or "[s. n.]"
        details_md.append(f"{city}: {pub}, {data.year}.")
        if data.url:
            details_md.append(f"Disponível em: <{data.url}>.")
            if data.access_date:
                details_md.append(f"Acesso em: {data.access_date}.")

    elif data.entry_type == "journal_article":
        j_name = data.journal_name or "Revista"
        j_styled = f"**{j_name}**" if is_bold else f"*{j_name}*"
        details_md.append(f"{j_styled}")
        city = f", {data.city}" if data.city else ""
        vol = f", v. {data.volume}" if data.volume else ""
        num = f", n. {data.number}" if data.number else ""
        pages = f", p. {data.pages}" if data.pages else ""
        details_md.append(f"{city}{vol}{num}{pages}, {data.year}.")
        if data.url:
            details_md.append(f"Disponível em: <{data.url}>.")
            if data.access_date:
                details_md.append(f"Acesso em: {data.access_date}.")

    elif data.entry_type == "thesis":
        degree = data.degree or "Trabalho de Conclusão de Curso (Graduação)"
        inst = data.institution or "Instituição de Ensino"
        city = data.city or "Local"
        details_md.append(f"{data.year}. {degree} – {inst}, {city}, {data.year}.")
        if data.url:
            details_md.append(f"Disponível em: <{data.url}>.")
            if data.access_date:
                details_md.append(f"Acesso em: {data.access_date}.")

    elif data.entry_type == "website":
        details_md.append(f"{data.year}.")
        if data.url:
            details_md.append(f"Disponível em: <{data.url}>.")
            if data.access_date:
                details_md.append(f"Acesso em: {data.access_date}.")

    else:
        city = f"{data.city}: " if data.city else ""
        pub = f"{data.publisher}, " if data.publisher else ""
        details_md.append(f"{city}{pub}{data.year}.")
        if data.url:
            details_md.append(f"Disponível em: <{data.url}>.")
            if data.access_date:
                details_md.append(f"Acesso em: {data.access_date}.")

    details_str = " ".join(details_md).strip()
    formatted_md = f"{author_str} {title_md}. {details_str}".strip()

    return {
        "standard": "NBR 6023:2018",
        "formatted_reference": formatted_md,
        "author_string": author_str,
        "title_string": f"{title_main}{subtitle_part}",
        "alinhamento": "À esquerda (não justificado)",
        "espacamento": "Simples (1,0) internamente, separado por 1 linha em branco",
    }


def generate_abnt_resumo(
    context: str,
    objective: str,
    methodology: str,
    results: str,
    conclusion: str,
    keywords: list[str],
    language: str = "pt",
) -> dict[str, Any]:
    """
    Gera Resumo ou Abstract estruturado e canônico conforme a NBR 6028:2021.
    - Parágrafo único contínuo.
    - Verbos na 3ª pessoa do singular (voz passiva sintética).
    - 150 a 500 palavras para TCC/Monografia/Dissertação.
    - 3 a 5 palavras-chave separadas por ponto e vírgula e terminadas em ponto.
    """
    is_pt = language.lower() in {"pt", "pt-br", "portugues", "português"}

    # Monta o corpo em parágrafo único
    if is_pt:
        p1 = f"{context.strip().rstrip('.')}."
        p2 = f"Este trabalho tem como objetivo {objective.strip().rstrip('.')}."
        p3 = f"Para tanto, utilizou-se como metodologia {methodology.strip().rstrip('.')}."
        p4 = f"Os resultados obtidos demonstram que {results.strip().rstrip('.')}."
        p5 = f"Conclui-se que {conclusion.strip().rstrip('.')}."
        header = "RESUMO"
        kw_prefix = "Palavras-chave:"
    else:
        p1 = f"{context.strip().rstrip('.')}."
        p2 = f"The objective of this study is to {objective.strip().rstrip('.')}."
        p3 = f"Regarding the methodology, {methodology.strip().rstrip('.')}."
        p4 = f"The results indicate that {results.strip().rstrip('.')}."
        p5 = f"In conclusion, {conclusion.strip().rstrip('.')}."
        header = "ABSTRACT"
        kw_prefix = "Keywords:"

    full_paragraph = f"{p1} {p2} {p3} {p4} {p5}".strip()
    words = full_paragraph.split()
    word_count = len(words)

    # Formata palavras-chave
    clean_kws = [k.strip().rstrip(".;") for k in keywords if k.strip()]
    if len(clean_kws) < 3:
        clean_kws.extend(["Metodologia", "Pesquisa", "Inovação"][: 3 - len(clean_kws)])
    clean_kws = clean_kws[:5]  # máximo 5

    kw_formatted = f"**{kw_prefix}** " + "; ".join(clean_kws) + "."

    # Avaliação de conformidade (150 a 500 palavras)
    status_msg = "Extensão ideal para trabalhos acadêmicos (150 a 500 palavras)."
    is_compliant = True
    if word_count < 150:
        status_msg = f"Atenção: O resumo contém {word_count} palavras. A NBR 6028 recomenda mínimo de 150 palavras para TCCs/teses."
        is_compliant = False
    elif word_count > 500:
        status_msg = f"Atenção: O resumo contém {word_count} palavras. A NBR 6028 recomenda máximo de 500 palavras."
        is_compliant = False

    output_text = (
        f"**{header}**\n\n"
        f"{full_paragraph}\n\n"
        f"{kw_formatted}"
    )

    return {
        "standard": "NBR 6028:2021",
        "language": language,
        "word_count": word_count,
        "is_length_compliant": is_compliant,
        "message": status_msg,
        "formatted_text": output_text,
        "paragraph": full_paragraph,
        "keywords_line": kw_formatted,
    }


def reformulate_to_impersonal(text: str) -> dict[str, Any]:
    """
    Substitui construções de 1ª pessoa por construções impessoais acadêmicas.
    """
    replacements = [
        (r"\b(eu fiz|fizemos)\b", "realizou-se"),
        (r"\b(nós achamos|eu acho|achamos)\b", "constata-se"),
        (r"\b(meu trabalho|nosso trabalho)\b", "o presente estudo"),
        (r"\b(minha pesquisa|nossa pesquisa)\b", "a presente pesquisa"),
        (r"\b(analisei|analisamos)\b", "analisou-se"),
        (r"\b(observei|observamos)\b", "observou-se"),
        (r"\b(concluo|concluímos)\b", "conclui-se"),
        (r"\b(percebi|percebemos)\b", "percebeu-se"),
        (r"\b(verifiquei|verificamos)\b", "verificou-se"),
        (r"\b(utilizei|utilizamos)\b", "utilizou-se"),
        (r"\b(propus|propusemos)\b", "propôs-se"),
        (r"\b(desenvolvi|desenvolvemos)\b", "desenvolveu-se"),
        (r"\ba gente\b", "observa-se"),
        (r"\bpra caramba\b", "significativamente"),
        (r"\bcoisa\b", "elemento"),
        (r"\bcoisas\b", "fatores"),
    ]

    modified = text
    changes_made: list[str] = []
    for pattern, repl in replacements:
        if re.search(pattern, modified, re.IGNORECASE):
            modified = re.sub(pattern, repl, modified, flags=re.IGNORECASE)
            changes_made.append(f"Substituído '{pattern}' por '{repl}'.")

    return {
        "original": text,
        "reformulated": modified,
        "changes_count": len(changes_made),
        "changes": changes_made,
    }


def format_figure_abnt(
    image_path: str,
    caption: str,
    source: str = "Elaborado pelo autor (2026).",
    figure_number: int | str = 1,
    target_format: str = "markdown",
) -> dict[str, Any]:
    """
    Formata uma ilustração/figura conforme a ABNT NBR 14724:
    - Identificação no topo: 'Figura X – Título' (tamanho 10).
    - Ilustração centralizada.
    - Indicação da fonte no rodapé: 'Fonte: ...' (tamanho 10).
    - Chamada obrigatória no texto precedente ('conforme a Figura X').
    """
    label_fig = f"Figura {figure_number} – {caption.strip()}"
    source_fig = f"Fonte: {source.strip()}"
    text_call = f"Conforme ilustra a Figura {figure_number}, ..."

    # Snippet em Markdown
    md_code = (
        f"{label_fig}\n\n"
        f"![{caption}]({image_path})\n\n"
        f"<small>{source_fig}</small>"
    )

    # Snippet em LaTeX (abnTeX2)
    clean_path = image_path.replace("\\", "/")
    latex_code = (
        f"\\begin{{figure}}[htbp]\n"
        f"    \\centering\n"
        f"    \\caption{{{caption.strip()}}}\n"
        f"    \\includegraphics[width=0.8\\textwidth]{{{clean_path}}}\n"
        f"    \\fonte{{{source.strip()}}}\n"
        f"    \\label{{fig:figura{figure_number}}}\n"
        f"\\end{{figure}}"
    )

    # Snippet em Typst
    typst_code = (
        f"#figure(\n"
        f'  image("{clean_path}", width: 80%),\n'
        f"  caption: [{caption.strip()}],\n"
        f")\n"
        f"#align(center)[#text(size: 10pt)[{source_fig}]]"
    )

    return {
        "standard": "ABNT NBR 14724:2011",
        "figure_number": figure_number,
        "caption": caption.strip(),
        "source": source.strip(),
        "text_call_example": text_call,
        "rules": [
            "Identificação no topo com tipo, número de ordem e título.",
            "Indicação da fonte obrigatória no rodapé, mesmo quando elaborada pelo próprio autor.",
            "Tamanho da fonte menor (10 pt) e espaçamento simples para legenda e fonte.",
            "Chamada obrigatória no texto anterior ou concomitante à figura."
        ],
        "snippets": {
            "markdown": md_code,
            "latex": latex_code,
            "typst": typst_code,
        }
    }


def format_table_abnt(
    title: str,
    headers: list[str],
    rows: list[list[str]],
    source: str = "Elaborado pelo autor (2026).",
    table_number: int | str = 1,
    category: str = "tabela",
) -> dict[str, Any]:
    """
    Formata dados no padrão ABNT / Normas Tabulares do IBGE (1993):
    - Tabela (dados numéricos/estatísticos): laterais ABERTAS, sem linhas verticais externas.
    - Quadro (dados qualitativos/textuais): bordas laterais FECHADAS (moldura completa).
    """
    is_table = category.lower() in {"tabela", "table"}
    type_name = "Tabela" if is_table else "Quadro"
    top_label = f"{type_name} {table_number} – {title.strip()}"
    source_label = f"Fonte: {source.strip()}"
    text_call = f"Como indicado na {type_name} {table_number}, ..."

    # 1. Markdown
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    rows_lines = ["| " + " | ".join(r) + " |" for r in rows]
    md_code = f"**{top_label}**\n\n" + "\n".join([header_line, sep_line] + rows_lines) + f"\n\n<small>{source_label}</small>"

    # 2. LaTeX
    col_spec = "c" * len(headers)
    if is_table:
        # Padrão IBGE: booktabs, sem barras verticais nas bordas
        latex_tabular = (
            f"\\begin{{tabular}}{{{col_spec}}}\n"
            f"    \\toprule\n"
            f"    " + " & ".join(headers) + " \\\\\n"
            f"    \\midrule\n"
            + "\n".join(f"    {' & '.join(r)} \\\\" for r in rows) + "\n"
            f"    \\bottomrule\n"
            f"\\end{{tabular}}"
        )
    else:
        # Quadro: bordas fechadas com |
        col_spec_closed = "|" + "|".join(["c"] * len(headers)) + "|"
        latex_tabular = (
            f"\\begin{{tabular}}{{{col_spec_closed}}}\n"
            f"    \\hline\n"
            f"    " + " & ".join(headers) + " \\\\\n"
            f"    \\hline\n"
            + "\n".join(f"    {' & '.join(r)} \\\\ \\hline" for r in rows) + "\n"
            f"\\end{{tabular}}"
        )

    latex_code = (
        f"\\begin{{{category.lower()}}}[htbp]\n"
        f"    \\centering\n"
        f"    \\caption{{{title.strip()}}}\n"
        f"    {latex_tabular}\n"
        f"    \\fonte{{{source.strip()}}}\n"
        f"    \\label{{{category.lower()}:{table_number}}}\n"
        f"\\end{{{category.lower()}}}"
    )

    # 3. Typst
    typst_code = (
        f"#figure(\n"
        f"  table(\n"
        f"    columns: {len(headers)},\n"
        f"    stroke: {'(x, y) => if x == 0 or x == ' + str(len(headers)) + ' { none } else { 0.5pt }' if is_table else '0.5pt'},\n"
        f"    " + ", ".join(f"[{h}]" for h in headers) + ",\n"
        + ",\n".join(f"    {', '.join(f'[{cell}]' for cell in r)}" for r in rows) + "\n"
        f"  ),\n"
        f"  caption: [{title.strip()}],\n"
        f")\n"
        f"#align(center)[#text(size: 10pt)[{source_label}]]"
    )

    return {
        "standard": "Normas do IBGE (1993) / ABNT NBR 14724:2011",
        "category": category,
        "is_table": is_table,
        "distinction_rule": (
            "Tabelas contêm dados numéricos com bordas laterais abertas (IBGE). "
            "Quadros contêm dados textuais/qualitativos com bordas fechadas em moldura."
        ),
        "text_call_example": text_call,
        "snippets": {
            "markdown": md_code,
            "latex": latex_code,
            "typst": typst_code,
        }
    }

