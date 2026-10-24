"""Testes para o Pilar 4: Dicas, Mentoria & Banca Examinadora."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from abnt_mcp.pillars.advisory import (
    search_academic_literature,
    fetch_bibtex_by_doi_service,
    clean_bibtex_file_service,
    simulate_banca_examination,
)


@patch("requests.get")
def test_search_academic_literature_mocked(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "items": [
                {
                    "title": ["Machine Learning in Software Engineering"],
                    "author": [{"family": "Silva", "given": "Carlos"}],
                    "published": {"date-parts": [[2023, 5]]},
                    "container-title": ["Journal of Systems"],
                    "DOI": "10.1000/182",
                    "URL": "https://doi.org/10.1000/182",
                    "abstract": "<jats:p>This study presents...</jats:p>"
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    results = search_academic_literature("machine learning", source="crossref", limit=1)
    assert len(results) == 1
    assert results[0]["title"] == "Machine Learning in Software Engineering"
    assert results[0]["doi"] == "10.1000/182"
    assert "This study presents..." in results[0]["abstract"]


@patch("requests.get")
def test_fetch_bibtex_by_doi_service_mocked(mock_get, tmp_path: Path):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"@article{test2024, title={Sample}, year={2024}}"
    mock_get.return_value = mock_response

    bib_file = tmp_path / "refs.bib"
    res = fetch_bibtex_by_doi_service("10.1234/test", bib_file=str(bib_file))
    assert res["success"] is True
    assert res["saved_to_file"] == str(bib_file)
    assert bib_file.exists()
    assert "test2024" in bib_file.read_text(encoding="utf-8")


def test_clean_bibtex_file_service(tmp_path: Path, sample_bib_content):
    in_file = tmp_path / "raw.bib"
    out_file = tmp_path / "cleaned.bib"
    in_file.write_text(sample_bib_content, encoding="utf-8")

    res = clean_bibtex_file_service(str(in_file), str(out_file))
    assert res["success"] is True
    assert out_file.exists()
    cleaned_txt = out_file.read_text(encoding="utf-8")
    assert "maio" in cleaned_txt.lower()


def test_simulate_banca_examination(tmp_path: Path, sample_tex_content):
    doc = tmp_path / "main.tex"
    doc.write_text(sample_tex_content, encoding="utf-8")

    res = simulate_banca_examination(str(tmp_path))
    assert "veredito" in res
    assert "nota_global" in res
    assert "pontuacao_por_eixo" in res
    assert len(res["perguntas_da_banca"]) >= 3
    assert len(res["principais_recomendacoes"]) > 0
