"""Testes para o Pilar 3: Testar & Compilar."""

from pathlib import Path
from abnt_mcp.pillars.compiler import (
    lint_latex_source,
    parse_latex_log_for_errors,
    parse_typst_error,
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


def test_parse_typst_error_and_suggestions():
    """Valida o diagnóstico detalhado e sugestões acionáveis para erros do Typst."""
    # 1. Erro de supplement ausente
    diag_supp = """
    error: please specify the figure's supplement
      ┌─ main.typ:42:1
      │
    42 │ #figure(kind: "quadro", caption: [Teste])[Conteúdo]
      │  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    """
    res_supp = parse_typst_error(Exception("please specify the figure's supplement"), raw_output=diag_supp)
    assert res_supp["line"] == 42
    assert res_supp["column"] == 1
    assert any("supplement: [Quadro]" in s for s in res_supp["suggestions"])

    # 2. Erro de delimitador não fechado
    diag_delim = """
    error: unclosed delimiter
      ┌─ cap1.typ:15:3
      │
    15 │ #["aro de 18
      │  ^
    """
    res_delim = parse_typst_error(Exception("unclosed delimiter"), raw_output=diag_delim)
    assert res_delim["line"] == 15
    assert res_delim["column"] == 3
    assert any("delimitadores não fechados" in s for s in res_delim["suggestions"])

    # 3. Compilação real com erro gerando diagnóstico estruturado
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir) / "main.typ"
        p.write_text('Linha 1\n#figure(kind: "quadro", caption: [X])[Y]\n', encoding="utf-8")
        comp = compile_project(p, engine="typst")
        assert comp["success"] is False
        assert comp["line"] == 2
        assert "supplement: [Quadro]" in comp["suggestions"][0]
        assert "diagnostic_snippet" in comp
