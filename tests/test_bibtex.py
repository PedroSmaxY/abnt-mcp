import tempfile
from pathlib import Path
from abnt_mcp.tools.bibtex import append_to_bib, parse_bib_keys, clean_bibtex_file


def test_bibtex_append_and_parse():
    with tempfile.NamedTemporaryFile(suffix=".bib", delete=False, mode="w", encoding="utf-8") as f:
        f.write("@article{silva2020, title={Teste}, year={2020}}\n")
        bib_file = f.name

    try:
        keys = parse_bib_keys(bib_file)
        assert "silva2020" in keys

        append_to_bib(bib_file, "@book{knuth1984, title={TeXbook}, year={1984}}")
        new_keys = parse_bib_keys(bib_file)
        assert "knuth1984" in new_keys
    finally:
        Path(bib_file).unlink(missing_ok=True)


def test_clean_bibtex_utf8_accents():
    raw_bib = """@article{SILVA2024,
  author = {SILVA, JOÃO and SANTOS, MARIA},
  title = {Inteligência Artificial Aplicada à Educação Brasileira},
  journal = {Revista Brasileira de Informática},
  year = {2024}
}"""
    with tempfile.NamedTemporaryFile(suffix=".bib", delete=False, mode="w", encoding="utf-8") as f:
        f.write(raw_bib)
        bib_file = f.name

    try:
        res = clean_bibtex_file(bib_file)
        assert res["status"] == "success"
        content = Path(bib_file).read_text(encoding="utf-8")
        # Verifica que o título preservou os acentos em UTF-8
        assert "Inteligência Artificial Aplicada à Educação Brasileira" in content
        # Verifica que os autores foram convertidos preservando 'and'
        assert "Silva, João and Santos, Maria" in content
    finally:
        Path(bib_file).unlink(missing_ok=True)
