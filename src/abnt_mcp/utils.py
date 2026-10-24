from __future__ import annotations

import re
from pathlib import Path


def read_file_with_fallback(file_path: str | Path) -> str:
    """Lê um arquivo de texto testando codificações comuns (UTF-8, latin-1, cp1252)."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Não foi possível decodificar o arquivo '{file_path}' com nenhuma codificação suportada.")


def write_file_with_encoding(file_path: str | Path, content: str, encoding: str = "utf-8") -> None:
    """Grava o conteúdo em arquivo com codificação especificada (padrão UTF-8)."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def remove_comments(content: str, file_type: str = "tex") -> str:
    """Remove comentários para evitar falsos positivos de citações ou seções comentadas."""
    if file_type == "tex":
        # Remove comentários iniciados com % (exceto se escapado com \%)
        return re.sub(r"(?<!\\)%.*$", "", content, flags=re.MULTILINE)
    elif file_type in ("md", "markdown"):
        # Remove comentários HTML <!-- ... -->
        return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    elif file_type == "typ":
        # Remove comentários // e /* ... */
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        return re.sub(r"//.*$", "", content, flags=re.MULTILINE)
    return content
