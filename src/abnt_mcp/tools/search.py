from __future__ import annotations

import os
from typing import Any
import requests


def get_user_agent() -> str:
    """Retorna User-Agent acadêmico para evitar bloqueios de taxa em APIs públicas."""
    email = os.getenv("ABNT_MCP_EMAIL", "usuario@academico.br")
    return f"ABNT-MCP/0.1.0 (https://github.com/josemurilors/ABNT-MCP; mailto:{email})"


def search_papers(query: str, limit: int = 10, source: str = "crossref") -> dict[str, Any]:
    """Busca artigos científicos via Crossref, Semantic Scholar ou SciELO.
    
    Args:
        query: Tema ou termo de busca (ex: 'inteligência artificial na educação')
        limit: Quantidade máxima de resultados (padrão 10)
        source: Base de dados ('crossref', 'semantic_scholar', 'scielo')
    """
    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "application/json"
    }

    try:
        source_lower = source.lower()
        if source_lower == "crossref":
            return _search_crossref(query, limit, headers)
        elif source_lower in ("semantic_scholar", "s2"):
            return _search_semantic_scholar(query, limit, headers)
        elif source_lower == "scielo":
            return _search_scielo(query, limit, headers)
        else:
            return {
                "status": "error",
                "message": f"Fonte '{source}' desconhecida. Use 'crossref', 'semantic_scholar' ou 'scielo'."
            }
    except Exception as e:
        return {"status": "error", "message": f"Erro ao consultar {source}: {str(e)}"}


def _search_crossref(query: str, limit: int, headers: dict) -> dict[str, Any]:
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": limit,
        "select": "DOI,title,author,issued,abstract,container-title"
    }

    response = requests.get(url, params=params, headers=headers, timeout=12)
    response.raise_for_status()

    data = response.json()
    papers = []

    for item in data.get("message", {}).get("items", []):
        container = item.get("container-title", [])
        journal = container[0] if container else ""
        papers.append({
            "doi": item.get("DOI", ""),
            "title": item.get("title", [""])[0] if item.get("title") else "",
            "authors": _format_crossref_authors(item.get("author", [])),
            "journal": journal,
            "year": _extract_year(item.get("issued", {})),
            "abstract": item.get("abstract", "")
        })

    return {"status": "success", "source": "crossref", "total": len(papers), "papers": papers}


def _search_semantic_scholar(query: str, limit: int, headers: dict) -> dict[str, Any]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,year,abstract,externalIds,venue"
    }
    
    # Se houver chave configurada, usa para evitar rate limit
    s2_key = os.getenv("S2_API_KEY")
    if s2_key:
        headers["x-api-key"] = s2_key

    response = requests.get(url, params=params, headers=headers, timeout=12)
    response.raise_for_status()

    data = response.json()
    papers = []

    for item in data.get("data", []):
        authors = ", ".join([a.get("name", "") for a in item.get("authors", [])])
        papers.append({
            "doi": item.get("externalIds", {}).get("DOI", ""),
            "title": item.get("title", ""),
            "authors": authors,
            "journal": item.get("venue", ""),
            "year": item.get("year", 0),
            "abstract": item.get("abstract", "")
        })

    return {"status": "success", "source": "semantic_scholar", "total": len(papers), "papers": papers}


def _search_scielo(query: str, limit: int, headers: dict) -> dict[str, Any]:
    """Consulta artigos brasileiros e latino-americanos indexados via Crossref com filtro de SciELO."""
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "filter": "publisher-name:SciELO",
        "rows": limit,
        "select": "DOI,title,author,issued,abstract,container-title"
    }

    response = requests.get(url, params=params, headers=headers, timeout=12)
    response.raise_for_status()

    data = response.json()
    papers = []

    for item in data.get("message", {}).get("items", []):
        container = item.get("container-title", [])
        journal = container[0] if container else ""
        papers.append({
            "doi": item.get("DOI", ""),
            "title": item.get("title", [""])[0] if item.get("title") else "",
            "authors": _format_crossref_authors(item.get("author", [])),
            "journal": journal,
            "year": _extract_year(item.get("issued", {})),
            "abstract": item.get("abstract", "")
        })

    return {"status": "success", "source": "scielo", "total": len(papers), "papers": papers}


def _format_crossref_authors(authors: list) -> str:
    names = []
    for author in authors:
        given = author.get("given", "")
        family = author.get("family", "")
        names.append(f"{given} {family}".strip())
    return ", ".join(names)


def _extract_year(issued: dict) -> int:
    date_parts = issued.get("date-parts", [[]])
    if date_parts and date_parts[0]:
        return date_parts[0][0]
    return 0
