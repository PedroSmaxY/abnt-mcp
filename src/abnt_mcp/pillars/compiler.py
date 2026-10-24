"""Pilar 3: Testar & Compilar.

Compilador multi-engine (LaTeX abnTeX2, Typst, Pandoc/Markdown) com
pré-checagem estrutural, ciclo multi-pass e linter de sintaxe com diagnóstico amigável.
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def lint_latex_source(content: str) -> list[dict[str, Any]]:
    """Analisa o código LaTeX antes da compilação detectando erros clássicos."""
    issues: list[dict[str, Any]] = []
    lines = content.splitlines()

    # 1. Checagem de balanceamento de ambientes \begin{env} / \end{env}
    stack: list[tuple[str, int]] = []
    for line_num, line in enumerate(lines, start=1):
        clean_line = line.split("%")[0] if "%" in line else line

        for begin_match in re.finditer(r"\\begin\{([^}]+)\}", clean_line):
            stack.append((begin_match.group(1), line_num))

        for end_match in re.finditer(r"\\end\{([^}]+)\}", clean_line):
            env_name = end_match.group(1)
            if not stack:
                issues.append({
                    "line": line_num,
                    "level": "error",
                    "type": "unmatched_end",
                    "message": f"\\end{{{env_name}}} sem correspondente \\begin{{{env_name}}} anterior."
                })
            else:
                last_env, start_line = stack.pop()
                if last_env != env_name:
                    issues.append({
                        "line": line_num,
                        "level": "error",
                        "type": "mismatched_env",
                        "message": f"Ambiente fechado \\end{{{env_name}}} não fecha o último aberto \\begin{{{last_env}}} na linha {start_line}."
                    })

    for env_name, line_num in stack:
        issues.append({
            "line": line_num,
            "level": "error",
            "type": "unclosed_begin",
            "message": f"Ambiente \\begin{{{env_name}}} na linha {line_num} nunca foi fechado com \\end{{{env_name}}}."
        })

    # 2. Caracteres especiais desprotegidos em texto comum
    # %, _, &, $, # fora de comandos matemáticos ou comentários
    for line_num, line in enumerate(lines, start=1):
        clean_line = line.split("%")[0] if "%" in line else line
        # Checa '_' fora de modo matemático e fora de \cite/\label/\ref/\bibliography
        if "_" in clean_line and not re.search(r"(\$|\\label|\\cite|\\ref|\\input|\\include|\\bibliography)", clean_line):
            if re.search(r"(?<!\\)_", clean_line):
                issues.append({
                    "line": line_num,
                    "level": "warning",
                    "type": "unescaped_underscore",
                    "message": "Caractere sublinhado '_' desprotegido fora de modo matemático. Use '\\_' se for texto."
                })

    return issues


def parse_latex_log_for_errors(log_content: str) -> list[dict[str, Any]]:
    """Extrai erros e alertas específicos de um arquivo .log do LaTeX."""
    errors: list[dict[str, Any]] = []

    # Procura linhas com '! '
    lines = log_content.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("!"):
            msg = stripped[1:].strip()
            line_ref = None
            # Tenta pegar linha seguinte para achar 'l.XXX'
            context = []
            for j in range(i, min(len(lines), i + 6)):
                context.append(lines[j])
                match_l = re.search(r"l\.(\d+)", lines[j])
                if match_l:
                    line_ref = int(match_l.group(1))
                    break

            errors.append({
                "message": msg,
                "line": line_ref,
                "context": "\n".join(context)
            })

    # Procura referências indefinidas (ex: LaTeX Warning: Citation `xxx' on page X undefined)
    for match in re.finditer(r"LaTeX Warning: Citation `([^']+)' on page \d+ undefined", log_content):
        errors.append({
            "message": f"Citação indefinida: '{match.group(1)}'. Verifique se consta no arquivo .bib.",
            "line": None,
            "context": match.group(0)
        })

    return errors


def compile_project(project_path: str | Path, engine: str = "auto") -> dict[str, Any]:
    """
    Compila o projeto acadêmico para PDF utilizando o engine apropriado
    (LaTeX, Pandoc ou Typst) com pré-checagens e diagnóstico de erros.
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho não encontrado: {path}")

    target_dir = path if path.is_dir() else path.parent

    # Detecta automaticamente se o engine for 'auto'
    selected_engine = engine.lower()
    main_file: Path | None = None

    if selected_engine == "auto":
        if path.is_file():
            main_file = path
            ext = path.suffix.lower()
            if ext == ".tex":
                selected_engine = "latex"
            elif ext in {".md", ".markdown"}:
                selected_engine = "markdown"
            elif ext == ".typ":
                selected_engine = "typst"
        else:
            # Procura arquivos principais comuns no diretório
            candidates_tex = list(target_dir.glob("main.tex")) or list(target_dir.glob("tcc.tex")) or list(target_dir.glob("*.tex"))
            candidates_typ = list(target_dir.glob("main.typ")) or list(target_dir.glob("*.typ"))
            candidates_md = list(target_dir.glob("main.md")) or list(target_dir.glob("tcc.md")) or list(target_dir.glob("*.md"))

            if candidates_typ:
                selected_engine = "typst"
                main_file = candidates_typ[0]
            elif candidates_tex:
                selected_engine = "latex"
                main_file = candidates_tex[0]
            elif candidates_md:
                selected_engine = "markdown"
                main_file = candidates_md[0]
            else:
                return {
                    "success": False,
                    "engine": "none",
                    "error": "Nenhum arquivo fonte acadêmico (.tex, .typ, .md) encontrado no diretório.",
                    "suggestions": ["Crie um arquivo main.tex, main.typ ou main.md no projeto."]
                }
    else:
        if path.is_file():
            main_file = path
        else:
            ext_map = {"latex": "*.tex", "markdown": "*.md", "typst": "*.typ"}
            glob_pat = ext_map.get(selected_engine, "*.*")
            files = list(target_dir.glob(glob_pat))
            if files:
                main_file = files[0]
            else:
                return {
                    "success": False,
                    "engine": selected_engine,
                    "error": f"Nenhum arquivo para o engine '{selected_engine}' encontrado em {target_dir}.",
                }

    # Executa a compilação conforme o engine
    if selected_engine == "latex":
        return _compile_latex(main_file, target_dir)
    elif selected_engine == "typst":
        return _compile_typst(main_file, target_dir)
    elif selected_engine in {"markdown", "pandoc"}:
        return _compile_markdown(main_file, target_dir)
    else:
        return {
            "success": False,
            "engine": selected_engine,
            "error": f"Engine desconhecido: '{selected_engine}'. Use 'latex', 'typst', 'markdown' ou 'auto'."
        }


