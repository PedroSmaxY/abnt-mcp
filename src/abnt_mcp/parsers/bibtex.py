"""Manipulador e higienizador de arquivos BibTeX segundo a ABNT NBR 6023:2018."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any
import bibtexparser
from abnt_mcp.config import ABNT_MONTHS, RE_MAI_WITH_DOT


# Requisitos mínimos de campos por tipo de entrada BibTeX (NBR 6023)
MANDATORY_FIELDS_BY_TYPE: dict[str, list[str]] = {
    "book": ["title", "year"],  # author ou editor
    "article": ["author", "title", "journal", "year"],
    "incollection": ["author", "title", "booktitle", "year"],
    "inproceedings": ["author", "title", "booktitle", "year"],
    "conference": ["author", "title", "booktitle", "year"],
    "mastersthesis": ["author", "title", "school", "year"],
    "phdthesis": ["author", "title", "school", "year"],
    "misc": ["title", "year"],
    "online": ["title", "url", "year"],
}


def normalize_abnt_month(month_value: str) -> str:
    """Normaliza o valor do mês para o padrão ABNT NBR 6023 (maio sem ponto!)."""
    cleaned = month_value.strip().lower().rstrip(".")
    if cleaned in ABNT_MONTHS:
        return ABNT_MONTHS[cleaned]
    # Se já é 'maio', retorna sem ponto
    if cleaned == "maio" or cleaned == "may":
        return "maio"
    return month_value


def clean_latex_accents(text: str) -> str:
    """Converte comandos de acentuação LaTeX obsoletos para caracteres UTF-8 nativos."""
    replacements = [
        (r"\'a", "á"), (r"\'e", "é"), (r"\'i", "í"), (r"\'o", "ó"), (r"\'u", "ú"),
        (r"\'A", "Á"), (r"\'E", "É"), (r"\'I", "Í"), (r"\'O", "Ó"), (r"\'U", "Ú"),
        (r'\"a', "ä"), (r'\"e', "ë"), (r'\"i', "ï"), (r'\"o', "ö"), (r'\"u', "ü"),
        (r'\"A', "Ä"), (r'\"E', "Ë"), (r'\"I', "Ï"), (r'\"O', "Ö"), (r'\"U', "Ü"),
        (r"\^a", "â"), (r"\^e", "ê"), (r"\^i", "î"), (r"\^o", "ô"), (r"\^u", "û"),
        (r"\^A", "Â"), (r"\^E", "Ê"), (r"\^I", "Î"), (r"\^O", "Ô"), (r"\^U", "Û"),
        (r"\`a", "à"), (r"\`e", "è"), (r"\`i", "ì"), (r"\`o", "ò"), (r"\`u", "ù"),
        (r"\`A", "À"), (r"\~a", "ã"), (r"\~o", "õ"), (r"\~A", "Ã"), (r"\~O", "Õ"),
        (r"\c{c}", "ç"), (r"\c{C}", "Ç"), (r"\~n", "ñ"), (r"\~N", "Ñ"),
        (r"{\\'a}", "á"), (r"{\\'e}", "é"), (r"{\\'i}", "í"), (r"{\\'o}", "ó"), (r"{\\'u}", "ú"),
        (r"{\\~a}", "ã"), (r"{\\~o}", "õ"), (r"{\\c{c}}", "ç"),
    ]
    result = text
    for pattern, char in replacements:
        result = result.replace(pattern, char)
    return result


def extract_bib_keys_and_dois(bib_content: str) -> tuple[set[str], set[str]]:
    """Extrai todas as chaves e DOIs de uma string BibTeX."""
    keys: set[str] = set()
    dois: set[str] = set()

    try:
        library = bibtexparser.parse_string(bib_content)
        for entry in library.entries:
            keys.add(entry.key.strip())
            doi = entry.get("doi")
            if doi:
                # Remove prefixos como https://doi.org/
                clean_doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", str(doi).strip().lower())
                dois.add(clean_doi)
    except Exception:
        # Fallback via regex simples
        for match in re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib_content):
            keys.add(match.group(1).strip())
        for match in re.finditer(r"doi\s*=\s*[\"{]([^\"}]+)[\"}]", bib_content, re.IGNORECASE):
            doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", match.group(1).strip().lower())
            dois.add(doi)

    return keys, dois


def sanitize_bibtex_string(bib_content: str) -> tuple[str, list[str]]:
    """
    Higieniza e valida entradas BibTeX conforme a NBR 6023:2018.
    Retorna a string higienizada e uma lista de avisos/correções feitas.
    """
    warnings: list[str] = []
    
    # 1. Limpa acentos em código LaTeX obsoleto para UTF-8 limpo
    content_utf8 = clean_latex_accents(bib_content)
    
    # 2. Corrige ocorrências de 'mai.' para 'maio'
    if RE_MAI_WITH_DOT.search(content_utf8):
        content_utf8 = RE_MAI_WITH_DOT.sub("maio", content_utf8)
        warnings.append("Corrigido mês 'mai.' para 'maio' (sem ponto) conforme NBR 6023.")

    try:
        library = bibtexparser.parse_string(content_utf8)
    except Exception as exc:
        warnings.append(f"Aviso no parser BibTeX: {exc}. Retornando texto com correções básicas.")
        return content_utf8, warnings

    for entry in library.entries:
        entry_type = entry.entry_type.lower()
        key = entry.key

        # Verifica campos obrigatórios
        reqs = MANDATORY_FIELDS_BY_TYPE.get(entry_type, ["title", "year"])
        for req in reqs:
            if req == "author" and entry_type == "book":
                # Livros podem ter author ou editor
                if "author" not in entry and "editor" not in entry:
                    warnings.append(f"[{key}] Livro sem campo 'author' ou 'editor'.")
            elif req not in entry:
                warnings.append(f"[{key}] Campo obrigatório ausente: '{req}' para tipo @{entry_type}.")

        # Normaliza campo month se existir
        if "month" in entry:
            original_month = str(entry["month"]).strip("{} \"'")
            normalized = normalize_abnt_month(original_month)
            if normalized != original_month:
                entry["month"] = normalized
                warnings.append(f"[{key}] Mês '{original_month}' normalizado para '{normalized}'.")

    cleaned_output = bibtexparser.write_string(library)
    return cleaned_output, warnings


def append_entry_if_absent(bib_file_path: Path, new_bibtex_entry: str) -> dict[str, Any]:
    """
    Insere uma nova entrada BibTeX em um arquivo .bib sem duplicar chaves ou DOIs.
    """
    if not bib_file_path.exists():
        bib_file_path.parent.mkdir(parents=True, exist_ok=True)
        bib_file_path.write_text(new_bibtex_entry.strip() + "\n", encoding="utf-8")
        return {
            "status": "created",
            "message": f"Arquivo criado e entrada inserida com sucesso em '{bib_file_path.name}'.",
            "inserted": True,
        }

    existing_content = bib_file_path.read_text(encoding="utf-8", errors="replace")
    existing_keys, existing_dois = extract_bib_keys_and_dois(existing_content)

    new_keys, new_dois = extract_bib_keys_and_dois(new_bibtex_entry)

    # Verifica duplicidade por DOI
    common_dois = existing_dois.intersection(new_dois)
    if common_dois:
        return {
            "status": "duplicate_doi",
            "message": f"A entrada já existe no arquivo com o DOI '{list(common_dois)[0]}'.",
            "inserted": False,
        }

    # Se a chave coincide, gera chave alternativa unívoca
    final_entry_text = new_bibtex_entry
    for key in new_keys:
        if key in existing_keys:
            # Modifica chave para key_alt
            new_key = f"{key}_new"
            counter = 2
            while new_key in existing_keys:
                new_key = f"{key}_{counter}"
                counter += 1
            final_entry_text = re.sub(
                rf"@(\w+)\s*\{{\s*{re.escape(key)}\s*,",
                rf"@\1{{{new_key},",
                final_entry_text,
                count=1
            )

    # Anexa ao final do arquivo
    with bib_file_path.open("a", encoding="utf-8") as f:
        if not existing_content.endswith("\n\n"):
            f.write("\n\n" if not existing_content.endswith("\n") else "\n")
        f.write(final_entry_text.strip() + "\n")

    return {
        "status": "appended",
        "message": f"Entrada anexada com sucesso em '{bib_file_path.name}'.",
        "inserted": True,
    }
