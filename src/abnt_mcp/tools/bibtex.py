from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional
import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
import requests

from ..utils import read_file_with_fallback, write_file_with_encoding


def get_user_agent() -> str:
    import os
    email = os.getenv("ABNT_MCP_EMAIL", "usuario@academico.br")
    return f"ABNT-MCP/0.1.0 (mailto:{email})"


def get_bibtex_by_doi(doi: str, bib_path: Optional[str] = None) -> dict[str, Any]:
    """Busca os metadados oficiais em BibTeX via DOI e opcionalmente adiciona ao arquivo .bib.
    
    Args:
        doi: O Digital Object Identifier (ex: '10.1016/j.future.2019.05.015')
        bib_path: Caminho opcional do arquivo .bib para inserção direta sem duplicatas
    """
    cleaned_doi = doi.strip()
    if cleaned_doi.startswith("https://doi.org/"):
        cleaned_doi = cleaned_doi.replace("https://doi.org/", "")
    elif cleaned_doi.startswith("http://doi.org/"):
        cleaned_doi = cleaned_doi.replace("http://doi.org/", "")

    url = f"https://doi.org/{cleaned_doi}"
    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "application/x-bibtex; charset=utf-8"
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 404:
            return {"status": "error", "message": f"DOI '{cleaned_doi}' não encontrado na base internacional."}
        response.raise_for_status()

        bibtex = response.text.strip()
        key = extract_bibtex_key(bibtex)

        if bib_path:
            target_path = Path(bib_path)
            if target_path.exists():
                existing_keys = parse_bib_keys(str(target_path))
                if key in existing_keys:
                    return {
                        "status": "duplicate",
                        "message": f"A referência com chave '{key}' já existe em {bib_path}.",
                        "key": key,
                        "bibtex": bibtex
                    }
            append_to_bib(str(target_path), bibtex)
            return {
                "status": "added",
                "message": f"Referência '{key}' inserida com sucesso em {bib_path}.",
                "key": key,
                "bibtex": bibtex
            }

        return {"status": "fetched", "key": key, "bibtex": bibtex}

    except Exception as e:
        return {"status": "error", "message": f"Falha ao obter BibTeX do DOI '{cleaned_doi}': {str(e)}"}


def extract_bibtex_key(bibtex: str) -> str:
    """Extrai a chave de citação de uma entrada BibTeX."""
    match = re.search(r"@\w+\s*\{\s*([^,]+),", bibtex)
    return match.group(1).strip() if match else ""


def parse_bib_keys(bib_path: str) -> set[str]:
    """Retorna todas as chaves de citação presentes em um arquivo .bib."""
    try:
        content = read_file_with_fallback(bib_path)
        keys = set()
        for match in re.finditer(r"@\w+\s*\{\s*([^,]+),", content):
            key = match.group(1).strip()
            if key:
                keys.add(key)
        return keys
    except Exception:
        return set()


def append_to_bib(bib_path: str, bibtex: str) -> None:
    """Acrescenta de forma atômica e limpa uma entrada ao final de um arquivo .bib."""
    target = Path(bib_path)
    if target.exists():
        content = read_file_with_fallback(bib_path)
        if content and not content.endswith("\n"):
            content += "\n\n"
        content += bibtex + "\n"
    else:
        content = bibtex + "\n"
    write_file_with_encoding(bib_path, content, encoding="utf-8")


def clean_bibtex_file(bib_path: str) -> dict[str, Any]:
    """Padroniza e higieniza um arquivo BibTeX para os requisitos da NBR 6023 (ABNT).
    
    Verifica campos mandatórios por tipo de obra e preserva integridade de acentos UTF-8.
    """
    path = Path(bib_path)
    if not path.exists():
        return {"status": "error", "message": f"Arquivo não encontrado: {bib_path}"}

    try:
        content = read_file_with_fallback(bib_path)
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        bib_database = bibtexparser.loads(content, parser=parser)

        cleaned_entries = []
        diagnostics = []

        for entry in bib_database.entries:
            key = entry.get("ID", "")
            # Remove apenas espaços da chave, mantendo case para não quebrar referências no texto
            entry["ID"] = key.replace(" ", "_")

            # Formatação de autores (preserva 'and' como separador)
            if "author" in entry:
                entry["author"] = normalize_authors(entry["author"])

            # Validação NBR 6023
            missing = check_abnt_required_fields(entry)
            if missing:
                diagnostics.append({
                    "key": entry["ID"],
                    "type": entry.get("ENTRYTYPE", "unknown"),
                    "missing_recommended_fields": missing
                })

            cleaned_entries.append(entry)

        cleaned_db = BibDatabase()
        cleaned_db.entries = cleaned_entries
        writer = bibtexparser.bwriter.BibTexWriter()
        writer.indent = "  "
        writer.order_entries_by = ("ID",)
        cleaned_bibtex = writer.write(cleaned_db)

        write_file_with_encoding(bib_path, cleaned_bibtex, encoding="utf-8")

        return {
            "status": "success",
            "total_entries": len(cleaned_entries),
            "diagnostics": diagnostics,
            "message": f"Higienização concluída para {len(cleaned_entries)} referências."
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro ao higienizar BibTeX: {str(e)}"}


def normalize_authors(author_str: str) -> str:
    """Formata nomes de autores preservando a separação por 'and' exigida pelo BibTeX."""
    authors = author_str.split(" and ")
    normalized = []
    for a in authors:
        a_clean = a.strip()
        # Se estiver tudo em maiúsculas (ex: SILVA, JOAO), converte para Title Case mantendo sobrenome
        if a_clean.isupper() and "," in a_clean:
            sobrenome, nome = a_clean.split(",", 1)
            normalized.append(f"{sobrenome.strip().title()}, {nome.strip().title()}")
        else:
            normalized.append(a_clean)
    return " and ".join(normalized)


def check_abnt_required_fields(entry: dict[str, str]) -> list[str]:
    """Retorna lista de campos recomendados pela NBR 6023 ausentes na entrada."""
    entry_type = entry.get("ENTRYTYPE", "").lower()

    requirements = {
        "article": ["author", "title", "journal", "year"],
        "book": ["author", "title", "year", "publisher"],
        "inproceedings": ["author", "title", "booktitle", "year"],
        "phdthesis": ["author", "title", "year", "school"],
        "mastersthesis": ["author", "title", "year", "school"],
        "misc": ["title", "year"],
    }

    reqs = requirements.get(entry_type, ["author", "title", "year"])
    return [field for field in reqs if not entry.get(field)]
