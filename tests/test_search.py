from unittest.mock import Mock, patch
from abnt_mcp.tools.search import search_papers


@patch("requests.get")
def test_search_crossref_mock(mock_get):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "items": [
                {
                    "DOI": "10.1000/182",
                    "title": ["Artigo Teste"],
                    "author": [{"given": "Maria", "family": "Silva"}],
                    "issued": {"date-parts": [[2023]]},
                    "abstract": "Resumo do artigo."
                }
            ]
        }
    }
    mock_get.return_value = mock_resp

    res = search_papers("inteligencia artificial", limit=1, source="crossref")
    assert res["status"] == "success"
    assert res["total"] == 1
    assert res["papers"][0]["doi"] == "10.1000/182"
    assert res["papers"][0]["authors"] == "Maria Silva"
    assert res["papers"][0]["year"] == 2023


def test_search_unknown_source():
    res = search_papers("teste", source="inexistente")
    assert res["status"] == "error"
    assert "desconhecida" in res["message"]
