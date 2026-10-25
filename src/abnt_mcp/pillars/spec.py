"""Motor de Escrita Acadêmica Orientada a Especificações (SDD - Spec-Driven Development).

Gerencia a criação, leitura, sincronização Markdown e auditoria cruzada do manifesto
científico `abnt.spec.json` / `SPEC.md` em três camadas:
1. Perfil Normativo (ABNT NBR 14724 vs NBR 6022, referências mínimas, rigor científico)
2. Matriz Científica Rastreável (Problema, Objetivo Geral e Objetivos Específicos OBJ-XX)
3. Estrutura de Capítulos Planejados
"""

from __future__ import annotations
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Literal

from abnt_mcp.config import NORMATIVE_RULES, get_current_year
from abnt_mcp.models import (
    DiagnosticItem,
    ResearchSpec,
    NormativeProfile,
    SpecificObjective,
    PlannedChapter,
    ObjectiveAuditItem,
    ChapterAuditItem,
    SpecAuditResult,
    ProjectScaffoldResult,
)
from abnt_mcp.parsers.pdf_reader import extract_institutional_pattern_from_pdf
from abnt_mcp.pillars.diagnostics import (
    check_project_structure,
    audit_citations_and_references,
    analyze_scientific_tone,
    audit_project_illustrations_and_tables,
)


DEFAULT_PLANNED_CHAPTERS_TCC: list[dict[str, Any]] = [
    {"number": "1", "title": "Introdução", "min_words": 250, "min_citations": 1},
    {"number": "2", "title": "Fundamentação Teórica", "min_words": 500, "min_citations": 3},
    {"number": "3", "title": "Metodologia", "min_words": 300, "min_citations": 1},
    {"number": "4", "title": "Resultados e Discussão", "min_words": 400, "min_citations": 1},
    {"number": "5", "title": "Conclusão", "min_words": 200, "min_citations": 0},
]

DEFAULT_PLANNED_CHAPTERS_ARTIGO: list[dict[str, Any]] = [
    {"number": "1", "title": "Introdução", "min_words": 150, "min_citations": 1},
    {"number": "2", "title": "Metodologia", "min_words": 150, "min_citations": 1},
    {"number": "3", "title": "Resultados e Discussão", "min_words": 250, "min_citations": 1},
    {"number": "4", "title": "Considerações Finais", "min_words": 100, "min_citations": 0},
]


def render_spec_markdown(spec: ResearchSpec) -> str:
    """Renderiza uma visualização Markdown legível (`SPEC.md`) a partir de `ResearchSpec`."""
    lines = [
        f"# Especificação Científica (SDD): {spec.title}",
        "",
        f"- **Versão da Spec:** `{spec.spec_version}`",
        f"- **Autor(a):** {spec.author or 'Não informado'}",
        f"- **Tipo Documental:** `{spec.profile.document_type.upper()}`",
        f"- **Norma Estrutural:** `{spec.profile.standard}`",
        f"- **Instituição / Periódico:** {spec.profile.institution or 'Padrão Geral ABNT'}",
        f"- **Curso / Programa:** {spec.profile.course or 'Não informado'}",
        f"- **Orientador(a):** {spec.profile.advisor or 'Não informado'}",
        f"- **Logotipo na Capa:** {spec.profile.cover_logo_path if spec.profile.has_cover_logo else 'Não configurado'}",
        f"- **Rótulo de Conclusão:** `{spec.profile.conclusion_label}`",
        f"- **Meta Mínima de Referências (`.bib`):** {spec.profile.min_references}",
        f"- **Meta de Rigor Científico:** {spec.profile.min_scientific_tone_score}/100",
        "",
        "---",
        "",
        "## 1. Matriz Científica",
        "",
        "### 1.1 Problema de Pesquisa",
        f"> {spec.research_problem}",
        "",
        "### 1.2 Objetivo Geral",
        f"{spec.general_objective}",
        "",
        "### 1.3 Síntese Metodológica",
        f"{spec.methodology_summary}",
        "",
        "### 1.4 Objetivos Específicos Rastreáveis",
        "",
        "| ID | Objetivo Específico | Palavras-Chave de Validação | Seção Alvo |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for obj in spec.specific_objectives:
        kw_str = ", ".join(f"`{k}`" for k in obj.keywords) if obj.keywords else "*Auto-extraídas*"
        sec_str = obj.target_section or "Desenvolvimento"
        lines.append(f"| `{obj.id}` | {obj.description} | {kw_str} | {sec_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Arquitetura de Capítulos Planejados",
        "",
        "| Seção | Título Planejado | Mín. Palavras | Mín. Citações |",
        "| :--- | :--- | :---: | :---: |",
    ])

    for ch in spec.planned_chapters:
        lines.append(f"| `{ch.number}` | {ch.title} | {ch.min_words} | {ch.min_citations} |")

    lines.append("")
    return "\n".join(lines)


