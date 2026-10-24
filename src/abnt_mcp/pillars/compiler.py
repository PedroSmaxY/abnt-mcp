"""Pilar 3: Testar & Compilar.

Compilador multi-engine (Typst nativo embutido em Python, LaTeX abnTeX2, Pandoc/Markdown)
com pré-checagem estrutural, ciclo multi-pass, linter de sintaxe e entrega direta de PDF.
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
    for match in re.finditer(r"LaTeX Warning: Citation [`']([^'`]+)['`] on page \d+ undefined", log_content):
        errors.append({
            "message": f"Citação indefinida: '{match.group(1)}'. Verifique se consta no arquivo .bib.",
            "line": None,
            "context": match.group(0)
        })

    return errors


def convert_markdown_to_typst(md_content: str, title: str = "Trabalho Acadêmico", author: str = "Autor") -> str:
    """Converte conteúdo Markdown para formato Typst estruturado no padrão ABNT NBR 14724."""
    # Remove metadados YAML se existirem
    clean_md = re.sub(r"^---\n.*?\n---\n", "", md_content, flags=re.DOTALL)
    
    # Extrai título ou autor do YAML se presente
    title_match = re.search(r'title:\s*["\']?([^"\']+)["\']?', md_content)
    if title_match:
        title = title_match.group(1).strip()
    author_match = re.search(r'author:\s*["\']?([^"\']+)["\']?', md_content)
    if author_match:
        author = author_match.group(1).strip()

    # Normaliza URLs entre colchetes angulares <http...> para evitar conflito com labels do Typst
    clean_md = re.sub(r"<(https?://[^>]+)>", r" \1 ", clean_md)
    clean_md = re.sub(r"<[^>]+>", "", clean_md)

    # Preâmbulo Typst ABNT com margens 3-3-2-2 (NBR 14724)
    # A numeração visível nasce exclusivamente na primeira folha textual
    typst_doc = f"""#set document(title: "{title}", author: "{author}")
#set page(
  paper: "a4",
  margin: (top: 3cm, left: 3cm, bottom: 2cm, right: 2cm),
  header: none
)
#set text(size: 12pt, lang: "pt", region: "BR")
#set par(justify: true, leading: 1.5em, first-line-indent: 1.25cm)

#show heading.where(level: 1): it => {{
  pagebreak(weak: true)
  v(1cm)
  text(weight: "bold")[#it.body]
  v(1cm)
}}

