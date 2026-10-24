from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..utils import read_file_with_fallback, remove_comments


MANDATORY_PRE_TEXTUAL = {
    "capa": "Capa",
    "folha_de_rosto": "Folha de Rosto",
    "resumo": "Resumo em Língua Vernácula",
    "abstract": "Resumo em Língua Estrangeira (Abstract)",
    "sumario": "Sumário",
}

OPTIONAL_PRE_TEXTUAL = {
    "errata": "Errata",
    "dedicatoria": "Dedicatória",
    "agradecimentos": "Agradecimentos",
    "epigrafe": "Epígrafe",
    "lista_ilustracoes": "Lista de Ilustrações",
    "lista_tabelas": "Lista de Tabelas",
    "lista_abreviaturas": "Lista de Abreviaturas e Siglas",
}

MANDATORY_TEXTUAL = {
    "introducao": "Introdução",
    "desenvolvimento": "Desenvolvimento (Fundamentação / Metodologia / Resultados)",
    "conclusao": "Conclusão ou Considerações Finais",
}

MANDATORY_POST_TEXTUAL = {
    "referencias": "Referências Bibliográficas",
}

OPTIONAL_POST_TEXTUAL = {
    "apendices": "Apêndices",
    "anexos": "Anexos",
    "glossario": "Glossário",
}


def check_tcc_structure(project_path: str) -> dict[str, Any]:
    """Valida a estrutura do trabalho acadêmico de acordo com a norma ABNT NBR 14724.
    
    Diferencia com rigor os elementos estritamente obrigatórios dos elementos
    opcionais (ex: listas de tabelas e ilustrações são opcionais e não geram erro).
    Suporta projetos em LaTeX (.tex), Markdown (.md) e Typst (.typ).
    """
    project = Path(project_path)
    if not project.exists():
        return {"status": "error", "message": f"Diretório não encontrado: {project_path}"}

    format_detected, all_content = load_project_clean_content(project)
    if format_detected is None:
        return {"status": "error", "message": "Nenhum arquivo textual (.tex, .md, .typ) foi encontrado."}

    detected_elements = scan_elements(all_content, format_detected)

    missing_mandatory_pre = [
        name for key, name in MANDATORY_PRE_TEXTUAL.items() if key not in detected_elements
    ]
    missing_mandatory_textual = [
        name for key, name in MANDATORY_TEXTUAL.items() if key not in detected_elements
    ]
    missing_mandatory_post = [
        name for key, name in MANDATORY_POST_TEXTUAL.items() if key not in detected_elements
    ]

    all_missing = missing_mandatory_pre + missing_mandatory_textual + missing_mandatory_post
    present_optional = [
        name for key, name in {**OPTIONAL_PRE_TEXTUAL, **OPTIONAL_POST_TEXTUAL}.items()
        if key in detected_elements
    ]

    is_compliant = len(all_missing) == 0

    return {
        "status": "success",
        "norma": "ABNT NBR 14724",
        "format": format_detected,
        "is_compliant": is_compliant,
        "missing_mandatory_elements": all_missing,
        "present_mandatory_elements": [
            name for key, name in {**MANDATORY_PRE_TEXTUAL, **MANDATORY_TEXTUAL, **MANDATORY_POST_TEXTUAL}.items()
            if key in detected_elements
        ],
        "present_optional_elements": present_optional,
        "message": (
            "Estrutura em total conformidade com a NBR 14724!"
            if is_compliant
            else f"Atenção: faltam {len(all_missing)} elemento(s) obrigatório(s) para a conformidade com a ABNT."
        )
    }