def init_project_spec(
    project_path: str | Path,
    title: str,
    research_problem: str,
    general_objective: str,
    specific_objectives: list[dict[str, Any]],
    methodology_summary: str,
    document_type: Literal["tcc", "dissertacao", "tese", "artigo"] = "tcc",
    author: str | None = None,
    institution: str | None = None,
    course: str | None = None,
    advisor: str | None = None,
    city: str | None = None,
    min_references: int | None = None,
    planned_chapters: list[dict[str, Any]] | None = None,
    sample_pdf_path: str | Path | None = None,
    logo_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Inicializa e persiste o manifesto `abnt.spec.json` e o documento `SPEC.md`
    no diretório do projeto acadêmico, com suporte opcional a aprendizado de
    padrão institucional via PDF de exemplo (`sample_pdf_path`) e cópia de logotipo (`logo_path`).
    """
    path = Path(project_path)
    target_dir = path if (path.exists() and path.is_dir()) else (path.parent if path.suffix else path)
    target_dir.mkdir(parents=True, exist_ok=True)
    figuras_dir = target_dir / "figuras"

    inferred_profile: dict[str, Any] | None = None
    if sample_pdf_path:
        inferred_profile = extract_institutional_pattern_from_pdf(
            pdf_path=sample_pdf_path,
            output_assets_dir=figuras_dir,
        )

    effective_logo_path = inferred_profile.get("cover_logo_path") if inferred_profile else None
    has_cover_logo = bool(inferred_profile.get("has_cover_logo")) if inferred_profile else False

    if logo_path:
        src_logo = Path(logo_path)
        if not src_logo.is_file():
            raise FileNotFoundError(f"Arquivo de logotipo não encontrado: {src_logo}")
        figuras_dir.mkdir(parents=True, exist_ok=True)
        ext = src_logo.suffix.lower() or ".png"
        dest_logo = figuras_dir / f"logo_instituicao{ext}"
        if src_logo.resolve() != dest_logo.resolve():
            shutil.copy2(src_logo, dest_logo)
        has_cover_logo = True
        effective_logo_path = f"figuras/{dest_logo.name}"

    standard: Literal["ABNT_14724", "ABNT_6022"] = (
        "ABNT_6022" if document_type == "artigo" else "ABNT_14724"
    )
    effective_min_refs = (
        min_references
        if min_references is not None
        else (5 if document_type == "artigo" else 15)
    )

    parsed_objectives: list[SpecificObjective] = []
    for idx, raw_obj in enumerate(specific_objectives, start=1):
        obj_id = raw_obj.get("id") or f"OBJ-{idx:02d}"
        desc = raw_obj.get("description", "").strip()
        kws = raw_obj.get("keywords") or _extract_candidate_keywords(desc)
        parsed_objectives.append(
            SpecificObjective(
                id=obj_id,
                description=desc,
                keywords=kws,
                target_section=raw_obj.get("target_section"),
            )
        )

    effective_conclusion_label = (
        inferred_profile.get("conclusion_label", "Conclusão")
        if inferred_profile
        else ("Considerações Finais" if document_type == "artigo" else "Conclusão")
    )

    if planned_chapters is not None:
        raw_chapters = planned_chapters
    elif document_type == "artigo":
        raw_chapters = [dict(c) for c in DEFAULT_PLANNED_CHAPTERS_ARTIGO]
    else:
        raw_chapters = [dict(c) for c in DEFAULT_PLANNED_CHAPTERS_TCC]
        if raw_chapters and raw_chapters[-1]["number"] == "5":
            raw_chapters[-1]["title"] = effective_conclusion_label

    parsed_chapters = [PlannedChapter(**ch) for ch in raw_chapters]

    effective_institution = institution or (inferred_profile.get("institution") if inferred_profile else None)
    effective_course = course or (inferred_profile.get("course") if inferred_profile else None)
    effective_department = inferred_profile.get("department") if inferred_profile else None
    effective_advisor = advisor or (inferred_profile.get("advisor") if inferred_profile else None)
    effective_city = city or (inferred_profile.get("city") if inferred_profile else None)
    cover_header_lines = (
        list(inferred_profile.get("cover_header_lines", []))
        if inferred_profile
        else ([effective_institution] if effective_institution else [])
    )
    preamble_text = inferred_profile.get("preamble_text") if inferred_profile else None
    required_pre_textual = (
        list(inferred_profile.get("required_pre_textual", []))
        if inferred_profile
        else []
    )

    profile = NormativeProfile(
        document_type=document_type,
        standard=standard,
        institution=effective_institution,
        course=effective_course,
        department=effective_department,
        advisor=effective_advisor,
        city=effective_city,
        cover_header_lines=cover_header_lines,
        has_cover_logo=has_cover_logo,
        cover_logo_path=effective_logo_path,
        preamble_text=preamble_text,
        required_pre_textual=required_pre_textual,
        conclusion_label=effective_conclusion_label,
        inferred_from_pdf=bool(inferred_profile),
        min_references=effective_min_refs,
    )

    spec = ResearchSpec(
        title=title,
        author=author,
        research_problem=research_problem,
        general_objective=general_objective,
        methodology_summary=methodology_summary,
        specific_objectives=parsed_objectives,
        profile=profile,
        planned_chapters=parsed_chapters,
    )

    spec_json_path = target_dir / "abnt.spec.json"
    spec_md_path = target_dir / "SPEC.md"

    spec_json_path.write_text(
        json.dumps(spec.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    spec_md_path.write_text(render_spec_markdown(spec), encoding="utf-8")

    return {
        "success": True,
        "spec_json_path": str(spec_json_path),
        "spec_md_path": str(spec_md_path),
        "spec": spec.model_dump(),
        "inferred_institutional_profile": inferred_profile,
        "message": (
            f"Especificação SDD inicializada com sucesso ({len(parsed_objectives)} objetivos "
            f"específicos e {len(parsed_chapters)} capítulos planejados sob {standard})."
        ),
    }


def _render_dynamic_pre_textual(
    format: Literal["typst", "latex", "markdown"],
    spec: ResearchSpec,
) -> tuple[str, str]:
    """
    Renderiza dinamicamente os blocos de elementos pré-textuais exigidos pela instituição
    (`spec.profile.required_pre_textual`) na ordem estrita da ABNT NBR 14724:2011:
    - Bloco pré-Resumo (após Folha de Rosto): Ficha Catalográfica, Folha de Aprovação, Dedicatória, Agradecimentos, Epígrafe.
    - Bloco pós-Abstract (antes do Sumário): Lista de Ilustrações, Lista de Tabelas, Lista de Quadros, Lista de Abreviaturas e Siglas.
    Garante estrita aderência à NBR14724-R02 (nenhum elemento pré-textual exibe número de página impresso).
    """
    req_normalized = {
        unicodedata.normalize("NFKD", item.lower().strip()).encode("ascii", "ignore").decode("ascii")
        for item in spec.profile.required_pre_textual
    }
    if not req_normalized:
        return "", ""

    year = get_current_year()
    author = spec.author or "Autor do Trabalho"
    title = spec.title
    inst = spec.profile.institution or "Instituição de Ensino Superior"
    advisor = spec.profile.advisor or "Prof. Dr. Nome do Orientador"
    preamble = spec.profile.preamble_text or (
        f"Trabalho de Conclusão de Curso apresentado à {inst} como requisito parcial para obtenção do título acadêmico."
    )

    pre_resumo_chunks: list[str] = []
    post_abstract_chunks: list[str] = []

    if format == "typst":
        if "ficha catalografica" in req_normalized:
            pre_resumo_chunks.append(f"""// --- FICHA CATALOGRÁFICA (NBR 14724) ---
#v(1fr)
#align(center)[
  *Dados Internacionais de Catalogação na Publicação (CIP)* \\
  *Ficha Catalográfica elaborada pela Biblioteca de {inst}*
  #v(0.5cm)
  #rect(width: 12.5cm, inset: 12pt, stroke: 0.5pt)[
    #align(left)[
      #text(size: 10pt)[
        {author} \\
        #h(1cm) {title} / {author}. -- Brasil, {year}. \\
        #h(1cm) Orientador(a): {advisor}. \\
        #h(1cm) 1. Pesquisa acadêmica. 2. Normas ABNT. I. Título.
      ]
    ]
  ]
]
#pagebreak()
""")

        if "folha de aprovacao" in req_normalized:
            pre_resumo_chunks.append(f"""// --- FOLHA DE APROVAÇÃO (NBR 14724) ---
#align(center)[
  *{author.upper()}*

  #v(2cm)
  #text(size: 14pt, weight: "bold")[{title.upper()}]
]
#v(1.5cm)
#align(right)[
  #block(width: 8.5cm)[
    #set par(justify: true, leading: 0.49em, first-line-indent: 0cm)
    #text(size: 10pt)[
      {preamble}
    ]
  ]
]
#v(1cm)
Aprovado em: _____ de _________________ de {year}.

#v(1.5cm)
#align(center)[
  *BANCA EXAMINADORA*
  #v(1cm)
  #line(length: 10cm, stroke: 0.5pt) \\
  {advisor} (Orientador)

  #v(1cm)
  #line(length: 10cm, stroke: 0.5pt) \\
  Prof. Dr. Examinador 1 (Membro da Banca Examinadora)

  #v(1cm)
  #line(length: 10cm, stroke: 0.5pt) \\
  Prof. Dr. Examinador 2 (Membro da Banca Examinadora)
]
#pagebreak()
""")

        if "dedicatoria" in req_normalized:
            pre_resumo_chunks.append("""// --- DEDICATÓRIA (NBR 14724) ---
#v(1fr)
#align(right)[
  #block(width: 8cm)[
    #set par(first-line-indent: 0cm)
    _Dedico este trabalho a todos que contribuíram para a realização desta pesquisa científica._
  ]
]
#pagebreak()
""")

        if "agradecimentos" in req_normalized:
            pre_resumo_chunks.append(f"""// --- AGRADECIMENTOS (NBR 14724) ---
#align(center)[*AGRADECIMENTOS*]
#v(1cm)
Registro meus sinceros agradecimentos à {inst}, ao(à) orientador(a) {advisor} e a todos que colaboraram direta ou indiretamente para o desenvolvimento deste estudo.
#pagebreak()
""")

        if "epigrafe" in req_normalized:
            pre_resumo_chunks.append("""// --- EPÍGRAFE (NBR 14724) ---