def _compile_latex(main_file: Path, work_dir: Path) -> dict[str, Any]:
    """Compilação LaTeX com ciclo completo (multi-pass para referências) ou latexmk."""
    # 1. Pré-checagem de sintaxe no arquivo principal
    try:
        content = main_file.read_text(encoding="utf-8", errors="replace")
        lint_issues = lint_latex_source(content)
    except Exception:
        lint_issues = []

    # 2. Verifica executáveis no ambiente
    has_latexmk = shutil.which("latexmk") is not None
    has_pdflatex = shutil.which("pdflatex") is not None
    has_bibtex = shutil.which("bibtex") is not None

    if not (has_latexmk or has_pdflatex):
        return {
            "success": False,
            "engine": "latex",
            "file": main_file.name,
            "error": "Compilador LaTeX não encontrado no sistema operacional (nem 'latexmk' nem 'pdflatex').",
            "precheck_lint_issues": lint_issues,
            "install_guide": (
                "Para compilar documentos LaTeX/abnTeX2, instale uma distribuição TeX:\n"
                "- Windows: MiKTeX (https://miktex.org) ou TeX Live (https://tug.org/texlive/)\n"
                "- Linux: sudo apt install texlive-full\n"
                "- macOS: brew install --cask mactex"
            )
        }

    job_name = main_file.stem
    output_pdf = work_dir / f"{job_name}.pdf"
    log_file = work_dir / f"{job_name}.log"

    try:
        if has_latexmk:
            # Compilação inteligente multi-pass via latexmk
            cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", main_file.name]
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
        else:
            # Ciclo multi-pass clássico para resolver todas as citações e sumários
            # pdflatex -> bibtex -> pdflatex -> pdflatex
            cmd_pdf = ["pdflatex", "-interaction=nonstopmode", main_file.name]
            subprocess.run(cmd_pdf, cwd=str(work_dir), capture_output=True, timeout=60)
            if has_bibtex:
                subprocess.run(["bibtex", job_name], cwd=str(work_dir), capture_output=True, timeout=30)
            subprocess.run(cmd_pdf, cwd=str(work_dir), capture_output=True, timeout=60)
            result = subprocess.run(cmd_pdf, cwd=str(work_dir), capture_output=True, text=True, timeout=60)

        # Diagnóstico a partir do log
        parsed_errors: list[dict[str, Any]] = []
        if log_file.exists():
            log_text = log_file.read_text(encoding="utf-8", errors="replace")
            parsed_errors = parse_latex_log_for_errors(log_text)

        success = output_pdf.exists() and len([e for e in parsed_errors if e.get("line") is not None]) == 0

        return {
            "success": output_pdf.exists(),
            "engine": "latex (abnTeX2)",
            "file": main_file.name,
            "pdf_generated": str(output_pdf) if output_pdf.exists() else None,
            "log_file": str(log_file) if log_file.exists() else None,
            "errors": parsed_errors[:10],
            "precheck_lint_issues": lint_issues,
            "message": "PDF compilado com sucesso!" if output_pdf.exists() else "Falha na geração do PDF."
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "engine": "latex",
            "file": main_file.name,
            "error": "A compilação excedeu o limite de tempo (timeout). Verifique se há loops ou comandos travados.",
        }
    except Exception as exc:
        return {
            "success": False,
            "engine": "latex",
            "file": main_file.name,
            "error": f"Erro inesperado durante a compilação: {exc}",
        }