def load_project_clean_content(project: Path) -> tuple[str | None, str]:
    """Lê e concatena o conteúdo de texto desconsiderando comentários."""
    tex_files = list(project.glob("**/*.tex"))
    if tex_files:
        texts = [remove_comments(read_file_with_fallback(f), "tex") for f in tex_files]
        return "latex", "\n".join(texts)

    md_files = [f for f in project.glob("**/*.md") if "readme" not in f.name.lower()]
    if md_files:
        texts = [remove_comments(read_file_with_fallback(f), "md") for f in md_files]
        return "markdown", "\n".join(texts)

    typ_files = list(project.glob("**/*.typ"))
    if typ_files:
        texts = [remove_comments(read_file_with_fallback(f), "typ") for f in typ_files]
        return "typst", "\n".join(texts)

    return None, ""


def scan_elements(content: str, doc_format: str) -> set[str]:
    """Verifica comandos estruturais para evitar falsos positivos de palavras no meio de frases."""
    detected = set()

    # Padrões para Capa e Folha de Rosto
    if re.search(r"\\(?:imprimircapa|maketitle|begin\{titlepage\})|#cover|title:\s*|#page\(", content, re.I):
        detected.add("capa")
    if re.search(r"\\imprimirfolhaderosto|folha\s+de\s+rosto", content, re.I):
        detected.add("folha_de_rosto")

    # Resumo e Abstract
    if re.search(r"\\begin\{resumo\}|#heading.*resumo|#align.*resumo|^#+\s*resumo\b", content, re.I | re.M):
        detected.add("resumo")
    if re.search(r"\\begin\{abstract\}|#heading.*abstract|#align.*abstract|^#+\s*abstract\b", content, re.I | re.M):
        detected.add("abstract")

    # Sumário
    if re.search(r"\\tableofcontents|#outline\(|^#+\s*sum[aá]rio\b", content, re.I | re.M):
        detected.add("sumario")

    # Listas Opcionais
    if re.search(r"\\listoffigures|lista\s+de\s+figuras|lista\s+de\s+ilustra[cç][õo]es", content, re.I):
        detected.add("lista_ilustracoes")
    if re.search(r"\\listoftables|lista\s+de\s+tabelas", content, re.I):
        detected.add("lista_tabelas")
    if re.search(r"lista\s+de\s+(?:abreviaturas|siglas)", content, re.I):
        detected.add("lista_abreviaturas")

    # Introdução (comando de seção ou título Markdown/Typst)
    if re.search(r"\\chapter\*?\{.*introdu[cç][aã]o.*\}|^#+\s*introdu[cç][aã]o\b|=+\s*introdu[cç][aã]o\b", content, re.I | re.M):
        detected.add("introducao")

    # Desenvolvimento (presença de capítulos técnicos além da introdução e conclusão)
    dev_matches = re.findall(
        r"\\chapter\*?\{(?!(?:introdu[cç][aã]o|conclus[aã]o|considera[cç][õo]es|refer[êe]ncias|resumo|abstract))([^}]+)\}|"
        r"^#+\s*(?!(?:introdu[cç][aã]o|conclus[aã]o|considera[cç][õo]es|refer[êe]ncias|resumo|abstract))(.+)$",
        content,
        re.I | re.M
    )
    if dev_matches:
        detected.add("desenvolvimento")

    # Conclusão
    if re.search(r"\\chapter\*?\{.*(?:conclus[aã]o|considera[cç][õo]es\s+finais).*\}|^#+\s*(?:conclus[aã]o|considera[cç][õo]es\s+finais)\b", content, re.I | re.M):
        detected.add("conclusao")

    # Referências
    if re.search(r"\\(?:bibliography|printbibliography)|\\begin\{thebibliography\}|#bibliography\(|^#+\s*refer[êe]ncias\b", content, re.I | re.M):
        detected.add("referencias")

    # Apêndices e Anexos (opcionais)
    if re.search(r"\\(?:begin\{apendicesenv\}|part\{ap[êe]ndices\}|apendices)|^#+\s*ap[êe]ndice", content, re.I | re.M):
        detected.add("apendices")
    if re.search(r"\\(?:begin\{anexosenv\}|part\{anexos\}|anexos)|^#+\s*anexo", content, re.I | re.M):
        detected.add("anexos")

    return detected
