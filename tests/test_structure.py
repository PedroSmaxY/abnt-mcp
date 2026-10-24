import tempfile
from pathlib import Path
from abnt_mcp.tools.structure import check_tcc_structure


def test_structure_complete_latex():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        content = """\\documentclass{abntex2}
\\begin{document}
\\imprimircapa
\\imprimirfolhaderosto
\\begin{resumo}
Resumo do trabalho em português com palavras-chave.
\\end{resumo}
\\begin{abstract}
Abstract of the work in English.
\\end{abstract}
\\tableofcontents

\\chapter{Introdução}
Texto introdutório.

\\chapter{Fundamentação Teórica}
Revisão de literatura.

\\chapter{Conclusão}
Considerações finais.

\\bibliography{referencias}
\\end{document}
"""
        (p / "main.tex").write_text(content, encoding="utf-8")

        res = check_tcc_structure(tmp)
        assert res["status"] == "success"
        assert res["is_compliant"] is True
        assert len(res["missing_mandatory_elements"]) == 0


def test_structure_missing_abstract_and_conclusion():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        content = """\\documentclass{abntex2}
\\begin{document}
\\imprimircapa
\\imprimirfolhaderosto
\\begin{resumo} Resumo \\end{resumo}
\\tableofcontents
\\chapter{Introdução} Intro
\\chapter{Metodologia} Metodo
\\bibliography{ref}
\\end{document}
"""
        (p / "main.tex").write_text(content, encoding="utf-8")

        res = check_tcc_structure(tmp)
        assert res["status"] == "success"
        assert res["is_compliant"] is False
        assert any("Abstract" in el for el in res["missing_mandatory_elements"])
        assert any("Conclusão" in el for el in res["missing_mandatory_elements"])