#v(1fr)
#align(right)[
  #block(width: 8cm)[
    #set par(first-line-indent: 0cm)
    _"A ciência consiste em substituir o saber que parecia seguro por uma teoria, ou seja, por algo problemático."_ \\
    (Karl Popper)
  ]
]
#pagebreak()
""")

        # Elementos pós-abstract: Listas de ilustrações, tabelas e quadros no Typst
        # são geradas por blocos reativos (#context query) em _render_scaffolded_typst
        # para que só se materializem no PDF quando de fato existirem itens no manuscrito.
        if "lista de abreviaturas" in req_normalized:
            post_abstract_chunks.append("""// --- LISTA DE ABREVIATURAS E SIGLAS (NBR 14724) ---
#align(center)[*LISTA DE ABREVIATURAS E SIGLAS*]
#v(1cm)
#align(left)[
  #set par(first-line-indent: 0cm, leading: 1.061em)
  *ABNT* -- Associação Brasileira de Normas Técnicas \\
  *IBGE* -- Instituto Brasileiro de Geografia e Estatística \\
  *MCP* -- Model Context Protocol \\
  *SDD* -- Spec-Driven Development
]
#pagebreak()
""")

    elif format == "latex":
        if "ficha catalografica" in req_normalized:
            pre_resumo_chunks.append(f"""\\begin{{fichacatalografica}}
\\vspace*{{\\fill}}
\\begin{{center}}
\\textbf{{Ficha Catalográfica elaborada pela Biblioteca de {inst}}} \\\\
\\fbox{{\\parbox{{12.5cm}}{{\\small {author}. \\textit{{{title}}}. Brasil, {year}. Orientador(a): {advisor}.}}}}
\\end{{center}}
\\end{{fichacatalografica}}
""")

        if "folha de aprovacao" in req_normalized:
            pre_resumo_chunks.append(f"""\\begin{{folhadeaprovacao}}
\\begin{{center}}
{{\\ABNTEXchapterfont\\large\\MakeUppercase{{{author}}}}}
\\vspace*{{\\fill}}\\\\{{\\ABNTEXchapterfont\\bfseries\\Large\\MakeUppercase{{{title}}}}}\\\\
\\vspace*{{\\fill}}
\\hspace{{.45\\textwidth}}
\\begin{{minipage}}{{.5\\textwidth}}
\\SingleSpacing
{preamble}
\\end{{minipage}}
\\vspace*{{\\fill}}
\\end{{center}}
Trabalho aprovado em: \\_\\_\\_ de \\_\\_\\_\\_\\_\\_\\_\\_\\_\\_ de {year}.
\\assinatura{{\\textbf{{{advisor}}} \\\\ Orientador(a)}}
\\assinatura{{\\textbf{{Prof. Dr. Examinador 1}} \\\\ Banca Examinadora}}
\\assinatura{{\\textbf{{Prof. Dr. Examinador 2}} \\\\ Banca Examinadora}}
\\end{{folhadeaprovacao}}
""")

        if "dedicatoria" in req_normalized:
            pre_resumo_chunks.append("""\\begin{dedicatoria}
\\vspace*{\\fill}
\\centering
\\noindent
\\textit{Dedico este trabalho a todos que contribuíram para a realização desta pesquisa.}
\\vspace*{\\fill}
\\end{dedicatoria}
""")

        if "agradecimentos" in req_normalized:
            pre_resumo_chunks.append(f"""\\begin{{agradecimentos}}
Agradeço à {inst}, ao(à) orientador(a) {advisor} e aos demais colaboradores desta pesquisa.
\\end{{agradecimentos}}
""")

        if "epigrafe" in req_normalized:
            pre_resumo_chunks.append("""\\begin{epigrafe}
\\vspace*{\\fill}
\\begin{flushright}
\\textit{``A ciência consiste em substituir o saber que parecia seguro por uma teoria.'' \\\\ (Karl Popper)}
\\end{flushright}
\\end{epigrafe}
""")

        if "lista de ilustracoes" in req_normalized:
            post_abstract_chunks.append("""% --- LISTA DE ILUSTRAÇÕES ---
\\pdfbookmark[0]{\\listfigurename}{lof}
\\listoffigures*
\\cleardoublepage
""")

        if "lista de tabelas" in req_normalized:
            post_abstract_chunks.append("""% --- LISTA DE TABELAS ---
\\pdfbookmark[0]{\\listtablename}{lot}
\\listoftables*
\\cleardoublepage
""")

        if "lista de quadros" in req_normalized:
            post_abstract_chunks.append("""% --- LISTA DE QUADROS ---
\\pdfbookmark[0]{\\listofquadrosname}{loq}
\\listofquadros*
\\cleardoublepage
""")

        if "lista de abreviaturas" in req_normalized:
            post_abstract_chunks.append("""% --- LISTA DE ABREVIATURAS E SIGLAS ---
\\begin{siglas}
  \\item[ABNT] Associação Brasileira de Normas Técnicas
  \\item[IBGE] Instituto Brasileiro de Geografia e Estatística
  \\item[MCP] Model Context Protocol
  \\item[SDD] Spec-Driven Development
\\end{siglas}
""")

    else:  # markdown
        if "ficha catalografica" in req_normalized:
            pre_resumo_chunks.append(f"""# Ficha Catalográfica {{.unnumbered}}

Dados Internacionais de Catalogação na Publicação (CIP) — {inst}.
{author}. *{title}*. {year}. Orientador(a): {advisor}.
""")

        if "folha de aprovacao" in req_normalized:
            pre_resumo_chunks.append(f"""# Folha de Aprovação {{.unnumbered}}

{preamble}

Aprovado em: ___/___/{year}.

- **{advisor}** — Orientador(a) (Banca Examinadora)
- **Prof. Dr. Examinador 1** — Membro da Banca Examinadora
- **Prof. Dr. Examinador 2** — Membro da Banca Examinadora
""")

        if "dedicatoria" in req_normalized:
            pre_resumo_chunks.append("""# Dedicatória {.unnumbered}

*Dedico este trabalho a todos que contribuíram para a realização desta pesquisa.*
""")

        if "agradecimentos" in req_normalized:
            pre_resumo_chunks.append(f"""# Agradecimentos {{.unnumbered}}

Agradeço à {inst}, ao(à) orientador(a) {advisor} e aos demais colaboradores deste estudo.
""")

        if "epigrafe" in req_normalized:
            pre_resumo_chunks.append("""# Epígrafe {.unnumbered}

> *"A ciência consiste em substituir o saber que parecia seguro por uma teoria."* (Karl Popper)
""")

        if "lista de ilustracoes" in req_normalized:
            post_abstract_chunks.append("""# Lista de Ilustrações {.unnumbered}

- Figura 1 – Arquitetura do Estudo
""")

        if "lista de tabelas" in req_normalized:
            post_abstract_chunks.append("""# Lista de Tabelas {.unnumbered}

- Tabela 1 – Indicadores Quantitativos
""")

        if "lista de quadros" in req_normalized:
            post_abstract_chunks.append("""# Lista de Quadros {.unnumbered}

- Quadro 1 – Síntese Conceitual
""")

        if "lista de abreviaturas" in req_normalized:
            post_abstract_chunks.append("""# Lista de Abreviaturas e Siglas {.unnumbered}

