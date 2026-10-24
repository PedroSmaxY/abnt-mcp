from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from ..utils import read_file_with_fallback, remove_comments
from .bibtex import parse_bib_keys


def validate_citations(project_path: str) -> dict[str, Any]:
    """Valida referências cruzadas entre o texto (LaTeX, Markdown ou Typst) e o arquivo .bib.
    
    Identifica citações órfãs (usadas no texto mas ausentes no .bib) e referências
    não utilizadas (presentes no .bib mas nunca citadas no texto).
    """
    project = Path(project_path)
    if not project.exists():
        return {"status": "error", "message": f"Diretório não encontrado: {project_path}"}

    # 1. Localizar arquivo .bib
    bib_file = find_bib_file(project)
    if not bib_file:
        return {
            "status": "error",
            "message": "Nenhum arquivo de bibliografia (.bib) encontrado no projeto."
        }

    bib_keys = parse_bib_keys(str(bib_file))

    # 2. Identificar formato predominante e extrair citações
    detected_format, citations_found = extract_all_project_citations(project)

    if detected_format is None:
        return {
            "status": "error",
            "message": "Nenhum arquivo de documento (.tex, .md, .typ) foi encontrado no projeto."
        }

    orphan_citations = sorted(list(citations_found - bib_keys))
    uncited_references = sorted(list(bib_keys - citations_found))

    return {
        "status": "success",
        "format": detected_format,
        "bib_file": str(bib_file.name),
        "total_unique_citations": len(citations_found),
        "total_bib_entries": len(bib_keys),
        "orphan_citations": orphan_citations,
        "uncited_references": uncited_references,
        "is_healthy": len(orphan_citations) == 0,
        "message": (
            "Perfeito! Todas as citações existem no arquivo .bib."
            if not orphan_citations
            else f"Atenção: {len(orphan_citations)} citação(ões) órfã(s) encontrada(s)."
        )
    }


def find_bib_file(project: Path) -> Optional[Path]:
    """Localiza o arquivo .bib principal do projeto."""
    for candidate in ["referencias.bib", "references.bib", "bibliografia.bib"]:
        p = project / candidate
        if p.exists():
            return p
    # Busca recursiva
    bibs = list(project.glob("**/*.bib"))
    return bibs[0] if bibs else None


def extract_all_project_citations(project: Path) -> tuple[Optional[str], set[str]]:
    """Extrai todas as citações do projeto com base no formato (LaTeX, Markdown ou Typst)."""
    citations = set()

    # Checar se é LaTeX
    tex_files = list(project.glob("**/*.tex"))
    if tex_files:
        main_tex = find_main_tex(project)
        if main_tex:
            all_resolved = resolve_tex_files(main_tex)
            for f in all_resolved:
                content = read_file_with_fallback(f)
                citations.update(extract_latex_citations(content))
            return "latex", citations

    # Checar se é Markdown
    md_files = list(project.glob("**/*.md"))
    if md_files:
        for f in md_files:
            # Ignora READMEs
            if "readme" in f.name.lower():
                continue
            content = read_file_with_fallback(f)
            citations.update(extract_markdown_citations(content))
        return "markdown", citations

    # Checar se é Typst
    typ_files = list(project.glob("**/*.typ"))
    if typ_files:
        for f in typ_files:
            content = read_file_with_fallback(f)
            citations.update(extract_typst_citations(content))
        return "typst", citations

    return None, citations


def find_main_tex(project: Path) -> Optional[Path]:
    for name in ["main.tex", "tcc.tex", "dissertacao.tex", "tese.tex", "artigo.tex"]:
        target = project / name
        if target.exists():
            return target
    texs = list(project.glob("*.tex"))
    return texs[0] if texs else None


def resolve_tex_files(main_tex: Path, visited: Optional[set[Path]] = None) -> list[Path]:
    r"""Resolve recursivamente \input e \include evitando loops infinitos."""
    if visited is None:
        visited = set()

    normalized = main_tex.resolve()
    if normalized in visited or not normalized.exists():
        return []

    visited.add(normalized)
    files = [normalized]

    content = read_file_with_fallback(normalized)
    clean = remove_comments(content, "tex")

    for match in re.finditer(r"\\(?:input|include|subfile)\{([^}]+)\}", clean):
        target_name = match.group(1).strip()
        if not target_name.endswith(".tex"):
            target_name += ".tex"
        child_path = normalized.parent / target_name
        files.extend(resolve_tex_files(child_path, visited))

    return files


def extract_latex_citations(raw_content: str) -> set[str]:
    """Extrai chaves de citação LaTeX (abntex2, natbib, biblatex)."""
    clean = remove_comments(raw_content, "tex")
    citations = set()

    # Suporte aos comandos abntex2 e padrão TeX: \cite, \citeonline, \apud, \citet, \citep, etc.
    patterns = [
        r"\\(?:cite|citeonline|citet|citep|citeauthor|citeyear|apud|citeauthoronline|cif)\*?(?:\[[^\]]*\])*\{([^}]+)\}",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, clean):
            raw_keys = match.group(1).split(",")
            for k in raw_keys:
                clean_k = k.strip()
                if clean_k:
                    citations.add(clean_k)

    return citations


def extract_markdown_citations(raw_content: str) -> set[str]:
    """Extrai chaves de citação do Pandoc Markdown: [@silva2020], [-@silva2020] ou @silva2020."""
    clean = remove_comments(raw_content, "md")
    citations = set()

    # Formato entre colchetes: [@silva2020; @santos2021]
    bracketed = re.findall(r"\[([^\]]*@[a-zA-Z0-9_\-:\.]+[^\]]*)\]", clean)
    for group in bracketed:
        matches = re.findall(r"(?:^|[\s;])-?@([a-zA-Z0-9_\-:\.]+)", group)
        citations.update(matches)

    # Formato inline: @silva2020
    inline_matches = re.findall(r"(?<![a-zA-Z0-9_\-])@([a-zA-Z0-9_\-:\.]+)", clean)
    citations.update(inline_matches)

    return citations


def extract_typst_citations(raw_content: str) -> set[str]:
    """Extrai chaves de citação do Typst: @chave ou @chave:pagina."""
    clean = remove_comments(raw_content, "typ")
    citations = set()

    # No Typst, citações são precedidas por @ e delimitadas por espaço/pontuação
    matches = re.findall(r"(?<![a-zA-Z0-9_\-])@([a-zA-Z0-9_\-:\.]+)", clean)
    citations.update(matches)

    return citations
