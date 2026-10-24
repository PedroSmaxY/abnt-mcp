"""Leitor e extrator de seções de PDF usando pypdf."""

from __future__ import annotations
import re
import struct
import zlib
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


def _encode_rgb_png_bytes(width: int, height: int, rgb_bytes: bytes) -> bytes:
    """Codifica bytes RGB puros em um arquivo PNG válido usando apenas a biblioteca padrão."""
    w = max(1, min(width, 512))
    h = max(1, min(height, 512))
    expected_len = w * h * 3
    if len(rgb_bytes) < expected_len:
        rgb_bytes = (rgb_bytes + b"\x1a\x3b\x5c" * (w * h))[:expected_len]
    else:
        rgb_bytes = rgb_bytes[:expected_len]

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    raw_scanlines = bytearray()
    stride = w * 3
    for y in range(h):
        raw_scanlines.append(0)
        raw_scanlines.extend(rgb_bytes[y * stride : (y + 1) * stride])

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw_scanlines))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )


def _extract_cover_logo_from_page(
    page: Any,
    output_assets_dir: Path | None = None,
) -> tuple[bool, str | None]:
    """
    Detecta e extrai a primeira imagem (brasão/logo institucional) da Capa (Página 1).
    Funciona com `page.images` ou inspecionando diretamente `/Resources -> /XObject`
    sem depender de bibliotecas externas como Pillow.
    """
    try:
        resources = page.get("/Resources") or {}
        if hasattr(resources, "get_object"):
            resources = resources.get_object()
        xobjects = resources.get("/XObject") or {}
        if hasattr(xobjects, "get_object"):
            xobjects = xobjects.get_object()
    except Exception:
        xobjects = {}

    for _, obj_ref in xobjects.items():
        try:
            obj = obj_ref.get_object() if hasattr(obj_ref, "get_object") else obj_ref
            subtype = str(obj.get("/Subtype", ""))
            if subtype != "/Image":
                continue

            if output_assets_dir is None:
                return True, None

            output_assets_dir.mkdir(parents=True, exist_ok=True)
            raw_data = obj.get_data()
            img_filter = str(obj.get("/Filter", ""))

            if raw_data.startswith(b"\x89PNG"):
                target_file = output_assets_dir / "logo_instituicao.png"
                target_file.write_bytes(raw_data)
                return True, f"figuras/{target_file.name}"
            if raw_data.startswith(b"\xff\xd8") or "/DCTDecode" in img_filter:
                target_file = output_assets_dir / "logo_instituicao.jpg"
                target_file.write_bytes(raw_data)
                return True, f"figuras/{target_file.name}"

            width = int(obj.get("/Width", 64) or 64)
            height = int(obj.get("/Height", 64) or 64)
            png_bytes = _encode_rgb_png_bytes(width, height, raw_data)
            target_file = output_assets_dir / "logo_instituicao.png"
            target_file.write_bytes(png_bytes)
            return True, f"figuras/{target_file.name}"
        except Exception:
            continue

    return False, None


