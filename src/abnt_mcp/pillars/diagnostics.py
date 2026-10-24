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
    NORMATIVE_RULES,
)
from abnt_mcp.models import (
    DiagnosticItem,
    StructureCheckResult,
    ToneAnalysisResult,
    ToneIssue,
    CitationValidationResult,
    IllustrationAuditResult,
)
from abnt_mcp.parsers.citations import (
    extract_citations_from_project,
)
from abnt_mcp.parsers.bibtex import (
    extract_bib_keys_and_dois,
)


# Elementos da NBR 14724:2011 classificados (Monografias/TCC/Dissertações/Teses)
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

# Elementos obrigatórios da NBR 6022:2018 (Artigos Científicos Periódicos)
MANDATORY_ELEMENTS_6022: dict[str, list[str]] = {
    "pre_textual": [
        "resumo",
        "abstract",
    ],
    "textual": [
        "introducao",
        "desenvolvimento",
        "conclusao",
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
    "introducao": re.compile(r"(\\chapter\{.*introdu[çc][ãa]o.*\}|#chapter\[.*introdu[çc][ãa]o.*\]|#heading\(.*introdu[çc][ãa]o.*\)|#+\s*1?\s*introdu[çc][ãa]o|^=\s*1?\s*introdu[çc][ãa]o|\b1\s+introdu[çc][ãa]o\b)", re.IGNORECASE | re.MULTILINE),
    "desenvolvimento": re.compile(r"(\\chapter\{|#chapter\[|#heading|#+\s*[2-9]|^=\s*(?:[2-9]|fundamenta[çc][ãa]o|metodologia|resultados)|\b[2-9]\s+[A-ZÁÉÍÓÚ])", re.IGNORECASE | re.MULTILINE),
    "conclusao": re.compile(r"(conclus[ãa]o|considera[çc][õo]es\s*finais)", re.IGNORECASE),
    "referencias": re.compile(r"(\\bibliography|\\printbibliography|#bibliography|\b#?refer[êe]ncias\b)", re.IGNORECASE),
    "apendices": re.compile(r"(\\apendices|#apendice|\bap[êe]ndice\b)", re.IGNORECASE),
    "anexos": re.compile(r"(\\anexos|#anexo|\banexo\b)", re.IGNORECASE),
}


def check_project_structure(project_path: str | Path, standard: str = "ABNT_14724") -> StructureCheckResult:
    """
    Verifica a presença e a conformidade dos elementos pré-textuais, textuais
    e pós-textuais de acordo com a ABNT NBR 14724:2011, NBR 6022:2018 e NBR 6024:2012.
    Suporta diretórios, arquivos-fonte (.tex, .md, .typ) e arquivos .pdf finais.
    Auto-detecta o perfil normativo de 'abnt.spec.json' quando presente no projeto.
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho do projeto não encontrado: {path}")

    project_dir = path if path.is_dir() else path.parent

    # Auto-detecta padrão normativo a partir de abnt.spec.json se o usuário não forçou outro
    effective_standard = standard.upper().strip()
    spec_file = project_dir / "abnt.spec.json"
    if effective_standard == "ABNT_14724" and spec_file.is_file():
        try:
            import json
            spec_raw = json.loads(spec_file.read_text(encoding="utf-8"))
            spec_std = spec_raw.get("profile", {}).get("standard", "")
            if spec_std in {"ABNT_14724", "ABNT_6022"}:
                effective_standard = spec_std
        except Exception:
            pass

    is_article_6022 = "6022" in effective_standard
    active_mandatory = MANDATORY_ELEMENTS_6022 if is_article_6022 else MANDATORY_ELEMENTS
    structure_rule_id = "NBR6022-R01" if is_article_6022 else "NBR14724-R01"

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
            if not is_article_6022:
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
            and f.name != "SPEC.md"
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

    rule_violations: list[dict[str, str]] = []
    diagnostics: list[DiagnosticItem] = []

    # Checa obrigatórios
    missing_mandatory: list[str] = []
    for category, items in active_mandatory.items():
        for item in items:
            if item not in elements_found:
                missing_mandatory.append(f"{item} ({category})")
                msg = f"Elemento obrigatório ausente: '{item}' ({category})."
                rule_violations.append({
                    "rule_id": structure_rule_id,
                    "standard": NORMATIVE_RULES[structure_rule_id]["standard"],
                    "severity": NORMATIVE_RULES[structure_rule_id]["severity"],
                    "message": msg,
                })
                diagnostics.append(DiagnosticItem(
                    rule_id=structure_rule_id,
                    nature="normative",
                    severity="error",
                    confidence="high",
                    message=msg,
                    suggestion=f"Adicione a seção/elemento '{item}' conforme exigido pela {NORMATIVE_RULES[structure_rule_id]['standard']}.",
                    human_review_required=False,
                ))

    # Checa opcionais presentes
    optional_present = [elem for elem in OPTIONAL_ELEMENTS if elem in elements_found]

    # Validação de seções (NBR 6024: sem ponto no final do número da seção)
    section_warnings: list[str] = []
    invalid_dot_matches = RE_INVALID_SECTION_DOT.findall(combined_text)
    for num, title in invalid_dot_matches:
        msg = f"Seção '{num}. {title}' possui ponto após o último algarismo (NBR 6024 exige '{num} {title}')."
        section_warnings.append(msg)
        rule_violations.append({
            "rule_id": "NBR6024-R01",
            "standard": NORMATIVE_RULES["NBR6024-R01"]["standard"],
            "severity": NORMATIVE_RULES["NBR6024-R01"]["severity"],
            "message": msg,
        })
        diagnostics.append(DiagnosticItem(
            rule_id="NBR6024-R01",
            nature="normative",
            severity="warning",
            confidence="high",
            message=msg,
            suggestion=f"Substitua '{num}. {title}' por '{num} {title}'.",
            human_review_required=False,
        ))

    # Incorpora avisos de paginação NBR 14724 se houver
    has_critical_pagination_error = False
    for p_iss in pagination_issues:
        section_warnings.append(f"[Paginação NBR 14724] {p_iss['message']}")
        sev_str = str(p_iss.get("severity", "critical"))
        rule_violations.append({
            "rule_id": "NBR14724-R02",
            "standard": NORMATIVE_RULES["NBR14724-R02"]["standard"],
            "severity": sev_str,
            "message": p_iss["message"],
        })
        diagnostics.append(DiagnosticItem(
            rule_id="NBR14724-R02",
            nature="normative",
            severity="critical" if sev_str == "critical" else "warning",
            confidence="high",
            message=p_iss["message"],
            suggestion="Suprima a numeração impressa nos elementos pré-textuais e inicie a contagem na Folha de Rosto.",
            human_review_required=False,
        ))
        if sev_str == "critical":
            has_critical_pagination_error = True

    # Cálculo da pontuação
    total_mandatory = sum(len(items) for items in active_mandatory.values())
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
    if not is_article_6022 and "folha de aprovacao" not in elements_found:
        recommendations.append(
            "Lembre-se de adicionar a Folha de Aprovação na versão final para a banca examinadora."
        )
    if "resumo" in elements_found and "abstract" in elements_found:
        recommendations.append(
            "Certifique-se de que o Resumo e o Abstract contenham de 150 a 500 palavras (100 a 250 para artigos) e de 3 a 5 palavras-chave."
        )

    is_valid = len(missing_mandatory) == 0 and final_score >= 80 and not has_critical_pagination_error

    return StructureCheckResult(
        standard="NBR 6022:2018" if is_article_6022 else "NBR 14724:2011",
        is_valid=is_valid,
        compliance_score=final_score,
        document_type="Artigo Científico Periódico (ABNT NBR 6022)" if is_article_6022 else "TCC / Dissertação / Tese ABNT",
        missing_mandatory=missing_mandatory,
        optional_elements_present=optional_present,
        elements_found=sorted(list(elements_found)),
        section_warnings=section_warnings[:10],
        rule_violations=rule_violations,
        diagnostics=diagnostics,
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

    diagnostics: list[DiagnosticItem] = []
    for uv in uppercase_violations:
        diagnostics.append(DiagnosticItem(
            rule_id="NBR10520-R01",
            nature="normative",
            severity="error",
            confidence="high",
            message=f"Citação em CAIXA ALTA entre parênteses '{uv.get('match')}' viola a ABNT NBR 10520:2023.",
            suggestion="Converta o sobrenome dentro dos parênteses para caixa mista (ex: '(Silva, 2023)').",
            file=str(uv.get("file", "")),
            line=int(uv["line"]) if isinstance(uv.get("line"), int) else None,
            human_review_required=False,
        ))

    for oc in orphan_citations:
        diagnostics.append(DiagnosticItem(
            rule_id="NBR10520-R02",
            nature="normative",
            severity="error",
            confidence="high",
            message=f"Citação órfã '{oc.get('key')}' no texto sem entrada correspondente no arquivo .bib.",
            suggestion=f"Adicione a entrada '@...{{{oc.get('key')}, ...}}' ao arquivo .bib ou corrija a chave citada.",
            file=str(oc.get("file", "")),
            line=int(oc["line"]) if isinstance(oc.get("line"), int) else None,
            human_review_required=False,
        ))

    for ur in unused_references:
        diagnostics.append(DiagnosticItem(
            rule_id="NBR10520-R02",
            nature="normative",
            severity="warning",
            confidence="high",
            message=f"A referência '{ur}' consta no arquivo .bib mas nunca foi citada no texto.",
            suggestion="Cite a obra no corpo do texto ou remova-a do arquivo .bib antes da entrega final.",
            human_review_required=False,
        ))

    is_consistent = len(orphan_citations) == 0 and len(uppercase_violations) == 0

    return CitationValidationResult(
        total_citations_in_text=len(all_cited_keys),
        total_references_in_bib=len(all_bib_keys),
        orphan_citations=orphan_citations,
        unused_references=unused_references,
        uppercase_violations=uppercase_violations,
        diagnostics=diagnostics,
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

    tone_diagnostics: list[DiagnosticItem] = [
        DiagnosticItem(
            rule_id=f"HEURISTIC-TONE-{iss.category.upper()}",
            nature="heuristic",
            severity="warning",
            confidence="medium",
            message=f"[{iss.category}] Termo ou trecho detectado: '{iss.term}'.",
            suggestion=iss.suggestion,
            line=iss.line_number,
            human_review_required=True,
        )
        for iss in issues
    ]

    return ToneAnalysisResult(
        score=score,
        is_acceptable=is_acceptable,
        total_words=total_words,
        issues_count=len(issues),
        issues=issues,
        diagnostics=tone_diagnostics,
        summary=summary,
        suggested_rewrites=suggested_rewrites,
    )


def audit_project_illustrations_and_tables(project_path: str | Path) -> IllustrationAuditResult:
    """
    Audita figuras, tabelas e quadros do projeto conforme a ABNT NBR 14724 (item 5.8)
    e as Normas de Apresentação Tabular do IBGE (1993):
    1. Verifica chamada prévia obrigatória no texto antes da ilustração/tabela ('Figura X', 'Tabela X', 'Quadro X');
    2. Verifica presença obrigatória de 'Fonte:' (ou '\\fonte{...}') na parte inferior;
    3. Verifica existência física dos arquivos de imagem referenciados em Markdown, LaTeX e Typst;
    4. Verifica sequência numérica (sem saltos ou duplicidades por categoria);
    5. Detecta possível confusão conceitual entre Tabela (quantitativo/bordas laterais abertas) e Quadro (qualitativo/fechado).
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho do projeto não encontrado: {path}")

    project_dir = path if path.is_dir() else path.parent
    if path.is_file():
        files = [path]
    else:
        files = sorted([
            f for f in path.rglob("*")
            if f.is_file()
            and f.suffix.lower() in {".tex", ".md", ".typ"}
            and f.name != "SPEC.md"
            and not any(p.startswith(".") or p in {"build", "dist", ".venv"} for p in f.parts)
        ])

    unreferenced_items: list[dict[str, Any]] = []
    missing_sources: list[dict[str, Any]] = []
    broken_image_paths: list[dict[str, Any]] = []
    numbering_issues: list[dict[str, Any]] = []
    quadro_vs_tabela_warnings: list[dict[str, Any]] = []
    diagnostics: list[DiagnosticItem] = []

    counts = {"figura": 0, "tabela": 0, "quadro": 0}
    seen_numbers: dict[str, list[tuple[int, str, int]]] = {"figura": [], "tabela": [], "quadro": []}

    decl_pattern = re.compile(
        r"(?:^\s*(?:\*\*|\*|#figure\(|\\caption\{)?\s*(Figura|Tabela|Quadro)\s+(\d+)\s*[-–—:]\s*([^\n*\]\}]+))",
        re.IGNORECASE,
    )
    img_patterns = [
        re.compile(r"!\[[^\]]*\]\(([^)]+)\)"),
        re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}"),
        re.compile(r'#?image\("([^"]+)"'),
    ]

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel_file = str(f.relative_to(project_dir)) if f.is_relative_to(project_dir) else f.name
        lines = content.splitlines()

        # 1. Verifica caminhos de imagens quebrados
        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("%") or stripped.startswith("//"):
                continue
            for pat in img_patterns:
                for m_img in pat.finditer(line):
                    raw_img_path = m_img.group(1).strip()
                    if raw_img_path.startswith(("http://", "https://", "data:")):
                        continue
                    candidate_1 = project_dir / raw_img_path
                    candidate_2 = f.parent / raw_img_path
                    if not (candidate_1.is_file() or candidate_2.is_file()):
                        item_err = {
                            "image_path": raw_img_path,
                            "file": rel_file,
                            "line": line_idx,
                        }
                        broken_image_paths.append(item_err)
                        diagnostics.append(DiagnosticItem(
                            rule_id="NBR14724-R03",
                            nature="normative",
                            severity="error",
                            confidence="high",
                            message=f"Arquivo de imagem '{raw_img_path}' não encontrado no projeto.",
                            suggestion=f"Verifique o caminho da imagem '{raw_img_path}' ou adicione o arquivo em 'figuras/'.",
                            file=rel_file,
                            line=line_idx,
                            human_review_required=False,
                        ))

        # 2. Verifica declarações de Figuras, Tabelas e Quadros
        for idx, line in enumerate(lines):
            m_decl = decl_pattern.search(line)
            if not m_decl:
                continue

            kind_raw = m_decl.group(1).lower()
            num_val = int(m_decl.group(2))
            caption_title = m_decl.group(3).strip()
            line_no = idx + 1

            counts[kind_raw] += 1
            seen_numbers[kind_raw].append((num_val, rel_file, line_no))

            # 2a. Verifica chamada prévia no texto antes da linha atual
            preceding_text = "\n".join(lines[:idx])
            call_regex = re.compile(
                rf"\b{kind_raw}\s+{num_val}\b|\\ref\{{|@(?:fig|tab|quadro)",
                re.IGNORECASE,
            )
            if not call_regex.search(preceding_text):
                unref_info = {
                    "type": kind_raw,
                    "number": num_val,
                    "title": caption_title,
                    "file": rel_file,
                    "line": line_no,
                }
                unreferenced_items.append(unref_info)
                diagnostics.append(DiagnosticItem(
                    rule_id="NBR14724-R03",
                    nature="normative",
                    severity="warning",
                    confidence="high",
                    message=(
                        f"{kind_raw.capitalize()} {num_val} ('{caption_title}') não possui chamada textual prévia "
                        f"no parágrafo anterior (ex: 'conforme a {kind_raw.capitalize()} {num_val}')."
                    ),
                    suggestion=f"Insira uma chamada no texto antes da {kind_raw.capitalize()} {num_val}.",
                    file=rel_file,
                    line=line_no,
                    human_review_required=False,
                ))

            # Determina o limite do bloco atual (até a próxima Figura/Tabela/Quadro ou até 15 linhas)
            block_end_idx = min(len(lines), idx + 16)
            for next_i in range(idx + 1, block_end_idx):
                if decl_pattern.search(lines[next_i]):
                    block_end_idx = next_i
                    break

            # 2b. Verifica presença de 'Fonte:' dentro do bloco do item atual
            window_lines = lines[idx:block_end_idx]
            window_text = "\n".join(window_lines)
            has_source = bool(re.search(r"(?:\bfonte\s*:|\\fonte\{|\\legend\{)", window_text, re.IGNORECASE))
            if not has_source:
                miss_info = {
                    "type": kind_raw,
                    "number": num_val,
                    "title": caption_title,
                    "file": rel_file,
                    "line": line_no,
                }
                missing_sources.append(miss_info)
                diagnostics.append(DiagnosticItem(
                    rule_id="NBR14724-R03",
                    nature="normative",
                    severity="error",
                    confidence="high",
                    message=(
                        f"{kind_raw.capitalize()} {num_val} ('{caption_title}') não apresenta indicação obrigatória "
                        "de 'Fonte:' na parte inferior (mesmo quando elaborada pelo próprio autor)."
                    ),
                    suggestion="Adicione 'Fonte: Elaborado pelo autor (ANO).' na parte inferior.",
                    file=rel_file,
                    line=line_no,
                    human_review_required=False,
                ))

            # 2c. Verifica distinção conceitual Tabela vs Quadro (IBGE 1993)
            if kind_raw == "tabela":
                # Se usa bordas verticais fechadas no LaTeX (\begin{tabular}{|...|}) ou se as linhas da tabela não têm nenhum dígito
                body_window = "\n".join(lines[idx + 1 : block_end_idx])
                has_closed_latex_borders = bool(re.search(r"\\begin\{tabular\}\{\|.*\|\}", body_window))
                # Linhas de células markdown/latex
                cell_lines = [
                    ln for ln in lines[idx + 1 : block_end_idx]
                    if ("|" in ln or "&" in ln) and not re.match(r"^\s*\|?[\s\-:|]+\|?\s*$", ln)
                ]
                cells_joined = " ".join(cell_lines)
                has_only_text_in_cells = len(cell_lines) >= 2 and not bool(re.search(r"\d", cells_joined))

                if has_closed_latex_borders or has_only_text_in_cells:
                    reason = (
                        "bordas laterais fechadas em LaTeX ('{|...|}')"
                        if has_closed_latex_borders
                        else "conteúdo exclusivamente textual/qualitativo sem dados numéricos"
                    )
                    warn_item = {
                        "type": "tabela",
                        "number": num_val,
                        "title": caption_title,
                        "reason": reason,
                        "file": rel_file,
                        "line": line_no,
                    }
                    quadro_vs_tabela_warnings.append(warn_item)
                    diagnostics.append(DiagnosticItem(
                        rule_id="IBGE1993-R01",
                        nature="normative",
                        severity="warning",
                        confidence="medium",
                        message=(
                            f"Tabela {num_val} ('{caption_title}') apresenta {reason}. "
                            "Pelas Normas Tabulares do IBGE (1993), dados qualitativos/textuais com bordas fechadas constituem um 'Quadro'."
                        ),
                        suggestion=f"Avalie reclassificar 'Tabela {num_val}' para 'Quadro {num_val}' ou remover bordas verticais laterais.",
                        file=rel_file,
                        line=line_no,
                        human_review_required=True,
                    ))

    # 3. Verifica sequência numérica por categoria
    for kind_raw, items_list in seen_numbers.items():
        expected = 1
        for num_val, rel_file, line_no in items_list:
            if num_val != expected:
                num_err = {
                    "type": kind_raw,
                    "found_number": num_val,
                    "expected_number": expected,
                    "file": rel_file,
                    "line": line_no,
                }
                numbering_issues.append(num_err)
                diagnostics.append(DiagnosticItem(
                    rule_id="NBR14724-R03",
                    nature="normative",
                    severity="warning",
                    confidence="high",
                    message=(
                        f"Quebra de sequência numérica em {kind_raw.capitalize()}: encontrado número {num_val}, "
                        f"mas esperava-se {expected}."
                    ),
                    suggestion=f"Renumere sequencialmente para '{kind_raw.capitalize()} {expected}'.",
                    file=rel_file,
                    line=line_no,
                    human_review_required=False,
                ))
            expected = num_val + 1

    is_valid = (
        len(unreferenced_items) == 0
        and len(missing_sources) == 0
        and len(broken_image_paths) == 0
        and len(numbering_issues) == 0
    )

    return IllustrationAuditResult(
        is_valid=is_valid,
        total_figures=counts["figura"],
        total_tables=counts["tabela"],
        total_quadros=counts["quadro"],
        unreferenced_items=unreferenced_items,
        missing_sources=missing_sources,
        broken_image_paths=broken_image_paths,
        numbering_issues=numbering_issues,
        quadro_vs_tabela_warnings=quadro_vs_tabela_warnings,
        diagnostics=diagnostics,
    )