- **ABNT**: Associação Brasileira de Normas Técnicas
- **IBGE**: Instituto Brasileiro de Geografia e Estatística
- **MCP**: Model Context Protocol
- **SDD**: Spec-Driven Development
""")

    pre_str = ("\n" + "\n".join(pre_resumo_chunks)) if pre_resumo_chunks else ""
    post_str = ("\n" + "\n".join(post_abstract_chunks)) if post_abstract_chunks else ""
    return pre_str, post_str


def _render_scaffolded_typst(spec: ResearchSpec) -> str:
    """Gera um manuscrito Typst completo e compilável customizado com o perfil institucional e SDD."""
    year = get_current_year()
    header_lines = spec.profile.cover_header_lines or [
        spec.profile.institution or "UNIVERSIDADE FEDERAL",
        spec.profile.course or "CURSO DE GRADUAÇÃO",
    ]
    header_typst = "\n  \n  ".join(f"*{ln.upper()}*" for ln in header_lines)
    logo_block = ""
    if spec.profile.has_cover_logo and spec.profile.cover_logo_path:
        logo_block = f'  #image("{spec.profile.cover_logo_path}", width: 3cm)\n  #v(0.5cm)\n'

    preamble = spec.profile.preamble_text or (
        f"Trabalho de Conclusão de Curso apresentado à {spec.profile.institution or 'Instituição'} "
        "como requisito parcial para obtenção do título acadêmico."
    )
    advisor_line = f"Orientador(a): {spec.profile.advisor}" if spec.profile.advisor else "Orientador(a): Prof. Dr. Nome do Orientador"
    concl_title = spec.profile.conclusion_label.upper()
    city_line = (spec.profile.city or "CIDADE - UF").upper()
    pre_resumo_block, post_abstract_block = _render_dynamic_pre_textual("typst", spec)

    return f"""// =========================================================================
// PROJETO ACADÊMICO ABNT (NBR 14724 / NBR 10520:2023 / NBR 6023:2018)
// Gerado via scaffold_academic_project (SDD)
// =========================================================================

#set document(title: "{spec.title}", author: "{spec.author or 'Autor'}")
#set text(font: ("Times New Roman", "Liberation Serif", "Linux Libertine"), size: 12pt, lang: "pt", region: "BR")

#set page(
  paper: "a4",
  margin: (top: 3cm, left: 3cm, right: 2cm, bottom: 2cm),
  numbering: none
)

#set par(
  justify: true,
  leading: 1.061em,
  first-line-indent: (amount: 1.25cm, all: true)
)
#set heading(numbering: "1.1")
#set math.equation(numbering: "(1)")
#show figure: set figure.caption(position: top)
#show figure.caption: set text(size: 10pt)

// --- REGRAS DE DIAGRAMAÇÃO ABNT (NBR 14724 itens 5.2.1 e 5.2.2) ---
// Cada capítulo primário inicia obrigatoriamente em folha distinta com respiro de 1,5 linha (0.8cm)
#show heading.where(level: 1): it => {{
  pagebreak(weak: true)
  v(1.0cm)
  it
  v(0.8cm)
}}

#show heading.where(level: 2): it => {{
  v(0.8cm)
  it
  v(0.6cm)
}}

// --- CAPA (Não contada na paginação - NBR 14724 item 5.3) ---
#align(center)[
{logo_block}  {header_typst}

  #v(3cm)
  *{(spec.author or 'AUTOR DO TRABALHO').upper()}*

  #v(4cm)
  #text(size: 14pt, weight: "bold")[{spec.title.upper()}]

  #v(1fr)
  *{city_line}* \\
  *{year}*
]
#pagebreak()

// --- FOLHA DE ROSTO (Inicia a contagem na página 1, sem exibir número) ---
#counter(page).update(1)

#align(center)[
  *{(spec.author or 'AUTOR DO TRABALHO').upper()}*

  #v(4cm)
  #text(size: 14pt, weight: "bold")[{spec.title.upper()}]

  #v(3cm)
  #align(right)[
    #block(width: 8cm)[
      #set par(leading: 0.49em, first-line-indent: 0cm)
      #text(size: 10pt)[
        {preamble}
        
        {advisor_line}
      ]
    ]
  ]

  #v(1fr)
  *{city_line}* \\
  *{year}*
]
#pagebreak()
{pre_resumo_block}
// --- RESUMO (NBR 6028:2021) ---
#align(center)[*RESUMO*]
#v(1cm)
#par(first-line-indent: 0cm, leading: 0.49em)[
  {spec.general_objective} A metodologia adotada consiste em: {spec.methodology_summary} Conclui-se que a estrutura orientada a especificações assegura rastreabilidade normativa e metodológica.
  
  #v(0.5cm)
  *Palavras-chave:* ABNT; pesquisa científica; metodologia; especificação.
]
#pagebreak()

// --- ABSTRACT ---
#align(center)[*ABSTRACT*]
#v(1cm)
#par(first-line-indent: 0cm, leading: 0.49em)[
  This academic work investigates the proposed research problem through a spec-driven methodology. Results demonstrate compliance with technical standards.
  
  #v(0.5cm)
  *Keywords:* ABNT; scientific research; methodology; specification.
]
#pagebreak()
{post_abstract_block}
// --- LISTAS PRÉ-TEXTUAIS REATIVAS (NBR 14724) ---
// Materializam-se automaticamente apenas se houver figuras, tabelas ou quadros no documento.
#context {{
  let figs = query(figure.where(kind: image))
  if figs.len() > 0 {{
    align(center)[*LISTA DE ILUSTRAÇÕES*]
    v(1cm)
    outline(title: none, target: figure.where(kind: image))
    pagebreak()
  }}
}}

#context {{
  let tabs = query(figure.where(kind: table))
  if tabs.len() > 0 {{
    align(center)[*LISTA DE TABELAS*]
    v(1cm)
    outline(title: none, target: figure.where(kind: table))
    pagebreak()
  }}
}}

#context {{
  let quadros = query(figure.where(kind: "quadro"))
  if quadros.len() > 0 {{
    align(center)[*LISTA DE QUADROS*]
    v(1cm)
    outline(title: none, target: figure.where(kind: "quadro"))
    pagebreak()
  }}
}}

// --- SUMÁRIO (NBR 6027:2012) ---
#align(center)[*SUMÁRIO*]
#v(1cm)
#outline(title: none, indent: auto)
#pagebreak()

// =========================================================================
// ELEMENTOS TEXTUAIS (Exibe numeração arábica no canto superior direito)
// =========================================================================
#set page(
  header: align(right, context counter(page).display("1"))
)

= INTRODUÇÃO
{spec.research_problem} O objetivo geral deste estudo consiste em: {spec.general_objective} Segundo @silva2023, a padronização normativa eleva a qualidade da comunicação científica.

= FUNDAMENTAÇÃO TEÓRICA
Desenvolvimento do referencial teórico vinculado aos objetivos específicos ({', '.join(o.id for o in spec.specific_objectives)}) conforme @silva2023.

= METODOLOGIA
{spec.methodology_summary}

= RESULTADOS E DISCUSSÃO
Apresentação e discussão analítica dos resultados alcançados em relação aos termos-chave ({', '.join(k for o in spec.specific_objectives for k in o.keywords[:2])}).

= {concl_title}
Retomada dos objetivos específicos ({', '.join(k for o in spec.specific_objectives for k in o.keywords[:2])}) demonstrando o atendimento integral da especificação científica.