def extract_institutional_pattern_from_pdf(
    pdf_path: str | Path,
    output_assets_dir: str | Path | None = None,
) -> dict[str, Any]:
    """
    Inspeciona um PDF acadêmico modelo da instituição (ex: TCC ou dissertação aprovada)
    para aprender o padrão institucional da universidade:
    1. Linhas de cabeçalho da Capa (instituição, faculdade/centro, curso);
    2. Presença e extração automática de brasão/logo na Capa (Página 1);
    3. Preâmbulo institucional e orientador na Folha de Rosto (Página 2);
    4. Elementos pré-textuais presentes (ficha catalográfica, folha de aprovação, etc.);
    5. Nomenclatura da seção conclusiva ('Conclusão' vs 'Considerações Finais').
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo PDF modelo não encontrado: {path}")

    reader = pypdf.PdfReader(str(path))
    if len(reader.pages) == 0:
        raise ValueError(f"O PDF modelo '{path.name}' não contém páginas.")

    assets_dir = Path(output_assets_dir) if output_assets_dir else None

    # 1. Capa (Página 1)
    cover_page = reader.pages[0]
    has_cover_logo, cover_logo_path = _extract_cover_logo_from_page(cover_page, assets_dir)

    cover_text = cover_page.extract_text() or ""
    cover_lines = [ln.strip() for ln in cover_text.splitlines() if ln.strip()]

    cover_header_lines: list[str] = []
    institution: str | None = None
    department: str | None = None
    course: str | None = None

    inst_keywords = (
        "universidade", "instituto", "faculdade", "centro universit", "centro de",
        "escola", "departamento", "programa de p", "curso de", "bacharelado", "licenciatura",
    )
    for ln in cover_lines[:6]:
        ln_lower = ln.lower()
        if any(k in ln_lower for k in inst_keywords) or (ln.isupper() and len(ln.split()) >= 2):
            cover_header_lines.append(ln)
            if institution is None and any(
                k in ln_lower for k in ("universidade", "instituto", "faculdade", "centro universit")
            ):
                institution = ln
            elif department is None and any(
                k in ln_lower for k in ("centro", "departamento", "instituto", "faculdade", "escola")
            ):
                department = ln
            elif course is None and any(
                k in ln_lower for k in ("curso", "programa", "bacharelado", "licenciatura", "engenharia", "ciência", "direito", "administração", "sistemas")
            ):
                course = ln

    if not institution and cover_header_lines:
        institution = cover_header_lines[0]

    # 2. Folha de Rosto (Página 2, se existir)
    preamble_text: str | None = None
    advisor: str | None = None
    if len(reader.pages) >= 2:
        rosto_text = reader.pages[1].extract_text() or ""
        rosto_lines = [ln.strip() for ln in rosto_text.splitlines() if ln.strip()]

        # Busca Orientador(a)
        for ln in rosto_lines:
            m_adv = re.search(r"orientador(?:\(a\)|a)?\s*:\s*(.+)", ln, re.IGNORECASE)
            if m_adv:
                advisor = m_adv.group(1).strip()
                break

        # Busca bloco de preâmbulo (natureza do trabalho)
        preamble_triggers = (
            "trabalho de conclus", "monografia apresentada", "disserta",
            "tese apresentada", "requisito parcial", "obten",
        )
        preamble_candidates: list[str] = []
        capturing = False
        for ln in rosto_lines:
            ln_low = ln.lower()
            if any(t in ln_low for t in preamble_triggers):
                capturing = True
            if capturing:
                if re.search(r"^orientador|^coorientador|^\d{4}$", ln_low):
                    break
                preamble_candidates.append(ln)
        if preamble_candidates:
            preamble_text = " ".join(preamble_candidates)

    # 3. Elementos pré-textuais e rótulo de conclusão
    pre_textual_Catalog = {
        "ficha catalografica": r"ficha\s+catalogr.{1,2}fica|dados\s+internacionais\s+de\s+cataloga",
        "folha de aprovacao": r"folha\s+de\s+aprova.{1,3}o|banca\s+examinadora",
        "dedicatoria": r"\bdedicat.{1,2}ria\b",
        "agradecimentos": r"\bagradecimento[s]?\b",
        "epigrafe": r"\bep.{1,2}grafe\b",
        "lista de ilustracoes": r"lista\s+de\s+(?:ilustra.{1,3}es|figuras)",
        "lista de tabelas": r"lista\s+de\s+tabelas",
        "lista de quadros": r"lista\s+de\s+quadros",
        "lista de abreviaturas": r"lista\s+de\s+(?:abreviaturas|siglas)",
    }

    required_pre_textual: list[str] = []
    conclusion_label = "Conclusão"

    max_scan_pages = min(len(reader.pages), 20)
    for idx in range(max_scan_pages):
        raw_page_text = reader.pages[idx].extract_text() or ""
        p_text = raw_page_text.lower()
        p_lines = [ln.strip() for ln in raw_page_text.splitlines() if ln.strip()]

        # Se a página já é o início da Introdução textual (após Capa/Folha de Rosto), encerra a varredura pré-textual
        if idx >= 2 and any(
            re.search(r"^(=+\s*)?(1\s+)?(cap.{1,2}tulo\s+1\s+)?introdu.{1,3}o\b", ln, re.IGNORECASE)
            for ln in p_lines[:5]
        ):
            break

        for elem_name, pattern in pre_textual_Catalog.items():
            if elem_name not in required_pre_textual and re.search(pattern, p_text, re.IGNORECASE):
                required_pre_textual.append(elem_name)

        # O Sumário é o último elemento pré-textual (NBR 14724); interrompe após processá-lo
        if idx >= 2 and any(re.search(r"^sum.{1,2}rio\b", ln, re.IGNORECASE) for ln in p_lines[:4]):
            break

    # Verifica nas últimas páginas ou no sumário se usa "Considerações Finais"
    for idx in range(len(reader.pages)):
        p_text = reader.pages[idx].extract_text() or ""
        if re.search(r"considera.{1,3}es\s+finais", p_text, re.IGNORECASE):
            conclusion_label = "Considerações Finais"
            break

    return {
        "institution": institution,
        "department": department,
        "course": course,
        "advisor": advisor,
        "cover_header_lines": cover_header_lines,
        "has_cover_logo": has_cover_logo,
        "cover_logo_path": cover_logo_path,
        "preamble_text": preamble_text,
        "required_pre_textual": required_pre_textual,
        "conclusion_label": conclusion_label,
        "inferred_from_pdf": True,
    }