def _compile_typst(main_file: Path, work_dir: Path) -> dict[str, Any]:
    """Compilação nativa ultra-rápida via Typst."""
    has_typst = shutil.which("typst") is not None

    if not has_typst:
        return {
            "success": False,
            "engine": "typst",
            "file": main_file.name,
            "error": "Executável 'typst' não encontrado no sistema operacional.",
            "install_guide": (
                "Para compilar com Typst:\n"
                "- Windows: winget install --id Typst.Typst ou cargo install --locked typst-cli\n"
                "- macOS: brew install typst\n"
                "- Linux: cargo install --locked typst-cli"
            )
        }

    output_pdf = work_dir / f"{main_file.stem}.pdf"
    cmd = ["typst", "compile", str(main_file), str(output_pdf)]

    try:
        res = subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True, timeout=45)
        success = res.returncode == 0 and output_pdf.exists()
        return {
            "success": success,
            "engine": "typst",
            "file": main_file.name,
            "pdf_generated": str(output_pdf) if success else None,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "message": "PDF compilado com Typst com sucesso!" if success else f"Erro ao compilar Typst: {res.stderr}"
        }
    except Exception as exc:
        return {
            "success": False,
            "engine": "typst",
            "file": main_file.name,
            "error": str(exc),
        }


def _compile_markdown(main_file: Path, work_dir: Path) -> dict[str, Any]:
    """Compilação Markdown via Pandoc com --citeproc."""
    has_pandoc = shutil.which("pandoc") is not None

    if not has_pandoc:
        return {
            "success": False,
            "engine": "pandoc/markdown",
            "file": main_file.name,
            "error": "Executável 'pandoc' não encontrado no sistema operacional.",
            "install_guide": (
                "Para compilar Markdown para PDF via Pandoc:\n"
                "- Windows: winget install JohnMacFarlane.Pandoc\n"
                "- macOS: brew install pandoc\n"
                "- Linux: sudo apt install pandoc"
            )
        }

    output_pdf = work_dir / f"{main_file.stem}.pdf"
    
    # Procura arquivo .bib no diretório para citar automaticamente
    bib_files = list(work_dir.glob("*.bib"))
    cmd = ["pandoc", str(main_file), "-o", str(output_pdf), "--citeproc", "--pdf-engine=xelatex"]
    if bib_files:
        cmd.extend(["--bibliography", str(bib_files[0])])

    try:
        res = subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True, timeout=90)
        success = res.returncode == 0 and output_pdf.exists()
        return {
            "success": success,
            "engine": "pandoc/markdown",
            "file": main_file.name,
            "pdf_generated": str(output_pdf) if success else None,
            "stderr": res.stderr,
            "message": "PDF compilado com Pandoc com sucesso!" if success else f"Erro ao compilar Pandoc: {res.stderr}"
        }
    except Exception as exc:
        return {
            "success": False,
            "engine": "pandoc/markdown",
            "file": main_file.name,
            "error": str(exc),
        }
