"""Leitor e extrator de seções de PDF usando pypdf."""

from __future__ import annotations
import re
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


def audit_pdf_pagination(pdf_path: str | Path) -> dict[str, Any]:
    """
    Audita a conformidade estrita da paginação segundo a ABNT NBR 14724:2011 (item 5.3):
    1. Folhas pré-textuais não podem conter números de página visíveis;
    2. A numeração visível deve iniciar na primeira folha textual (Introdução);
    3. A contagem sequencial deve iniciar a partir da folha de rosto (a Capa não é contada);
    4. Cruzamento dos números com o Sumário.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {path}")

    reader = pypdf.PdfReader(str(path))
    issues: list[dict[str, Any]] = []

    first_textual_page_idx: int | None = None
    first_textual_title: str | None = None
    sumario_page_idx: int | None = None
    sumario_entries: dict[str, int] = {}

    # 1. Identifica seções pré-textuais e a primeira textual
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            continue

        # Detecta Sumário
        if sumario_page_idx is None and any(re.search(r"^(sum[aá]rio)\b", l, re.IGNORECASE) for l in lines[:3]):
            sumario_page_idx = idx
            for l in lines:
                m = re.search(r"^(1\s+[A-Za-zÀ-ÿ]+.*?)\s*\.{2,}\s*(\d+)$", l)
                if m:
                    sumario_entries[m.group(1).strip()] = int(m.group(2))

        # Detecta primeira seção textual (Introdução ou Capítulo 1)
        if first_textual_page_idx is None:
            if sumario_page_idx is not None and idx == sumario_page_idx:
                continue
            for l in lines[:5]:
                if re.search(r"^(=+\s*)?(1\s+)?(cap[ií]tulo\s+1\s+)?introdu[cç][aã]o\b", l, re.IGNORECASE):
                    first_textual_page_idx = idx
                    first_textual_title = l
                    break

    # 2. Audita páginas pré-textuais (não podem conter algarismos de numeração no topo)
    if first_textual_page_idx is not None:
        for idx in range(first_textual_page_idx):
            page = reader.pages[idx]
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                continue
            first_line = lines[0]
            if re.match(r"^\d+$", first_line):
                issues.append({
                    "page_in_pdf": idx + 1,
                    "type": "pretextual_number_visible",
                    "severity": "critical",
                    "message": f"Violação da ABNT NBR 14724: número de página visível '{first_line}' detectado no elemento pré-textual (Página {idx + 1} do PDF)."
                })

    # 3. Audita numeração da primeira página textual
    if first_textual_page_idx is not None:
        page = reader.pages[first_textual_page_idx]
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        first_line = lines[0] if lines else ""

        has_number = bool(re.match(r"^\d+$", first_line))
        if not has_number:
            issues.append({
                "page_in_pdf": first_textual_page_idx + 1,
                "type": "textual_number_missing",
                "severity": "critical",
                "message": f"Violação da ABNT NBR 14724: a primeira folha textual ({first_textual_title}) não exibe a numeração arábica no cabeçalho."
            })
        else:
            visible_num = int(first_line)
            # A folha de rosto é 1, portanto a primeira página textual no índice N do PDF (0-indexado)
            # deve ter número N (se houver Capa). Se o número for N + 1, a Capa foi contada indevidamente.
            expected_num_without_capa = first_textual_page_idx
            expected_num_with_capa = first_textual_page_idx + 1

            if visible_num == expected_num_with_capa:
                issues.append({
                    "page_in_pdf": first_textual_page_idx + 1,
                    "type": "capa_counted_in_pagination",
                    "severity": "critical",
                    "message": f"Violação da ABNT NBR 14724: a Capa foi computada na numeração. O número impresso é {visible_num}, mas deve ser {expected_num_without_capa} (a contagem inicia exclusivamente na Folha de Rosto)."
                })

        # 4. Cruzamento com o sumário
        for title, reported_p in sumario_entries.items():
            if "introdu" in title.lower() and has_number:
                if int(first_line) != reported_p:
                    issues.append({
                        "page_in_pdf": first_textual_page_idx + 1,
                        "type": "sumario_mismatch",
                        "severity": "warning",
                        "message": f"Divergência normativa: Sumário indica página {reported_p} para a Introdução, mas a página textual exibe {first_line}."
                    })

    return {
        "is_compliant": len(issues) == 0,
        "first_textual_page_pdf": (first_textual_page_idx + 1) if first_textual_page_idx is not None else None,
        "first_textual_title": first_textual_title,
        "issues": issues,
    }
