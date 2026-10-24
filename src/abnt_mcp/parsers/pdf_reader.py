"""Leitor e extrator de seções de PDF usando pypdf."""

from __future__ import annotations
from pathlib import Path
from typing import Any
import pypdf


def extract_pdf_section(
    pdf_path: str | Path,
    pages: list[int] | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
) -> dict[str, Any]:
    """
    Extrai texto de um arquivo PDF por páginas selecionadas ou intervalo (1-indexado).
    
    Args:
        pdf_path: Caminho para o arquivo PDF.
        pages: Lista específica de páginas a extrair (ex: [1, 2, 5]). 1-indexado.
        start_page: Página inicial do intervalo (inclusive, 1-indexado).
        end_page: Página final do intervalo (inclusive, 1-indexado).
    
    Returns:
        Dicionário com texto extraído, contagem de palavras e metadados.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {path}")

    try:
        reader = pypdf.PdfReader(str(path))
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o arquivo PDF: {exc}") from exc

    total_pages = len(reader.pages)
    if total_pages == 0:
        return {
            "file": path.name,
            "total_pages": 0,
            "pages_extracted": [],
            "text": "",
            "word_count": 0,
            "character_count": 0,
            "is_scanned": True,
            "warning": "O documento PDF não possui páginas."
        }

    # Determina quais índices de páginas extrair (0-indexado internamente)
    target_indices: list[int] = []

    if pages is not None and len(pages) > 0:
        for p in pages:
            idx = p - 1  # converte 1-indexado para 0-indexado
            if 0 <= idx < total_pages and idx not in target_indices:
                target_indices.append(idx)
        target_indices.sort()
    elif start_page is not None or end_page is not None:
        s = max(0, (start_page - 1) if start_page is not None else 0)
        e = min(total_pages, end_page if end_page is not None else total_pages)
        target_indices = list(range(s, e))
    else:
        # Se nada for especificado, extrai todas as páginas
        target_indices = list(range(total_pages))

    extracted_chunks: list[str] = []
    actual_pages_extracted: list[int] = []

    for idx in target_indices:
        page = reader.pages[idx]
        page_text = page.extract_text() or ""
        extracted_chunks.append(f"--- PÁGINA {idx + 1} ---\n{page_text}")
        actual_pages_extracted.append(idx + 1)

    full_text = "\n\n".join(extracted_chunks).strip()
    words = full_text.split()
    word_count = len(words)
    char_count = len(full_text)

    is_scanned = word_count < 10 and total_pages > 0

    return {
        "file": path.name,
        "total_pages": total_pages,
        "pages_extracted": actual_pages_extracted,
        "text": full_text,
        "word_count": word_count,
        "character_count": char_count,
        "is_scanned": is_scanned,
        "warning": "O PDF parece ser digitalizado/sem camada de texto pesquisável." if is_scanned else None
    }