// =========================================================================
// ELEMENTOS PÓS-TEXTUAIS (NBR 6023:2018)
// =========================================================================
#pagebreak()
#bibliography("referencias.bib", title: "REFERÊNCIAS", style: "associacao-brasileira-de-normas-tecnicas")
"""


def _render_scaffolded_latex(spec: ResearchSpec) -> str:
    """Gera um manuscrito LaTeX (abnTeX2) customizado com o perfil institucional e SDD."""
    year = get_current_year()
    inst = spec.profile.institution or "UNIVERSIDADE FEDERAL"
    advisor = spec.profile.advisor or "Prof. Dr. Nome do Orientador"
    preamble = spec.profile.preamble_text or (
        f"Trabalho de Conclusão de Curso apresentado à {inst} como requisito parcial para obtenção do grau acadêmico."
    )
    logo_cmd = ""
    if spec.profile.has_cover_logo and spec.profile.cover_logo_path:
        logo_cmd = f"% Logotipo Institucional na Capa\n% \\includegraphics[width=3cm]{{{spec.profile.cover_logo_path}}}\n"

    concl_title = spec.profile.conclusion_label
    pre_resumo_block, post_abstract_block = _render_dynamic_pre_textual("latex", spec)

    return f"""\\documentclass[12pt,openright,oneside,a4paper,english,brazil]{{abntex2}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage[brazilian,hyperpageref]{{backref}}
\\usepackage[alf]{{abntex2cite}}

{logo_cmd}\\titulo{{{spec.title}}}
\\autor{{{spec.author or 'Autor do Trabalho'}}}
\\local{{{spec.profile.city or 'Cidade - UF'}}}
\\data{{{year}}}
\\orientador{{{advisor}}}
\\instituicao{{{inst}}}
\\tipotrabalho{{Trabalho de Conclusão de Curso}}
\\preambulo{{{preamble}}}

\\begin{{document}}
\\imprimircapa
\\imprimirfolhaderosto*
{pre_resumo_block}
\\begin{{resumo}}
{spec.general_objective} Metodologia: {spec.methodology_summary}

\\vspace{{\\onelineskip}}
\\noindent
\\textbf{{Palavras-chave}}: ABNT; pesquisa científica; especificação.
\\end{{resumo}}

\\begin{{resumo}}[Abstract]
\\begin{{otherlanguage*}}{{english}}
This study addresses the research problem using a spec-driven academic methodology.

\\vspace{{\\onelineskip}}
\\noindent
\\textbf{{Keywords}}: ABNT; scientific research; specification.
\\end{{otherlanguage*}}
\\end{{resumo}}
{post_abstract_block}
\\pdfbookmark[0]{{\\contentsname}}{{toc}}
\\tableofcontents*
\\cleardoublepage

\\textual
\\pagestyle{{simple}}

\\chapter{{Introdução}}
{spec.research_problem} Objetivo geral: {spec.general_objective} Conforme \\cite{{silva2023}}, o rigor normativo fortalece a produção científica.

\\chapter{{Fundamentação Teórica}}
Discussão teórica dos objetivos ({', '.join(o.id for o in spec.specific_objectives)}) segundo \\citeonline{{silva2023}}.

\\chapter{{Metodologia}}
{spec.methodology_summary}

\\chapter{{Resultados e Discussão}}
Análise empírica contemplando os conceitos ({', '.join(k for o in spec.specific_objectives for k in o.keywords[:2])}).

\\chapter{{{concl_title}}}
Síntese conclusiva respondendo aos objetivos específicos ({', '.join(k for o in spec.specific_objectives for k in o.keywords[:2])}).

\\postextual
\\bibliography{{referencias}}
\\end{{document}}
"""


def _render_scaffolded_markdown(spec: ResearchSpec) -> str:
    """Gera um manuscrito Markdown (Pandoc) customizado com o perfil institucional e SDD."""
    year = get_current_year()
    inst = spec.profile.institution or "UNIVERSIDADE FEDERAL"
    advisor = spec.profile.advisor or "Prof. Dr. Nome do Orientador"
    preamble = spec.profile.preamble_text or (
        f"Trabalho de Conclusão de Curso apresentado à {inst} como requisito parcial para obtenção do título acadêmico."
    )
    logo_md = ""
    if spec.profile.has_cover_logo and spec.profile.cover_logo_path:
        logo_md = f"![Logotipo Institucional]({spec.profile.cover_logo_path})\n\n"
    concl_title = spec.profile.conclusion_label
    pre_resumo_block, post_abstract_block = _render_dynamic_pre_textual("markdown", spec)

    return f"""---
title: "{spec.title}"
author: "{spec.author or 'Autor do Trabalho'}"
date: "{year}"
institution: "{inst}"
advisor: "{advisor}"
lang: pt-BR
bibliography: referencias.bib
---

<!-- CAPA -->
{logo_md}**{inst}**

**{spec.author or 'Autor do Trabalho'}**

# {spec.title}

**{(spec.profile.city or 'CIDADE - UF').upper()}**  
**{year}**

<!-- FOLHA DE ROSTO -->
{preamble}
Orientador(a): {advisor}
{pre_resumo_block}
# Resumo {{.unnumbered}}

{spec.general_objective} Metodologia: {spec.methodology_summary}

**Palavras-chave:** ABNT; pesquisa científica; especificação.

# Abstract {{.unnumbered}}

This academic work addresses the proposed research problem with a spec-driven methodology.

**Keywords:** ABNT; scientific research; specification.
{post_abstract_block}
# Sumário {{.unnumbered}}

1. Introdução
2. Fundamentação Teórica
3. Metodologia
4. Resultados e Discussão
5. {concl_title}

# 1 Introdução

{spec.research_problem} Objetivo geral: {spec.general_objective} Segundo [@silva2023], a padronização assegura rastreabilidade científica.

# 2 Fundamentação Teórica

Desenvolvimento conceitual dos objetivos ({', '.join(o.id for o in spec.specific_objectives)}) com base na literatura [@silva2023].

# 3 Metodologia

{spec.methodology_summary}

# 4 Resultados e Discussão

Análise dos resultados obtidos frente aos conceitos-chave ({', '.join(k for o in spec.specific_objectives for k in o.keywords[:2])}).

# 5 {concl_title}

Síntese final respondendo aos objetivos específicos ({', '.join(k for o in spec.specific_objectives for k in o.keywords[:2])}).

# Referências {{.unnumbered}}
"""


def scaffold_project(
    project_path: str | Path,
    title: str,
    author: str,
    document_type: Literal["tcc", "dissertacao", "tese", "artigo"] = "tcc",
    format: Literal["typst", "latex", "markdown"] = "typst",
    institution: str | None = None,
    course: str | None = None,
    advisor: str | None = None,
    city: str | None = None,
    research_problem: str | None = None,
    general_objective: str | None = None,
    specific_objectives: list[dict[str, Any]] | None = None,
    methodology_summary: str | None = None,
    sample_pdf_path: str | Path | None = None,
    logo_path: str | Path | None = None,
    overwrite: bool = False,
) -> ProjectScaffoldResult:
    """
    Cria a estrutura completa de diretórios e arquivos de um projeto acadêmico SDD:
    - Diretórios: `capitulos/`, `figuras/`, `tabelas/`, `anexos/`, `apendices/`, `.abnt-mcp/`.
    - Extrai automaticamente o padrão institucional e o brasão/logotipo da capa caso `sample_pdf_path` seja fornecido.
    - Copia o logotipo para `figuras/logo_instituicao.*` caso `logo_path` seja fornecido.
    - Inicializa `abnt.spec.json` e `SPEC.md`.
    - Cria `referencias.bib` e o arquivo principal (`main.typ`, `main.tex` ou `main.md`) pronto para compilação.
    """
    target_dir = Path(project_path)
    ext_map = {"typst": ".typ", "latex": ".tex", "markdown": ".md"}
    ext = ext_map[format]
    main_file = target_dir / f"main{ext}"
    spec_json_file = target_dir / "abnt.spec.json"

    if not overwrite and (main_file.exists() or spec_json_file.exists()):
        raise FileExistsError(
            f"O diretório '{target_dir}' já contém um projeto acadêmico inicializado "
            f"('{main_file.name}' ou 'abnt.spec.json'). Use overwrite=True para sobrescrever."
        )

    subdirs = ["capitulos", "figuras", "tabelas", "anexos", "apendices", ".abnt-mcp"]
    for sd in subdirs:
        (target_dir / sd).mkdir(parents=True, exist_ok=True)

    eff_problem = research_problem or f"Qual a contribuição acadêmica e empírica do estudo sobre {title}?"
    eff_general = general_objective or f"Analisar e desenvolver uma investigação sistemática sobre {title}."
    eff_methodology = methodology_summary or (
        "Pesquisa exploratória e descritiva com revisão bibliográfica sistematizada e análise documental."
    )
    eff_objectives = specific_objectives or [
        {
            "id": "OBJ-01",
            "description": "Mapear o referencial teórico e as normas técnicas aplicáveis ao tema.",
            "keywords": ["referencial", "normas", "padronização"],
            "target_section": "Fundamentação Teórica",
        },
        {
            "id": "OBJ-02",
            "description": "Avaliar os resultados obtidos frente ao problema de pesquisa proposto.",
            "keywords": ["resultados", "avaliação", "especificação"],
            "target_section": "Resultados e Discussão",
        },
    ]

    spec_res = init_project_spec(
        project_path=target_dir,
        title=title,
        research_problem=eff_problem,
        general_objective=eff_general,
        specific_objectives=eff_objectives,
        methodology_summary=eff_methodology,
        document_type=document_type,
        author=author,
        institution=institution,
        course=course,
        advisor=advisor,
        city=city,
        sample_pdf_path=sample_pdf_path,
        logo_path=logo_path,
    )
    spec = ResearchSpec(**spec_res["spec"])

    bib_file = target_dir / "referencias.bib"
    bib_content = """@article{silva2023,
  author  = {Silva, Maria Aparecida and Santos, João Carlos},
  title   = {Padronização Normativa e Rastreabilidade Científica em Manuscritos Acadêmicos},
  journal = {Revista Brasileira de Metodologia Científica},
  year    = {2023},
  volume  = {12},
  number  = {2},
  pages   = {45--62}
}
"""
    bib_file.write_text(bib_content, encoding="utf-8")

    if format == "typst":
        main_content = _render_scaffolded_typst(spec)
    elif format == "latex":
        main_content = _render_scaffolded_latex(spec)
    else:
        main_content = _render_scaffolded_markdown(spec)

    main_file.write_text(main_content, encoding="utf-8")

    intro_chapter = target_dir / "capitulos" / f"01-introducao{ext}"
    intro_chapter.write_text(
        f"% Capítulo 1 - Introdução ({title})\n{eff_problem}\n",
        encoding="utf-8",
    )

    created_files = [
        str(main_file),
        str(bib_file),
        spec_res["spec_json_path"],
        spec_res["spec_md_path"],
        str(intro_chapter),
    ]
    if spec.profile.cover_logo_path:
        created_files.append(str(target_dir / spec.profile.cover_logo_path))

    return ProjectScaffoldResult(
        success=True,
        project_path=str(target_dir),
        format=format,
        main_file=str(main_file),
        bib_file=str(bib_file),
        spec_json_path=spec_res["spec_json_path"],
        spec_md_path=spec_res["spec_md_path"],
        cover_logo_path=spec.profile.cover_logo_path,
        created_files=created_files,
        inferred_institutional_profile=spec_res.get("inferred_institutional_profile"),
        message=(
            f"Projeto acadêmico ({document_type.upper()}) inicializado em '{target_dir}' "
            f"no formato {format.upper()} com especificação SDD completa."
        ),
    )


def load_project_spec(project_path: str | Path, spec_path: str | Path | None = None) -> tuple[ResearchSpec, Path]:
    """Carrega e valida `abnt.spec.json` a partir do diretório do projeto ou caminho explícito."""
    if spec_path:
        sp = Path(spec_path)
    else:
        base = Path(project_path)
        proj_dir = base if base.is_dir() else base.parent
        sp = proj_dir / "abnt.spec.json"

    if not sp.is_file():
        raise FileNotFoundError(
            f"Manifesto de especificação 'abnt.spec.json' não encontrado em '{sp}'. "
            "Execute a ferramenta 'init_research_spec' para criar a especificação do projeto."
        )

    raw_data = json.loads(sp.read_text(encoding="utf-8"))
    return ResearchSpec(**raw_data), sp


def _extract_candidate_keywords(text: str) -> list[str]:
    """Extrai palavras substantivas (>= 5 letras) de um objetivo quando keywords não são fornecidas."""
    stopwords = {
        "sobre", "entre", "para", "como", "pelos", "pelas", "através", "partir",
        "estudo", "trabalho", "pesquisa", "forma", "meio", "dados", "análise",
        "analisar", "avaliar", "investigar", "desenvolver", "propor", "verificar",
        "identificar", "mapear", "compreender", "realizar", "elaborar", "implementar",
    }
    tokens = re.findall(r"[a-záéíóúâêôãõç0-9]{5,}", text.lower())
    keywords: list[str] = []
    for t in tokens:
        if t not in stopwords and t not in keywords:
            keywords.append(t)
        if len(keywords) >= 5:
            break
    return keywords


def _collect_manuscript_text(project_path: Path) -> str:
    """Coleta todo o texto do manuscrito ignorando SPEC.md e arquivos ocultos."""
    if project_path.is_file():
        if project_path.suffix.lower() == ".pdf":
            from abnt_mcp.parsers.pdf_reader import extract_pdf_section
            return extract_pdf_section(project_path)["text"]
        return project_path.read_text(encoding="utf-8", errors="replace")

    chunks: list[str] = []
    for f in sorted(project_path.rglob("*")):
        if (
            f.is_file()
            and f.suffix.lower() in {".tex", ".md", ".typ"}
            and f.name != "SPEC.md"
            and not any(p.startswith(".") or p in {"build", "dist", ".venv"} for p in f.parts)
        ):
            try:
                chunks.append(f.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
    return "\n\n".join(chunks)


def _split_body_and_conclusion(full_text: str) -> tuple[str, str]:
    """Separa o corpo do manuscrito e a seção de Conclusão / Considerações Finais."""
    concl_pattern = re.compile(
        r"(?:\\chapter\{[^}]*(?:conclus[ãa]o|considera[çc][õo]es\s+finais)[^}]*\}"
        r"|#+\s*\d*\s*(?:conclus[ãa]o|considera[çc][õo]es\s+finais)"
        r"|^=\s*\d*\s*(?:conclus[ãa]o|considera[çc][õo]es\s+finais)"
        r"|\b\d+\s+(?:CONCLUS[ÃA]O|CONSIDERA[ÇC][ÕO]ES\s+FINAIS)\b)",
        re.IGNORECASE | re.MULTILINE,
    )
    matches = list(concl_pattern.finditer(full_text))
    if not matches:
        return full_text, ""

    # Usa a última ocorrência (para não confundir com o Sumário)
    last_match = matches[-1]
    body_text = full_text[:last_match.start()]
    conclusion_text = full_text[last_match.start():]
    return body_text, conclusion_text


def _render_compliance_report_markdown(result: SpecAuditResult) -> str:
    """Renderiza o relatório consolidado de conformidade em Markdown (`.abnt-mcp/relatorio-conformidade.md`)."""
    lines = [
        f"# Relatório de Conformidade Acadêmica (SDD): {result.title}",
        "",
        f"- **Prontidão para Entrega (`submission_readiness`):** `{result.submission_readiness}`",
        f"- **Score Global SDD:** `{result.spec_compliance_score}/100`",
        f"- **Tipo Documental:** `{result.document_type.upper()}` (`{result.standard_applied}`)",
        f"- **Estrutura Normativa:** `{result.structure_score}/100`",
        f"- **Atendimento de Objetivos Específicos:** `{result.objectives_fulfillment_rate}%`",
        f"- **Rigor Científico (Heurístico):** `{result.tone_score}/100`",
        f"- **Referências no `.bib`:** `{result.references_count}/{result.min_references_required}`",
        "",
        "## 1. Auditoria de Objetivos Específicos (`OBJ-XX`)",
        "",
        "| ID | Status | Corpo | Conclusão | Feedback |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]
    for obj in result.objectives_audit:
        lines.append(
            f"| `{obj.id}` | `{obj.status}` | {'Sim' if obj.covered_in_body else 'Não'} "
            f"| {'Sim' if obj.answered_in_conclusion else 'Não'} | {obj.feedback} |"
        )

    lines.extend([
        "",
        "## 2. Conformidade Institucional e Ilustrações",
        "",
        f"- **Conformidade Institucional:** `{result.institutional_compliance.get('is_compliant', True)}`",
        f"- **Ilustrações / Tabelas Válidas:** `{result.illustrations_summary.get('is_valid', True)}` "
        f"(Figuras: {result.illustrations_summary.get('total_figures', 0)}, "
        f"Tabelas: {result.illustrations_summary.get('total_tables', 0)}, "
        f"Quadros: {result.illustrations_summary.get('total_quadros', 0)})",
        "",
        "## 3. Diagnósticos Rastreáveis",
        "",
    ])
    if not result.diagnostics:
        lines.append("- Nenhuma violação normativa ou institucional detectada.")
    else:
        for d in result.diagnostics:
            lines.append(
                f"- **[{d.severity.upper()}] `{d.rule_id}` ({d.nature}):** {d.message}"
                + (f" *(Sugestão: {d.suggestion})*" if d.suggestion else "")
            )

    lines.extend(["", "## 4. Recomendações Prioritárias", ""])
    for rec in result.recommendations:
        lines.append(f"- {rec}")
    lines.append("")
    return "\n".join(lines)


def audit_project_against_spec(
    project_path: str | Path,
    spec_path: str | Path | None = None,
) -> SpecAuditResult:
    """
    Executa a auditoria SDD completa confrontando o manuscrito acadêmico com o
    manifesto `abnt.spec.json` nas 3 camadas (Perfil Normativo/Institucional, Objetivos Específicos e Capítulos),
    auditando ilustrações/tabelas e persistindo relatórios em `.abnt-mcp/`.
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho do projeto não encontrado: {path}")

    proj_dir = path if path.is_dir() else path.parent
    spec, resolved_spec_path = load_project_spec(path, spec_path)

    # 1. Auditoria da Camada 1: Estrutura, Citações, Ilustrações/Tabelas e Tom Científico
    structure_res = check_project_structure(path, standard=spec.profile.standard)
    citations_res = audit_citations_and_references(path)
    illus_res = audit_project_illustrations_and_tables(path)
    full_text = _collect_manuscript_text(path)
    tone_res = analyze_scientific_tone(full_text)

    body_text, conclusion_text = _split_body_and_conclusion(full_text)
    body_lower = body_text.lower()
    concl_lower = conclusion_text.lower()
    full_lower = full_text.lower()

    # 1b. Auditoria de Regras Institucionais (aprendidas do PDF da faculdade ou configuradas no perfil)
    institutional_diagnostics: list[DiagnosticItem] = []
    missing_institutional_elements: list[str] = []
    full_ascii = unicodedata.normalize("NFKD", full_lower).encode("ascii", "ignore").decode("ascii")

    for req_elem in spec.profile.required_pre_textual:
        elem_low = req_elem.lower()
        elem_ascii = unicodedata.normalize("NFKD", elem_low).encode("ascii", "ignore").decode("ascii")
        found_in_struct = elem_low in [e.lower() for e in structure_res.elements_found]
        found_in_text = (elem_low in full_lower) or (elem_ascii in full_ascii)
        if not (found_in_struct or found_in_text):
            missing_institutional_elements.append(req_elem)
            institutional_diagnostics.append(DiagnosticItem(
                rule_id="INST-PROFILE-PRETEXTUAL",
                nature="institutional",
                severity="error",
                confidence="high",
                message=f"Elemento pré-textual exigido pelo padrão institucional ausente: '{req_elem}'.",
                suggestion=f"Inclua a seção '{req_elem}' conforme o modelo da instituição ({spec.profile.institution or 'universidade'}).",
                human_review_required=False,
            ))

    logo_ok = True
    if spec.profile.has_cover_logo:
        logo_rel = spec.profile.cover_logo_path or "figuras/logo_instituicao.png"
        logo_file = proj_dir / logo_rel
        logo_referenced = (logo_rel.lower() in full_lower) or (Path(logo_rel).name.lower() in full_lower)
        if not logo_file.is_file() or not logo_referenced:
            logo_ok = False
            institutional_diagnostics.append(DiagnosticItem(
                rule_id="INST-PROFILE-LOGO",
                nature="institutional",
                severity="warning",
                confidence="high",
                message=(
                    f"O perfil institucional prevê logotipo na capa ('{logo_rel}'), "
                    "mas o arquivo não foi encontrado ou não está referenciado na capa do manuscrito."
                ),
                suggestion=f"Verifique o arquivo '{logo_rel}' e sua inclusão na capa do documento.",
                human_review_required=False,
            ))

    institutional_compliance = {
        "institution": spec.profile.institution,
        "inferred_from_pdf": spec.profile.inferred_from_pdf,
        "required_pre_textual": spec.profile.required_pre_textual,
        "missing_pre_textual": missing_institutional_elements,
        "has_cover_logo": spec.profile.has_cover_logo,
        "cover_logo_verified": logo_ok,
        "is_compliant": len(missing_institutional_elements) == 0 and logo_ok,
    }

    illustrations_summary = {
        "is_valid": illus_res.is_valid,
        "total_figures": illus_res.total_figures,
        "total_tables": illus_res.total_tables,
        "total_quadros": illus_res.total_quadros,
        "unreferenced_count": len(illus_res.unreferenced_items),
        "missing_sources_count": len(illus_res.missing_sources),
        "broken_images_count": len(illus_res.broken_image_paths),
        "quadro_vs_tabela_warnings_count": len(illus_res.quadro_vs_tabela_warnings),
    }

    # 2. Auditoria da Camada 2: Matriz Científica (Objetivos Específicos OBJ-XX)
    objectives_audit: list[ObjectiveAuditItem] = []
    fulfilled_points = 0.0

    for obj in spec.specific_objectives:
        kws = obj.keywords or _extract_candidate_keywords(obj.description)
        matched_in_body = [k for k in kws if k.lower() in body_lower]
        matched_in_concl = [k for k in kws if k.lower() in concl_lower]

        covered_in_body = len(matched_in_body) > 0 if kws else bool(body_text.strip())
        answered_in_conclusion = len(matched_in_concl) > 0 if kws else bool(conclusion_text.strip())

        matched_all = sorted(list(set(matched_in_body + matched_in_concl)))
        missing_all = [k for k in kws if k not in matched_all]

        if covered_in_body and answered_in_conclusion:
            status: Literal["fulfilled", "partial", "missing"] = "fulfilled"
            fulfilled_points += 1.0
            feedback = (
                f"Objetivo {obj.id} desenvolvido no texto e respondido na Conclusão "
                f"(termos validados: {', '.join(matched_all)})."
            )
        elif covered_in_body or answered_in_conclusion:
            status = "partial"
            fulfilled_points += 0.5
            if not answered_in_conclusion:
                feedback = (
                    f"Objetivo {obj.id} abordado no desenvolvimento, mas NÃO retomado explicitamente "
                    f"na Conclusão/Considerações Finais."
                )
            else:
                feedback = f"Objetivo {obj.id} mencionado na conclusão, mas pouco aprofundado no corpo textual."
        else:
            status = "missing"
            feedback = (
                f"Objetivo {obj.id} órfão: termos-chave ({', '.join(kws)}) não foram encontrados "
                "nem no desenvolvimento nem na conclusão."
            )

        objectives_audit.append(
            ObjectiveAuditItem(
                id=obj.id,
                description=obj.description,
                status=status,
                covered_in_body=covered_in_body,
                answered_in_conclusion=answered_in_conclusion,
                matched_keywords=matched_all,
                missing_keywords=missing_all,
                feedback=feedback,
            )
        )

    total_objs = len(spec.specific_objectives)
    objectives_fulfillment_rate = int((fulfilled_points / total_objs) * 100) if total_objs else 100

    # 3. Auditoria da Camada 3: Capítulos Planejados
    chapters_audit: list[ChapterAuditItem] = []
    found_chapters_count = 0

    for ch in spec.planned_chapters:
        title_clean = ch.title.strip().lower()
        found = title_clean in full_lower
        if found:
            found_chapters_count += 1
            ch_feedback = f"Seção '{ch.number} {ch.title}' localizada no manuscrito."
        else:
            ch_feedback = f"Seção planejada '{ch.number} {ch.title}' ausente no manuscrito."
        chapters_audit.append(
            ChapterAuditItem(
                number=ch.number,
                title=ch.title,
                found_in_document=found,
                feedback=ch_feedback,
            )
        )

    total_chapters = len(spec.planned_chapters)
    chapters_rate = int((found_chapters_count / total_chapters) * 100) if total_chapters else 100

    # 4. Consolidação de Violações Normativas Rastreáveis e Diagnósticos Unificados
    normative_issues: list[dict[str, str]] = list(structure_res.rule_violations)

    if citations_res.uppercase_violations:
        normative_issues.append({
            "rule_id": "NBR10520-R01",
            "standard": NORMATIVE_RULES["NBR10520-R01"]["standard"],
            "severity": "error",
            "message": f"Encontradas {len(citations_res.uppercase_violations)} citações em CAIXA ALTA entre parênteses.",
        })

    if citations_res.orphan_citations:
        normative_issues.append({
            "rule_id": "NBR10520-R02",
            "standard": NORMATIVE_RULES["NBR10520-R02"]["standard"],
            "severity": "error",
            "message": f"Encontradas {len(citations_res.orphan_citations)} citações órfãs no texto sem correspondente no .bib.",
        })

    if citations_res.total_references_in_bib < spec.profile.min_references:
        normative_issues.append({
            "rule_id": "NBR6023-R02",
            "standard": NORMATIVE_RULES["NBR6023-R02"]["standard"],
            "severity": "warning",
            "message": (
                f"Quantidade de referências no .bib ({citations_res.total_references_in_bib}) "
                f"inferior à meta da spec ({spec.profile.min_references})."
            ),
        })

    all_diagnostics: list[DiagnosticItem] = (
        list(structure_res.diagnostics)
        + list(citations_res.diagnostics)
        + list(illus_res.diagnostics)
        + institutional_diagnostics
        + list(tone_res.diagnostics)
    )

    # 5. Cálculo do spec_compliance_score (0 a 100)
    ref_ratio = min(1.0, citations_res.total_references_in_bib / max(1, spec.profile.min_references))
    rigor_and_refs_score = int((tone_res.score * 0.6) + (ref_ratio * 100 * 0.4))

    spec_compliance_score = int(
        (structure_res.compliance_score * 0.35)
        + (objectives_fulfillment_rate * 0.40)
        + (chapters_rate * 0.15)
        + (rigor_and_refs_score * 0.10)
    )

    recommendations: list[str] = list(structure_res.recommendations)
    for item in objectives_audit:
        if item.status != "fulfilled":
            recommendations.append(
                f"[{item.id}] Retome os conceitos ({', '.join(item.missing_keywords or [item.description[:40]])}) "
                "no Desenvolvimento e responda-os diretamente na Conclusão."
            )
    for ch_item in chapters_audit:
        if not ch_item.found_in_document:
            recommendations.append(f"Adicione o capítulo planejado '{ch_item.number} {ch_item.title}'.")
    for miss_inst in missing_institutional_elements:
        recommendations.append(f"Inclua o elemento pré-textual institucional obrigatório '{miss_inst}'.")
    if citations_res.total_references_in_bib < spec.profile.min_references:
        recommendations.append(
            f"Amplie a revisão bibliográfica no arquivo .bib de {citations_res.total_references_in_bib} "
            f"para pelo menos {spec.profile.min_references} referências."
        )

    has_blocking_errors = any(
        d.nature in {"normative", "institutional"} and d.severity in {"error", "critical"}
        for d in all_diagnostics
    )

    is_compliant = (
        structure_res.is_valid
        and objectives_fulfillment_rate >= 80
        and citations_res.is_consistent
        and institutional_compliance["is_compliant"]
        and not has_blocking_errors
        and spec_compliance_score >= 80
    )

    if not is_compliant or any(o.status == "missing" for o in objectives_audit):
        submission_readiness: Literal["READY", "READY_WITH_WARNINGS", "NOT_READY"] = "NOT_READY"
    elif (
        any(d.severity == "warning" for d in all_diagnostics)
        or objectives_fulfillment_rate < 100
        or not illus_res.is_valid
        or citations_res.total_references_in_bib < spec.profile.min_references
    ):
        submission_readiness = "READY_WITH_WARNINGS"
    else:
        submission_readiness = "READY"

    audit_result = SpecAuditResult(
        spec_path=str(resolved_spec_path),
        title=spec.title,
        document_type=spec.profile.document_type,
        standard_applied=structure_res.standard,
        is_compliant=is_compliant,
        submission_readiness=submission_readiness,
        spec_compliance_score=spec_compliance_score,
        structure_score=structure_res.compliance_score,
        objectives_fulfillment_rate=objectives_fulfillment_rate,
        tone_score=tone_res.score,
        references_count=citations_res.total_references_in_bib,
        min_references_required=spec.profile.min_references,
        institutional_compliance=institutional_compliance,
        illustrations_summary=illustrations_summary,
        objectives_audit=objectives_audit,
        chapters_audit=chapters_audit,
        normative_issues=normative_issues,
        diagnostics=all_diagnostics,
        recommendations=recommendations,
    )

    # 6. Persiste relatórios em .abnt-mcp/
    try:
        reports_dir = proj_dir / ".abnt-mcp"
        reports_dir.mkdir(parents=True, exist_ok=True)
        last_audit_json = reports_dir / "last-audit.json"
        report_md = reports_dir / "relatorio-conformidade.md"

        audit_result.saved_report_paths = {
            "json": str(last_audit_json),
            "markdown": str(report_md),
        }
        last_audit_json.write_text(
            json.dumps(audit_result.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report_md.write_text(_render_compliance_report_markdown(audit_result), encoding="utf-8")
    except Exception:
        pass

    return audit_result


def get_spec_template_resource() -> str:
    """Retorna o template JSON comentado para o resource `abnt://template/spec`."""
    template_obj = {
        "spec_version": "1.0",
        "title": "Título Completo do Trabalho Acadêmico ou Artigo Científico",
        "author": "Nome Completo do Autor",
        "research_problem": "Qual pergunta científica o estudo responde?",
        "general_objective": "Analisar/Desenvolver/Avaliar...",
        "methodology_summary": "Pesquisa aplicada, exploratória, revisão sistemática ou estudo de caso...",
        "profile": {
            "document_type": "tcc",
            "standard": "ABNT_14724",
            "institution": "Universidade / Instituição",
            "emphasis_style": "bold",
            "min_references": 15,
            "min_scientific_tone_score": 80,
        },
        "specific_objectives": [
            {
                "id": "OBJ-01",
                "description": "Mapear o referencial teórico e as normas técnicas aplicáveis ao domínio.",
                "keywords": ["referencial", "normas", "mapeamento"],
                "target_section": "Fundamentação Teórica",
            },
            {
                "id": "OBJ-02",
                "description": "Avaliar empiricamente os resultados obtidos frente às hipóteses iniciais.",
                "keywords": ["resultados", "avaliação", "empírico"],
                "target_section": "Resultados e Discussão",
            },
        ],
        "planned_chapters": DEFAULT_PLANNED_CHAPTERS_TCC,
    }
    return json.dumps(template_obj, indent=2, ensure_ascii=False)
