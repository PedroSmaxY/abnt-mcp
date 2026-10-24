"""Extrator e validador de citações em documentos LaTeX, Markdown e Typst."""

from __future__ import annotations
import re
from pathlib import Path
from abnt_mcp.config import RE_UPPERCASE_CITATION
from abnt_mcp.models import CitationValidationResult


# Padrões de captura de chaves de citação
# LaTeX: \cite{key}, \citeonline{key1, key2}, \citep{key}, \citet{key}, \apud[...]{key}
RE_LATEX_CITE = re.compile(
    r"\\(?:cite|citeonline|citep|citet|citeauthor|citeyear|nocite|apud)(?:\[[^\]]*\])*\{([^}]+)\}"
)

# Markdown: [@key], [-@key], [@key1; @key2; p. 10], ou @key no texto
# Citações entre colchetes
RE_MD_BRACKET_CITE = re.compile(r"\[([^\]]*@[a-zA-Z0-9_\-:]+[^\]]*)\]")
# Citação isolada no texto: @key (precedida por espaço, início de linha ou pontuação, não email)
RE_MD_INLINE_CITE = re.compile(r"(?<![\w\.\-])@([a-zA-Z0-9_\-]+)")

# Typst: @key ou [@key]
RE_TYPST_CITE = re.compile(r"(?<![\w\.\-])@([a-zA-Z0-9_\-]+)")


def extract_citations_from_latex(content: str) -> list[tuple[str, int]]:
    """Extrai todas as chaves de citação de código LaTeX com número da linha."""
    citations: list[tuple[str, int]] = []
    lines = content.splitlines()
    for line_num, line in enumerate(lines, start=1):
        # Ignora linhas comentadas no LaTeX
        clean_line = line.split("%")[0] if "%" in line else line
        for match in RE_LATEX_CITE.finditer(clean_line):
            keys_group = match.group(1)
            for k in keys_group.split(","):
                key = k.strip()
                if key:
                    citations.append((key, line_num))
    return citations


def extract_citations_from_markdown(content: str) -> list[tuple[str, int]]:
    """Extrai todas as chaves de citação de Markdown (estilo Pandoc) com número da linha."""
    citations: list[tuple[str, int]] = []
    lines = content.splitlines()
    for line_num, line in enumerate(lines, start=1):
        # 1. Chaves dentro de colchetes [@key] ou [@key1; @key2]
        for match in RE_MD_BRACKET_CITE.finditer(line):
            bracket_text = match.group(1)
            for key_match in re.finditer(r"@([a-zA-Z0-9_\-]+)", bracket_text):
                citations.append((key_match.group(1).strip(), line_num))

        # 2. Chaves inline como @key (não precedidas por colchete já capturado)
        for inline_match in RE_MD_INLINE_CITE.finditer(line):
            key = inline_match.group(1).strip()
            # Evita duplicar se já foi capturado na mesma linha dentro de colchetes
            if not any(c[0] == key and c[1] == line_num for c in citations):
                citations.append((key, line_num))
    return citations


def extract_citations_from_typst(content: str) -> list[tuple[str, int]]:
    """Extrai chaves de citação de documentos Typst com número da linha."""
    citations: list[tuple[str, int]] = []
    lines = content.splitlines()
    for line_num, line in enumerate(lines, start=1):
        clean_line = line.split("//")[0] if "//" in line else line
        for match in RE_TYPST_CITE.finditer(clean_line):
            key = match.group(1).strip()
            if key and not key.isdigit():  # evita falsos positivos
                citations.append((key, line_num))
    return citations


def detect_uppercase_citations(content: str) -> list[dict[str, str | int]]:
    """Detecta citações com autor em caixa alta violando a NBR 10520:2023."""
    violations: list[dict[str, str | int]] = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        for match in RE_UPPERCASE_CITATION.finditer(line):
            raw = match.group(0)
            authors = match.group(1)
            year_part = match.group(2)
            # Sugestão com inicial maiúscula
            fixed_authors = "; ".join(
                part.strip().title() for part in authors.split(";")
            )
            violations.append({
                "line": line_num,
                "found": raw,
                "suggested": f"({fixed_authors}, {year_part})",
                "explanation": "NBR 10520:2023 extinguiu o uso de CAIXA ALTA para autores entre parênteses."
            })
    return violations


def extract_citations_from_project(
    project_dir: Path
) -> tuple[dict[str, list[dict[str, str | int]]], list[dict[str, str | int]]]:
    """Varre todos os arquivos de texto (.tex, .md, .typ) do projeto e extrai citações."""
    citations_by_key: dict[str, list[dict[str, str | int]]] = {}
    all_uppercase_violations: list[dict[str, str | int]] = []

    file_extensions = {".tex", ".md", ".markdown", ".typ"}

    for file_path in project_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in file_extensions:
            # Ignora pastas de cache ou build
            if any(part.startswith(".") or part in {"build", "dist", ".venv", "node_modules"} for part in file_path.parts):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Extrai violações de caixa alta
            file_violations = detect_uppercase_citations(content)
            for v in file_violations:
                v["file"] = file_path.name
                all_uppercase_violations.append(v)

            # Extrai citações conforme a extensão
            ext = file_path.suffix.lower()
            if ext == ".tex":
                items = extract_citations_from_latex(content)
            elif ext in {".md", ".markdown"}:
                items = extract_citations_from_markdown(content)
            elif ext == ".typ":
                items = extract_citations_from_typst(content)
            else:
                items = []

            for key, line in items:
                citations_by_key.setdefault(key, []).append({
                    "file": file_path.name,
                    "line": line
                })

    return citations_by_key, all_uppercase_violations
