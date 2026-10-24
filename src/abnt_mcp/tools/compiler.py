from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional


def compile_tcc(project_path: str, engine: str = "auto") -> dict[str, Any]:
    """Compila o trabalho acadêmico (LaTeX, Markdown com Pandoc ou Typst) gerando o PDF final.
    
    Implementa compilação multi-pass para LaTeX para garantir que todas as citações
    e referências bibliográficas do abnTeX2 sejam processadas corretamente.
    """
    project = Path(project_path)
    if not project.exists():
        return {"status": "error", "message": f"Diretório não encontrado: {project_path}"}

    if engine == "auto":
        detected_engine = detect_engine(project)
        if not detected_engine:
            return {
                "status": "error",
                "message": (
                    "Não foi possível detectar automaticamente o compilador. "
                    "Verifique se o projeto possui um arquivo principal (main.tex, main.md ou main.typ) "
                    "e se você tem TeX Live / MiKTeX, Pandoc ou Typst instalados."
                )
            }
        engine = detected_engine

    availability = check_compiler_availability(engine)
    if not availability["available"]:
        return {"status": "error", "message": availability["message"]}

    try:
        if engine in ("latexmk", "pdflatex"):
            return _compile_latex(project, engine)
        elif engine == "pandoc":
            return _compile_pandoc(project)
        elif engine == "typst":
            return _compile_typst(project)
        else:
            return {"status": "error", "message": f"Engine '{engine}' não suportada."}
    except Exception as e:
        return {"status": "error", "message": f"Erro durante compilação: {str(e)}"}


def detect_engine(project: Path) -> Optional[str]:
    """Detecta a ferramenta de compilação ideal a partir dos arquivos presentes."""
    if (project / "main.tex").exists() or any(project.glob("*.tex")):
        if shutil.which("latexmk"):
            return "latexmk"
        if shutil.which("pdflatex"):
            return "pdflatex"

    if (project / "main.md").exists() or any(project.glob("*.md")):
        if shutil.which("pandoc"):
            return "pandoc"

    if (project / "main.typ").exists() or any(project.glob("*.typ")):
        if shutil.which("typst"):
            return "typst"

    return None


def check_compiler_availability(engine: str) -> dict[str, Any]:
    binary_map = {
        "latexmk": "latexmk",
        "pdflatex": "pdflatex",
        "pandoc": "pandoc",
        "typst": "typst"
    }
    binary = binary_map.get(engine, engine)
    if not shutil.which(binary):
        return {
            "available": False,
            "message": f"Compilador '{binary}' não foi encontrado no PATH do sistema. Instale TeX Live, MiKTeX, Pandoc ou Typst."
        }
    return {"available": True, "binary": binary}


def _compile_latex(project: Path, engine: str) -> dict[str, Any]:
    """Executa a compilação LaTeX em múltiplos passos."""
    main_tex = find_main_tex(project)
    if not main_tex:
        return {"status": "error", "message": "Nenhum arquivo .tex principal encontrado."}

    stem = main_tex.stem
    output_pdf = main_tex.with_suffix(".pdf")

    try:
        if engine == "latexmk":
            cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-file-line-error", main_tex.name]
            result = subprocess.run(cmd, cwd=str(project), capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and output_pdf.exists():
                return {
                    "status": "success",
                    "engine": "latexmk",
                    "pdf_path": str(output_pdf),
                    "message": "Compilação concluída com sucesso via latexmk."
                }
            return {
                "status": "error",
                "engine": "latexmk",
                "message": "Falha na compilação do LaTeX.",
                "errors": extract_latex_errors(result.stdout + "\n" + result.stderr)
            }
        else:
            # Multi-pass manual: pdflatex -> bibtex -> pdflatex -> pdflatex
            subprocess.run(["pdflatex", "-interaction=nonstopmode", main_tex.name], cwd=str(project), capture_output=True, text=True, timeout=60)
            if shutil.which("bibtex"):
                subprocess.run(["bibtex", stem], cwd=str(project), capture_output=True, text=True, timeout=30)
            subprocess.run(["pdflatex", "-interaction=nonstopmode", main_tex.name], cwd=str(project), capture_output=True, text=True, timeout=60)
            last = subprocess.run(["pdflatex", "-interaction=nonstopmode", main_tex.name], cwd=str(project), capture_output=True, text=True, timeout=60)

            if output_pdf.exists():
                return {
                    "status": "success",
                    "engine": "pdflatex (multi-pass)",
                    "pdf_path": str(output_pdf),
                    "message": "Documento e referências compilados com sucesso."
                }
            return {
                "status": "error",
                "engine": "pdflatex",
                "message": "Falha na geração do PDF.",
                "errors": extract_latex_errors(last.stdout + "\n" + last.stderr)
            }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Tempo limite de compilação excedido (timeout)."}


def _compile_pandoc(project: Path) -> dict[str, Any]:
    """Compila Markdown para PDF com Pandoc e processador de citações."""
    main_md = project / "main.md"
    if not main_md.exists():
        mds = [f for f in project.glob("*.md") if "readme" not in f.name.lower()]
        if not mds:
            return {"status": "error", "message": "Nenhum arquivo .md principal encontrado."}
        main_md = mds[0]

    output_pdf = project / "documento.pdf"
    cmd = ["pandoc", str(main_md.name), "-o", str(output_pdf.name)]

    bib_file = next(project.glob("*.bib"), None)
    if bib_file:
        cmd.extend(["--citeproc", f"--bibliography={bib_file.name}"])

    result = subprocess.run(cmd, cwd=str(project), capture_output=True, text=True, timeout=90)
    if result.returncode == 0 and output_pdf.exists():
        return {
            "status": "success",
            "engine": "pandoc",
            "pdf_path": str(output_pdf),
            "message": "PDF gerado com sucesso via Pandoc."
        }
    return {
        "status": "error",
        "engine": "pandoc",
        "message": "Falha na compilação Pandoc.",
        "details": result.stderr
    }


def _compile_typst(project: Path) -> dict[str, Any]:
    """Compila documentos Typst (.typ) nativamente."""
    main_typ = project / "main.typ"
    if not main_typ.exists():
        typs = list(project.glob("*.typ"))
        if not typs:
            return {"status": "error", "message": "Nenhum arquivo .typ principal encontrado."}
        main_typ = typs[0]

    output_pdf = project / "documento.pdf"
    cmd = ["typst", "compile", str(main_typ.name), str(output_pdf.name)]

    result = subprocess.run(cmd, cwd=str(project), capture_output=True, text=True, timeout=40)
    if result.returncode == 0 and output_pdf.exists():
        return {
            "status": "success",
            "engine": "typst",
            "pdf_path": str(output_pdf),
            "message": "PDF gerado instantaneamente via Typst."
        }
    return {
        "status": "error",
        "engine": "typst",
        "message": "Falha na compilação Typst.",
        "details": result.stderr
    }


def find_main_tex(project: Path) -> Optional[Path]:
    for name in ["main.tex", "tcc.tex", "dissertacao.tex", "tese.tex", "artigo.tex"]:
        target = project / name
        if target.exists():
            return target
    texs = list(project.glob("*.tex"))
    return texs[0] if texs else None


def extract_latex_errors(log: str) -> list[str]:
    errors = []
    for line in log.splitlines():
        if line.startswith("!") or "Fatal error" in line or "Error:" in line:
            errors.append(line.strip())
    return errors[:10]
