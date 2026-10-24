from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from pypdf import PdfReader


def read_pdf_paper(file_path: str, pages: Optional[list[int]] = None) -> dict[str, Any]:
    """Extrai texto de um documento PDF acadêmico para revisão, leitura ou resumo.
    
    Args:
        file_path: Caminho completo ou relativo para o arquivo .pdf
        pages: Lista opcional de páginas a extrair (base 1, ex: [1, 2, 3]). Se omitido, lê todas.
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"Arquivo não encontrado: {file_path}"}

    if path.suffix.lower() != ".pdf":
        return {"status": "error", "message": "O arquivo especificado não possui extensão .pdf."}

    try:
        reader = PdfReader(str(path))
        total_pages = len(reader.pages)

        if pages is None:
            indices = list(range(total_pages))
        else:
            indices = [p - 1 for p in pages if 1 <= p <= total_pages]

        extracted = []
        for idx in indices:
            page = reader.pages[idx]
            text = page.extract_text() or ""
            extracted.append({
                "page": idx + 1,
                "text": text.strip()
            })

        return {
            "status": "success",
            "file_name": path.name,
            "total_pages": total_pages,
            "extracted_count": len(extracted),
            "content": extracted
        }
    except Exception as e:
        return {"status": "error", "message": f"Falha ao ler PDF: {str(e)}"}
