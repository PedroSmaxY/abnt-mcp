import tempfile
from pathlib import Path
from abnt_mcp.tools.citations import validate_citations


def test_validate_citations_latex_healthy():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "referencias.bib").write_text("@article{silva2020,\n  author={Silva, J.},\n  title={Titulo},\n  year={2020}\n}", encoding="utf-8")
        (p / "main.tex").write_text("\\documentclass{abntex2}\n\\begin{document}\nConforme \\citeonline{silva2020}.\n\\end{document}", encoding="utf-8")

        res = validate_citations(tmp)
        assert res["status"] == "success"
        assert res["format"] == "latex"
        assert res["is_healthy"] is True
        assert len(res["orphan_citations"]) == 0
        assert len(res["uncited_references"]) == 0


def test_validate_citations_latex_orphan():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "referencias.bib").write_text("@article{silva2020, year={2020}}", encoding="utf-8")
        (p / "main.tex").write_text("\\cite{souza2021}", encoding="utf-8")

        res = validate_citations(tmp)
        assert res["status"] == "success"
        assert res["is_healthy"] is False
        assert "souza2021" in res["orphan_citations"]
        assert "silva2020" in res["uncited_references"]


def test_validate_citations_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "referencias.bib").write_text("@article{turing1950, year={1950}}", encoding="utf-8")
        (p / "capitulo.md").write_text("Segundo [@turing1950], as máquinas pensam.", encoding="utf-8")

        res = validate_citations(tmp)
        assert res["status"] == "success"
        assert res["format"] == "markdown"
        assert res["is_healthy"] is True
        assert len(res["orphan_citations"]) == 0
