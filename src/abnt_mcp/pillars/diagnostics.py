"""Pilar 1: Analisar & Diagnosticar.

Validação Estrutural (NBR 14724), Auditoria de Citações vs Referências
e Análise de Tom e Rigor Científico.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any

from abnt_mcp.config import (
    FIRST_PERSON_PRONOUNS,
    FIRST_PERSON_VERBS,
    VALUE_JUDGMENTS,
    COLLOQUIALISMS,
    RE_INVALID_SECTION_DOT,
)
from abnt_mcp.models import (
    StructureCheckResult,
    ToneAnalysisResult,
    ToneIssue,
    CitationValidationResult,
)
from abnt_mcp.parsers.citations import (
    extract_citations_from_project,
)
from abnt_mcp.parsers.bibtex import (
    extract_bib_keys_and_dois,
)


# Elementos da NBR 14724:2011 classificados
MANDATORY_ELEMENTS: dict[str, list[str]] = {
    "pre_textual": [
        "capa",
        "folha de rosto",
        "resumo",
        "abstract",
        "sumario",
    ],
    "textual": [
        "introducao",
        "desenvolvimento",  # engloba metodologia/resultados/fundamentacao
        "conclusao",        # ou consideracoes finais
    ],
    "post_textual": [
        "referencias",
    ],
}

OPTIONAL_ELEMENTS: list[str] = [
    "lombada",
    "errata",
    "folha de aprovacao",
    "dedicatoria",
    "agradecimentos",
    "epigrafe",
    "lista de ilustracoes",
    "lista de tabelas",
    "lista de abreviaturas",
    "lista de simbolos",
    "glossario",
    "apendices",
    "anexos",
    "indice",
]

# Padrões regex para detecção flexível nos fontes (.tex, .md, .typ) e no texto final extraído de PDF
ELEMENT_PATTERNS: dict[str, re.Pattern] = {
    "capa": re.compile(r"(\\begin\{capa\}|\\imprimircapa|#imprimircapa|#page\(|title:|#set document\(title:|\buniversidade\b|\bfaculdade\b|\binstituto federal\b|\bcentro universit[áa]rio\b)", re.IGNORECASE),
    "folha de rosto": re.compile(r"(\\imprimirfolhaderosto|folha\s*de\s*rosto|titlepage|trabalho\s*de\s*conclus[ãa]o|disserta[çc][ãa]o|tese\s*apresentad|orientador:)", re.IGNORECASE),
    "folha de aprovacao": re.compile(r"(folha\s*de\s*aprova[çc][ãa]o|banca\s*examinadora|termo\s*de\s*aprova[çc][ãa]o)", re.IGNORECASE),
    "dedicatoria": re.compile(r"(\\begin\{dedicatoria\}|#dedicatoria|\bdedicat[óo]ria\b)", re.IGNORECASE),
    "agradecimentos": re.compile(r"(\\begin\{agradecimentos\}|#agradecimentos|\bagradecimentos\b)", re.IGNORECASE),
    "epigrafe": re.compile(r"(\\begin\{epigrafe\}|#epigrafe|\bep[íi]grafe\b)", re.IGNORECASE),
    "resumo": re.compile(r"(\\begin\{resumo\}|#resumo|\b#?resumo\b)", re.IGNORECASE),
    "abstract": re.compile(r"(\\begin\{abstract\}|#abstract|\b#?abstract\b)", re.IGNORECASE),
    "lista de ilustracoes": re.compile(r"(\\listoffigures|lista\s*de\s*ilustra[çc][õo]es|lista\s*de\s*figuras)", re.IGNORECASE),
    "lista de tabelas": re.compile(r"(\\listoftables|lista\s*de\s*tabelas)", re.IGNORECASE),
    "lista de abreviaturas": re.compile(r"(\\listofsiglas|lista\s*de\s*(?:abreviaturas|siglas))", re.IGNORECASE),
    "sumario": re.compile(r"(\\tableofcontents|#outline\(|\b#?sum[áa]rio\b)", re.IGNORECASE),
    "introducao": re.compile(r"(\\chapter\{.*introdu[çc][ãa]o.*\}|#chapter\[.*introdu[çc][ãa]o.*\]|#heading\(.*introdu[çc][ãa]o.*\)|#+\s*1?\s*introdu[çc][ãa]o|\b1\s+introdu[çc][ãa]o\b)", re.IGNORECASE),
    "desenvolvimento": re.compile(r"(\\chapter\{|#chapter\[|#heading|#+\s*[2-9]|\b[2-9]\s+[A-ZÁÉÍÓÚ])", re.IGNORECASE),
    "conclusao": re.compile(r"(conclus[ãa]o|considera[çc][õo]es\s*finais)", re.IGNORECASE),
    "referencias": re.compile(r"(\\bibliography|\\printbibliography|#bibliography|\b#?refer[êe]ncias\b)", re.IGNORECASE),
    "apendices": re.compile(r"(\\apendices|#apendice|\bap[êe]ndice\b)", re.IGNORECASE),
    "anexos": re.compile(r"(\\anexos|#anexo|\banexo\b)", re.IGNORECASE),
}


def check_project_structure(project_path: str | Path, standard: str = "ABNT_14724") -> StructureCheckResult:
    """
    Verifica a presença e a conformidade dos elementos pré-textuais, textuais
    e pós-textuais de acordo com a ABNT NBR 14724:2011 e NBR 6024:2012.
    Suporta diretórios, arquivos-fonte (.tex, .md, .typ) e arquivos .pdf finais.
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho do projeto não encontrado: {path}")

    # Coleta todo o texto do projeto
    all_content: list[str] = []
    file_count = 0

    pagination_issues: list[dict[str, Any]] = []

    if path.is_file():
        if path.suffix.lower() == ".pdf":
            from abnt_mcp.parsers.pdf_reader import extract_pdf_section, audit_pdf_pagination
            pdf_data = extract_pdf_section(path)
            all_content.append(pdf_data["text"])
            file_count = 1

            # Auditoria estrita de paginação no PDF conforme a ABNT NBR 14724 (item 5.3)
            try:
                pag_audit = audit_pdf_pagination(path)
                if not pag_audit["is_compliant"]:
                    pagination_issues = pag_audit["issues"]
            except Exception:
                pass
        else:
            files = [path]
            for f in files:
                try:
                    all_content.append(f.read_text(encoding="utf-8", errors="replace"))
                    file_count += 1
                except Exception:
                    pass
    else:
        files = [
            f for f in path.rglob("*")
            if f.is_file() and f.suffix.lower() in {".tex", ".md", ".typ"}
            and not any(p.startswith(".") or p in {"build", "dist", ".venv"} for p in f.parts)
        ]
        for f in files:
            try:
                all_content.append(f.read_text(encoding="utf-8", errors="replace"))
                file_count += 1
            except Exception:
                continue

    combined_text = "\n\n".join(all_content)

    elements_found: set[str] = set()
    for elem_name, pattern in ELEMENT_PATTERNS.items():
        if pattern.search(combined_text):
            elements_found.add(elem_name)

    # Checa obrigatórios
    missing_mandatory: list[str] = []
    for category, items in MANDATORY_ELEMENTS.items():
        for item in items:
            if item not in elements_found:
                missing_mandatory.append(f"{item} ({category})")

    # Checa opcionais presentes
    optional_present = [elem for elem in OPTIONAL_ELEMENTS if elem in elements_found]

    # Validação de seções (NBR 6024: sem ponto no final do número da seção)
    section_warnings: list[str] = []
    invalid_dot_matches = RE_INVALID_SECTION_DOT.findall(combined_text)
    for num, title in invalid_dot_matches:
        section_warnings.append(
            f"Seção '{num}. {title}' possui ponto após o último algarismo (NBR 6024 exige '{num} {title}')."
        )

    # Incorpora avisos de paginação NBR 14724 se houver
    has_critical_pagination_error = False
    for p_iss in pagination_issues:
        section_warnings.append(f"[Paginação NBR 14724] {p_iss['message']}")
        if p_iss.get("severity") == "critical":
            has_critical_pagination_error = True

    # Cálculo da pontuação
    total_mandatory = sum(len(items) for items in MANDATORY_ELEMENTS.values())
    found_mandatory = total_mandatory - len(missing_mandatory)
    base_score = int((found_mandatory / total_mandatory) * 100) if total_mandatory else 100

    # Penalidade por erros de numeração de seção e paginação
    section_penalty = min(15, len(section_warnings) * 3)
    pag_penalty = 25 if has_critical_pagination_error else 0
    final_score = max(0, base_score - section_penalty - pag_penalty)

    recommendations: list[str] = []
    if missing_mandatory:
        recommendations.append(
            f"Inclua os elementos obrigatórios ausentes: {', '.join(missing_mandatory)}."
        )
    if pagination_issues:
        recommendations.append(
            "Corrija os erros de paginação segundo a ABNT NBR 14724 (item 5.3): a contagem inicia na Folha de Rosto e nenhum elemento pré-textual pode conter número impresso."
        )
    if section_warnings:
        recommendations.append(
            "Remova os pontos ao final dos números de seções (use '1.1 Seção' em vez de '1.1. Seção')."
        )
    if "folha de aprovacao" not in elements_found:
        recommendations.append(
            "Lembre-se de adicionar a Folha de Aprovação na versão final para a banca examinadora."
        )
    if "resumo" in elements_found and "abstract" in elements_found:
        recommendations.append(
            "Certifique-se de que o Resumo e o Abstract contenham de 150 a 500 palavras e de 3 a 5 palavras-chave."
        )

    is_valid = len(missing_mandatory) == 0 and final_score >= 80 and not has_critical_pagination_error

    return StructureCheckResult(
        standard="NBR 14724:2011",
        is_valid=is_valid,
        compliance_score=final_score,
        document_type="TCC / Dissertação / Tese ABNT",
        missing_mandatory=missing_mandatory,
        optional_elements_present=optional_present,
        elements_found=sorted(list(elements_found)),
        section_warnings=section_warnings[:10],
        recommendations=recommendations,
    )


