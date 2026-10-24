"""Templates para documentos ABNT em LaTeX, Typst e Markdown."""

from abnt_mcp.templates.latex import get_latex_template
from abnt_mcp.templates.typst import get_typst_template
from abnt_mcp.templates.markdown import get_markdown_template

__all__ = [
    "get_latex_template",
    "get_typst_template",
    "get_markdown_template",
]