"""
    pretextual_keywords = {
        "resumo", "abstract", "sumario", "sumário", "capa", "folha de rosto",
        "agradecimentos", "dedicatoria", "dedicatória", "epigrafe", "epígrafe",
        "lista de figuras", "lista de tabelas", "lista de ilustrações",
        "lista de ilustracoes", "lista de abreviaturas", "lista de siglas"
    }

    has_started_textual = False

    # Converte cabeçalhos
    lines = clean_md.splitlines()
    converted_lines = []
    for line in lines:
        # Headers
        h1 = re.match(r"^#\s+(.+)$", line)
        h2 = re.match(r"^##\s+(.+)$", line)
        h3 = re.match(r"^###\s+(.+)$", line)
        h4 = re.match(r"^####\s+(.+)$", line)

        if h1:
            h1_title = h1.group(1).strip()
            title_lower = h1_title.lower()
            title_core = re.sub(r"^[\d\.\s]+", "", title_lower).strip()

            is_pretextual = (
                title_core in pretextual_keywords
                or any(title_lower.startswith(pt) for pt in pretextual_keywords)
            )

            if "folha de rosto" in title_lower:
                converted_lines.append("#counter(page).update(1)")

            if not is_pretextual and not has_started_textual:
                has_started_textual = True
                converted_lines.append(
                    "#set page(header: context { align(right)[#text(size: 10pt)[#counter(page).get().first()]] })"
                )

            converted_lines.append(f"= {h1_title}")
        elif h2:
            converted_lines.append(f"== {h2.group(1).strip()}")
        elif h3:
            converted_lines.append(f"=== {h3.group(1).strip()}")
        elif h4:
            converted_lines.append(f"==== {h4.group(1).strip()}")
        else:
            # Converte citações estilo pandoc [@key] para @key
            l_cite = re.sub(r"\[@([a-zA-Z0-9_\-]+)\]", r"@\1", line)
            # Remove marcadores de HTML de quebra de página
            l_clean = re.sub(r"\\newpage", "#pagebreak()", l_cite)
            converted_lines.append(l_clean)

    typst_doc += "\n".join(converted_lines)
    return typst_doc


def compile_project(project_path: str | Path, engine: str = "auto") -> dict[str, Any]:
    """
    Compila o projeto acadêmico para PDF utilizando o engine apropriado
    (Typst embutido, LaTeX ou Pandoc) com diagnóstico amigável e geração direta do PDF.
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
            if ext == ".typ":
                selected_engine = "typst"
            elif ext == ".tex":
                # Se tem typst embutido mas não tem pdflatex, pode priorizar typst
                selected_engine = "latex" if (shutil.which("latexmk") or shutil.which("pdflatex")) else "latex"
            elif ext in {".md", ".markdown"}:
                # Markdown pode compilar direto via Typst nativo embutido!
                selected_engine = "typst"
        else:
            # Procura arquivos principais comuns no diretório
            candidates_typ = list(target_dir.glob("main.typ")) or list(target_dir.glob("*.typ"))
            candidates_tex = list(target_dir.glob("main.tex")) or list(target_dir.glob("tcc.tex")) or list(target_dir.glob("*.tex"))
            candidates_md = list(target_dir.glob("main.md")) or list(target_dir.glob("tcc.md")) or list(target_dir.glob("*.md"))

            if candidates_typ:
                selected_engine = "typst"
                main_file = candidates_typ[0]
            elif candidates_tex and (shutil.which("latexmk") or shutil.which("pdflatex")):
                selected_engine = "latex"
                main_file = candidates_tex[0]
            elif candidates_md:
                # Markdown compila diretamente para PDF via Typst embutido!
                selected_engine = "typst"
                main_file = candidates_md[0]
            elif candidates_tex:
                selected_engine = "latex"
                main_file = candidates_tex[0]
            else:
                return {
                    "success": False,
                    "engine": "none",
                    "error": "Nenhum arquivo fonte acadêmico (.tex, .typ, .md) encontrado no diretório.",
                    "suggestions": ["Crie um arquivo main.typ, main.md ou main.tex no projeto."]
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
    if selected_engine == "typst":
        return _compile_typst(main_file, target_dir)
    elif selected_engine == "latex":
        return _compile_latex(main_file, target_dir)
    elif selected_engine in {"markdown", "pandoc"}:
        return _compile_markdown(main_file, target_dir)
    else:
        return {
            "success": False,
            "engine": selected_engine,
            "error": f"Engine desconhecido: '{selected_engine}'. Use 'typst', 'latex', 'markdown' ou 'auto'."
        }


def _compile_typst(main_file: Path, work_dir: Path) -> dict[str, Any]:
    """Compilação nativa ultra-rápida via Typst (usando módulo Python typst embutido ou CLI)."""
    output_pdf = work_dir / f"{main_file.stem}.pdf"

    # Se o arquivo de entrada for Markdown, converte para Typst temporariamente para compilar direto
    source_to_compile = main_file
    is_temp_typst = False

    if main_file.suffix.lower() in {".md", ".markdown"}:
        try:
            md_text = main_file.read_text(encoding="utf-8", errors="replace")
            typst_converted = convert_markdown_to_typst(md_text, title=main_file.stem)
            temp_typst_file = work_dir / f"{main_file.stem}_generated.typ"
            temp_typst_file.write_text(typst_converted, encoding="utf-8")
            source_to_compile = temp_typst_file
            is_temp_typst = True
        except Exception:
            pass

    # 1. Tenta compilação DIRETA via biblioteca embutida Python (Zero dependência externa!)
    try:
        import typst
        typst.compile(source_to_compile, output=str(output_pdf))
        if is_temp_typst and source_to_compile.exists():
            source_to_compile.unlink(missing_ok=True)

        if output_pdf.exists():
            return {
                "success": True,
                "engine": "typst (python nativo embutido)",
                "file": main_file.name,
                "pdf_generated": str(output_pdf),
                "size_bytes": output_pdf.stat().st_size,
                "message": f"PDF ABNT compilado e entregue com sucesso: {output_pdf.name}"
            }
    except Exception as py_exc:
        # Se falhou, tenta CLI se disponível
        pass

    # 2. Fallback via CLI executável
    has_typst_cli = shutil.which("typst") is not None
    if has_typst_cli:
        cmd = ["typst", "compile", str(source_to_compile), str(output_pdf)]
        try:
            res = subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True, timeout=45)
            if is_temp_typst and source_to_compile.exists():
                source_to_compile.unlink(missing_ok=True)

            success = res.returncode == 0 and output_pdf.exists()
            return {
                "success": success,
                "engine": "typst (cli)",
                "file": main_file.name,
                "pdf_generated": str(output_pdf) if success else None,
                "size_bytes": output_pdf.stat().st_size if success else 0,
                "message": "PDF compilado com sucesso via Typst CLI!" if success else f"Erro ao compilar Typst: {res.stderr}"
            }
        except Exception as exc:
            pass

    return {
        "success": False,
        "engine": "typst",
        "file": main_file.name,
        "error": "Não foi possível compilar o documento para PDF via Typst.",
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
            cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", main_file.name]
            subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True, timeout=120)
        else:
            cmd_pdf = ["pdflatex", "-interaction=nonstopmode", main_file.name]
            subprocess.run(cmd_pdf, cwd=str(work_dir), capture_output=True, timeout=60)
            if has_bibtex:
                subprocess.run(["bibtex", job_name], cwd=str(work_dir), capture_output=True, timeout=30)
            subprocess.run(cmd_pdf, cwd=str(work_dir), capture_output=True, timeout=60)
            subprocess.run(cmd_pdf, cwd=str(work_dir), capture_output=True, text=True, timeout=60)

        parsed_errors: list[dict[str, Any]] = []
        if log_file.exists():
            log_text = log_file.read_text(encoding="utf-8", errors="replace")
            parsed_errors = parse_latex_log_for_errors(log_text)

        return {
            "success": output_pdf.exists(),
            "engine": "latex (abnTeX2)",
            "file": main_file.name,
            "pdf_generated": str(output_pdf) if output_pdf.exists() else None,
            "size_bytes": output_pdf.stat().st_size if output_pdf.exists() else 0,
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


def _compile_markdown(main_file: Path, work_dir: Path) -> dict[str, Any]:
    """Compilação Markdown via Pandoc com --citeproc ou fallback para Typst nativo."""
    has_pandoc = shutil.which("pandoc") is not None

    if has_pandoc:
        output_pdf = work_dir / f"{main_file.stem}.pdf"
        bib_files = list(work_dir.glob("*.bib"))
        cmd = ["pandoc", str(main_file), "-o", str(output_pdf), "--citeproc", "--pdf-engine=xelatex"]
        if bib_files:
            cmd.extend(["--bibliography", str(bib_files[0])])

        try:
            res = subprocess.run(cmd, cwd=str(work_dir), capture_output=True, text=True, timeout=90)
            if res.returncode == 0 and output_pdf.exists():
                return {
                    "success": True,
                    "engine": "pandoc/markdown",
                    "file": main_file.name,
                    "pdf_generated": str(output_pdf),
                    "size_bytes": output_pdf.stat().st_size,
                    "message": "PDF compilado com Pandoc com sucesso!"
                }
        except Exception:
            pass

    # Fallback automático: compila via Typst embutido direto para PDF!
    return _compile_typst(main_file, work_dir)