def audit_citations_and_references(
    project_path: str | Path,
    bib_path: str | Path | None = None
) -> CitationValidationResult:
    """
    Cruza o texto do projeto com o arquivo .bib e aponta citações órfãs,
    entradas no .bib nunca citadas e citações em caixa alta violando a NBR 10520:2023.
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho não encontrado: {path}")

    project_dir = path if path.is_dir() else path.parent

    # 1. Encontra o arquivo .bib
    bib_files: list[Path] = []
    if bib_path:
        bp = Path(bib_path)
        if bp.exists():
            bib_files.append(bp)
    else:
        bib_files = list(project_dir.rglob("*.bib"))

    all_bib_keys: set[str] = set()
    for bf in bib_files:
        try:
            content = bf.read_text(encoding="utf-8", errors="replace")
            keys, _ = extract_bib_keys_and_dois(content)
            all_bib_keys.update(keys)
        except Exception:
            continue

    # 2. Extrai citações do texto
    citations_by_key, uppercase_violations = extract_citations_from_project(project_dir)

    all_cited_keys = set(citations_by_key.keys())

    # Citações órfãs: citadas no texto mas não presentes no bib
    orphan_citations: list[dict[str, str | int]] = []
    for cited_key, occurrences in citations_by_key.items():
        if cited_key not in all_bib_keys:
            for occ in occurrences:
                orphan_citations.append({
                    "key": cited_key,
                    "file": occ["file"],
                    "line": occ["line"],
                })

    # Entradas no .bib nunca citadas
    unused_references = sorted(list(all_bib_keys - all_cited_keys))

    is_consistent = len(orphan_citations) == 0 and len(uppercase_violations) == 0

    return CitationValidationResult(
        total_citations_in_text=len(all_cited_keys),
        total_references_in_bib=len(all_bib_keys),
        orphan_citations=orphan_citations,
        unused_references=unused_references,
        uppercase_violations=uppercase_violations,
        is_consistent=is_consistent,
    )


def analyze_scientific_tone(text: str) -> ToneAnalysisResult:
    """
    Analisa o tom acadêmico e rigor científico:
    - 1ª pessoa ("eu fiz", "nós achamos", "meu trabalho")
    - Juízos de valor sem fundamentação ("obviamente", "claramente")
    - Coloquialismos ("a gente", "pra caramba", "coisa")
    - Parágrafos longos sem fundamentação
    """
    issues: list[ToneIssue] = []
    lines = text.splitlines()
    words = text.split()
    total_words = len(words)

    # 1. Checagem linha a linha por palavras e expressões
    for line_idx, line in enumerate(lines, start=1):
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("%") or line_clean.startswith("#"):
            continue

        line_tokens = [
            t.strip(".,;:?!'\"()[]{}").lower()
            for t in line_clean.split()
        ]

        # Pronomes em 1ª pessoa
        for token_idx, token in enumerate(line_tokens):
            if token in FIRST_PERSON_PRONOUNS:
                # Disambiguação de 'nos': em português é contração da preposição 'em + os'
                # quando seguido de substantivos ou adjetivos plurais
                if token == "nos" and token_idx + 1 < len(line_tokens):
                    next_token = line_tokens[token_idx + 1]
                    if next_token.endswith("s") or next_token in {"mais", "menos", "quais", "seus", "suas", "outros", "outras", "dados", "casos", "setores"}:
                        continue

                issues.append(ToneIssue(
                    category="first_person",
                    term=token,
                    context=line_clean[:120],
                    line_number=line_idx,
                    suggestion=f"Substitua o pronome '{token}' por construção impessoal (ex: 'observou-se', 'constata-se')."
                ))

            # Verbos em 1ª pessoa
            if token in FIRST_PERSON_VERBS:
                issues.append(ToneIssue(
                    category="first_person",
                    term=token,
                    context=line_clean[:120],
                    line_number=line_idx,
                    suggestion=f"Substitua a conjugação em 1ª pessoa '{token}' pela voz passiva sintética (ex: 'analisou-se', 'propôs-se')."
                ))

        # Juízos de valor
        lower_line = line_clean.lower()
        for phrase, suggestion in VALUE_JUDGMENTS:
            if re.search(rf"\b{re.escape(phrase)}\b", lower_line):
                issues.append(ToneIssue(
                    category="value_judgment",
                    term=phrase,
                    context=line_clean[:120],
                    line_number=line_idx,
                    suggestion=suggestion
                ))

        # Coloquialismos
        for phrase, suggestion in COLLOQUIALISMS:
            if re.search(rf"\b{re.escape(phrase)}\b", lower_line):
                issues.append(ToneIssue(
                    category="colloquialism",
                    term=phrase,
                    context=line_clean[:120],
                    line_number=line_idx,
                    suggestion=suggestion
                ))

    # 2. Checagem de parágrafos sem fundamentação
    paragraphs = text.split("\n\n")
    for p_idx, p in enumerate(paragraphs, start=1):
        clean_p = p.strip()
        p_words = clean_p.split()
        # Se tem mais de 60 palavras e nenhuma citação ou número aparente
        if len(p_words) > 60:
            has_cite = bool(
                re.search(r"(\\cite|@\w+|\(\w+,\s*\d{4}\))", clean_p)
                or re.search(r"\b(19\d\d|20\d\d)\b", clean_p)
            )
            if not has_cite:
                issues.append(ToneIssue(
                    category="ungrounded_paragraph",
                    term=f"Parágrafo {p_idx} sem fundamentação",
                    context=clean_p[:140] + "...",
                    line_number=None,
                    suggestion="Parágrafo extenso contendo alegações sem citação bibliográfica ou comprovação empírica direta."
                ))

    # Cálculo da nota de rigor
    penalty = len(issues) * 7
    score = max(10, 100 - penalty)
    is_acceptable = score >= 75 and len(issues) <= 3

    suggested_rewrites = [
        {
            "original": "Nós analisamos os resultados obtidos e claramente percebemos um avanço.",
            "reescrita_abnt": "Analisaram-se os resultados obtidos, constatando-se avanços estatisticamente relevantes conforme os dados observados."
        },
        {
            "original": "Eu fiz uma pesquisa e achei a coisa muito boa pra caramba.",
            "reescrita_abnt": "Realizou-se uma investigação bibliográfica que evidenciou a eficácia do método proposto."
        }
    ]

    summary = (
        f"Texto analisado com {total_words} palavras. Foram encontrados {len(issues)} pontos de atenção. "
        f"Nota de Rigor Científico: {score}/100. "
        + ("O texto necessita de ajustes de impessoalidade e objetividade." if not is_acceptable else "Texto com ótimo rigor científico.")
    )

    return ToneAnalysisResult(
        score=score,
        is_acceptable=is_acceptable,
        total_words=total_words,
        issues_count=len(issues),
        issues=issues,
        summary=summary,
        suggested_rewrites=suggested_rewrites,
    )
