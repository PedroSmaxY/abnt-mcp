from __future__ import annotations

import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP

from abnt_mcp.tools.search import search_papers
from abnt_mcp.tools.bibtex import get_bibtex_by_doi, clean_bibtex_file
from abnt_mcp.tools.citations import validate_citations
from abnt_mcp.tools.structure import check_tcc_structure
from abnt_mcp.tools.compiler import compile_tcc
from abnt_mcp.tools.pdf import read_pdf_paper

mcp = FastMCP("ABNT-Copilot", description="Servidor MCP para assistência completa em TCCs e escrita acadêmica (ABNT).")


# ==============================================================================
# FERRAMENTAS (TOOLS)
# ==============================================================================

@mcp.tool()
def pesquisar_artigos(query: str, limit: int = 10, source: str = "crossref") -> dict:
    """Busca artigos acadêmicos científicos indexados no Crossref, Semantic Scholar ou SciELO."""
    return search_papers(query=query, limit=limit, source=source)


@mcp.tool()
def buscar_e_adicionar_bibtex(doi: str, bib_path: Optional[str] = None) -> dict:
    """Obtém a entrada BibTeX oficial a partir do DOI e opcionalmente adiciona ao .bib sem duplicar."""
    return get_bibtex_by_doi(doi=doi, bib_path=bib_path)


@mcp.tool()
def higienizar_bibtex(bib_path: str) -> dict:
    """Padroniza e valida o arquivo .bib conforme a norma ABNT NBR 6023 em UTF-8."""
    return clean_bibtex_file(bib_path=bib_path)


@mcp.tool()
def validar_citacoes(project_path: str) -> dict:
    """Valida citações no texto (LaTeX, Markdown, Typst) contra as referências do .bib."""
    return validate_citations(project_path=project_path)


@mcp.tool()
def verificar_estrutura_tcc(project_path: str) -> dict:
    """Verifica a presença dos elementos obrigatórios e opcionais segundo a ABNT NBR 14724."""
    return check_tcc_structure(project_path=project_path)


@mcp.tool()
def compilar_documento(project_path: str, engine: str = "auto") -> dict:
    """Compila o trabalho (LaTeX multi-pass, Pandoc ou Typst) gerando o PDF final."""
    return compile_tcc(project_path=project_path, engine=engine)


@mcp.tool()
def extrair_texto_pdf(file_path: str, pages: Optional[list[int]] = None) -> dict:
    """Extrai texto de um arquivo PDF local para leitura ou revisão acadêmica."""
    return read_pdf_paper(file_path=file_path, pages=pages)


# ==============================================================================
# PROMPTS EMBUTIDOS
# ==============================================================================

@mcp.prompt()
def revisar_capitulo(texto: str, foco: str = "geral") -> str:
    """Revisa um trecho ou capítulo com critérios rigorosos de tom científico e normas ABNT."""
    return f"""Atue como um orientador de pós-graduação e revisor acadêmico experiente.
Analise e aprimore o seguinte texto acadêmico (Foco: {foco}):

---
{texto}
---

Instruções para sua resposta:
1. Diagnóstico do Tom: Aponte qualquer uso de 1ª pessoa ('eu', 'nós') e reescreva para a 3ª pessoa ou voz passiva impessoal.
2. Rigor Científico: Indique afirmações que carecem de citação bibliográfica ou evidência factual.
3. Coesão e Fluidez: Mostre onde a transição entre parágrafos pode ser aprimorada.
4. Versão Reformulada: Forneça o texto revisado pronto para inclusão no TCC."""


@mcp.prompt()
def formatar_citacao(trecho: str, autor: str, ano: str, pagina: str = "", formato: str = "latex") -> str:
    """Gera a sintaxe correta de citação direta ou indireta conforme a NBR 10520."""
    return f"""Gere a citação exata para o formato '{formato}' de acordo com a ABNT NBR 10520:
- Trecho: "{trecho}"
- Autor(es): {autor}
- Ano: {ano}
- Página: {pagina}

Lembre-se:
- Citação direta curta (até 3 linhas): no corpo do parágrafo entre aspas.
- Citação direta longa (+ de 3 linhas): bloco recuado a 4 cm, fonte tamanho 10, espaçamento simples e sem aspas."""


@mcp.prompt()
def simular_banca(titulo: str, resumo: str, conclusao: str) -> str:
    """Simula as perguntas e questionamentos que a banca examinadora fará sobre o trabalho."""
    return f"""Você é um membro rigoroso da banca avaliadora de TCC.
Analise a coerência entre a proposta e o fechamento do trabalho:

Título: {titulo}
Resumo: {resumo}
Conclusão: {conclusao}

Apresente:
1. Três perguntas difíceis que a banca certamente fará sobre a metodologia e resultados.
2. Pontos frágeis onde a justificativa ou embasamento parece insuficiente.
3. Recomendações imediatas para blindar a defesa."""


# ==============================================================================
# RECURSOS (RESOURCES)
# ==============================================================================

@mcp.resource("abnt://guia/nbr10520")
def guia_nbr10520() -> str:
    """Resumo das regras vigentes da ABNT NBR 10520 para citações acadêmicas."""
    return """# ABNT NBR 10520 - Citações em Documentos

## 1. Citação Indireta (Paráfrase)
- No texto: De acordo com Silva (2023), o aprendizado federado...
- Entre parênteses: O aprendizado federado preserva a privacidade (SILVA, 2023).

## 2. Citação Direta Curta (até 3 linhas)
- Integrada ao texto, obrigatoriamente entre aspas duplas.
- Exemplo: Segundo Oliveira (2022, p. 45), "a tecnologia amplia os horizontes pedagógicos".

## 3. Citação Direta Longa (mais de 3 linhas)
- Parágrafo destacado com recuo de 4 cm da margem esquerda.
- Fonte menor (tamanho 10 ou 11), espaçamento entre linhas simples e SEM aspas.

## 4. Citação de Citação (Apud)
- Usado apenas quando a obra original não estiver acessível.
- Exemplo: Turing (1950 apud RUSSELL; NORVIG, 2020, p. 12).
"""


@mcp.resource("abnt://guia/nbr14724")
def guia_nbr14724() -> str:
    """Resumo da estrutura de trabalhos acadêmicos segundo a ABNT NBR 14724."""
    return """# ABNT NBR 14724 - Estrutura de Trabalhos Acadêmicos

## Elementos Pré-Textuais
- Capa (Obrigatório)
- Folha de Rosto (Obrigatório)
- Errata (Opcional)
- Dedicatória / Agradecimentos / Epígrafe (Opcionais)
- Resumo na língua vernácula com palavras-chave (Obrigatório)
- Resumo em língua estrangeira - Abstract (Obrigatório)
- Lista de ilustrações (Opcional)
- Lista de tabelas (Opcional)
- Lista de abreviaturas e siglas (Opcional)
- Sumário (Obrigatório)

## Elementos Textuais
- Introdução (Obrigatório)
- Desenvolvimento: Fundamentação Teórica, Metodologia e Resultados (Obrigatório)
- Conclusão / Considerações Finais (Obrigatório)

## Elementos Pós-Textuais
- Referências (Obrigatório - NBR 6023)
- Glossário (Opcional)
- Apêndices: materiais elaborados pelo próprio autor (Opcional)
- Anexos: documentos de terceiros anexados (Opcional)
"""


def main():
    mcp.run()


if __name__ == "__main__":
    main()
