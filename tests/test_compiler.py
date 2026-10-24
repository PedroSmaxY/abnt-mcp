"""Testes para o Pilar 3: Testar & Compilar."""

from pathlib import Path
from abnt_mcp.pillars.compiler import (
    lint_latex_source,
    parse_latex_log_for_errors,
    compile_project,
)


def test_lint_latex_unclosed_begin():
    content = r"""
    \begin{document}
    \begin{itemize}
    \item Item 1
    \end{document}
    """
    issues = lint_latex_source(content)
    types = [i["type"] for i in issues]
    assert "mismatched_env" in types or "unclosed_begin" in types


def test_lint_latex_unescaped_underscore():
    content = r"""
    \begin{document}
    Aqui temos uma variavel_nome desprotegida no texto.
    \end{document}
    """
    issues = lint_latex_source(content)
    types = [i["type"] for i in issues]
    assert "unescaped_underscore" in types


def test_parse_latex_log():
    log_content = r"""
    This is pdfTeX, Version 3.141592653
    (./main.tex
    ! Undefined control sequence.
    l.42 \comandoerrado
    )
    LaTeX Warning: Citation `artigo_fantasma' on page 1 undefined on input line 50.
    """
    errors = parse_latex_log_for_errors(log_content)
    assert len(errors) == 2
    assert any("Undefined control sequence" in e["message"] for e in errors)
    assert any(e["line"] == 42 for e in errors)
    assert any("artigo_fantasma" in e["message"] for e in errors)


def test_compile_project_auto_fallback(tmp_path: Path):
    doc = tmp_path / "main.tex"
    doc.write_text(r"\documentclass{article}\begin{document}Olá\end{document}", encoding="utf-8")
    
    # Executa compilação (se latexmk/pdflatex não estiver instalado, deve retornar relatório amigável com guia de instalação)
    res = compile_project(tmp_path, engine="auto")
    assert "engine" in res
    assert "file" in res or "error" in res
    if not res.get("success"):
        # Deve ter mensagem explicativa
        assert "install_guide" in res or "error" in res
