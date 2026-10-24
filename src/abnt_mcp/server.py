"""Servidor FastMCP do ABNT Copilot MCP.

Ponto central de registro de ferramentas (@mcp.tool), prompts (@mcp.prompt)
e recursos (@mcp.resource).
"""

from __future__ import annotations
import sys
from typing import Any, Literal
from fastmcp import FastMCP

from abnt_mcp.config import SERVER_NAME
from abnt_mcp.models import CitationInput, ReferenceInput, Author
from abnt_mcp.pillars.diagnostics import (
    check_project_structure,
    audit_citations_and_references,
    analyze_scientific_tone,
)
from abnt_mcp.pillars.writing import (
    format_citation_abnt,
    format_reference_abnt,
    generate_abnt_resumo,
    reformulate_to_impersonal,
    format_figure_abnt,
    format_table_abnt,
)
from abnt_mcp.pillars.compiler import compile_project
from abnt_mcp.pillars.advisory import (
    search_academic_literature,
    fetch_bibtex_by_doi_service,
    clean_bibtex_file_service,
    simulate_banca_examination,
)
from abnt_mcp.pillars.spec import (
    init_project_spec,
    scaffold_project,
    audit_project_against_spec,
    get_spec_template_resource,
)
from abnt_mcp.parsers.pdf_reader import extract_pdf_section
from abnt_mcp.resources.guides import (
    GUIDE_CITATIONS_NBR10520,
    GUIDE_STRUCTURE_NBR14724,
    GUIDE_REFERENCES_NBR6023,
    GUIDE_SDD_WORKFLOW,
)
from abnt_mcp.templates.latex import get_latex_template
from abnt_mcp.templates.typst import get_typst_template
from abnt_mcp.templates.markdown import get_markdown_template

# Inicializa o servidor FastMCP
mcp = FastMCP(
    SERVER_NAME,
    instructions="Servidor MCP para validação, redação, compilação e consultoria acadêmica segundo as normas ABNT.",
)


# ==============================================================================
# 1. FERRAMENTAS (@mcp.tool)
# ==============================================================================

@mcp.tool()
def search_academic_papers(
    query: str,
    source: Literal["all", "crossref", "scielo"] = "all",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Busca artigos científicos recentes nas bases abertas Crossref e SciELO por DOI, título e resumo.
    Útil para embasar fundamentação teórica e capítulos de revisão bibliográfica.
    """
    return search_academic_literature(query=query, source=source, limit=limit)


@mcp.tool()
def fetch_bibtex_by_doi(
    doi: str,
    bib_file: str | None = None,
) -> dict[str, Any]:
    """
    Recupera a entrada BibTeX oficial correspondente a um DOI via negociação de conteúdo
    e opcionalmente anexa ao arquivo .bib do projeto sem duplicar chaves ou DOIs.
    """
    return fetch_bibtex_by_doi_service(doi=doi, bib_file=bib_file)


@mcp.tool()
def validate_citations(
    project_path: str,
    bib_path: str | None = None,
) -> dict[str, Any]:
    """
    Realiza auditoria cruzada completa entre o texto e as referências:
    - Suporta LaTeX (\\cite, \\citeonline, \\apud, \\citep), Markdown ([@ref]) e Typst (@ref).
    - Detecta citações órfãs (citadas no texto, mas ausentes no .bib).
    - Aponta entradas do .bib nunca citadas no texto.
    - Identifica citações com sobrenome em CAIXA ALTA violando a NBR 10520:2023.
    """
    result = audit_citations_and_references(project_path=project_path, bib_path=bib_path)
    return result.model_dump()


@mcp.tool()
def check_structure(
    project_path: str,
    standard: str = "ABNT_14724",
) -> dict[str, Any]:
    """
    Valida a conformidade da estrutura acadêmica conforme a ABNT NBR 14724:2011:
    - Verifica elementos pré-textuais obrigatórios (capa, folha de rosto, resumo, abstract, sumário).
    - Não penaliza a ausência de listas opcionais (figuras, tabelas, siglas).
    - Verifica elementos textuais e pós-textuais (referências).
    - Diagnostica violações de numeração progressiva de seções da NBR 6024 (ex: ponto indevido no final).
    """
    result = check_project_structure(project_path=project_path, standard=standard)
    return result.model_dump()


@mcp.tool()
def compile_tcc(
    project_path: str,
    engine: Literal["auto", "latex", "typst", "markdown"] = "auto",
) -> dict[str, Any]:
    """
    Compila o projeto acadêmico para PDF utilizando LaTeX (abnTeX2 com ciclo multi-pass para evitar [?]),
    Typst ou Pandoc com --citeproc. Inclui pré-checagem de erros de sintaxe e diagnóstico amigável.
    """
    return compile_project(project_path=project_path, engine=engine)


@mcp.tool()
def read_pdf_section(
    pdf_path: str,
    pages: list[int] | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
) -> dict[str, Any]:
    """
    Extrai o texto e dados estatísticos de um PDF acadêmico para fins de revisão e auditoria.
    Permite selecionar páginas específicas ou intervalos (1-indexado).
    """
    return extract_pdf_section(
        pdf_path=pdf_path,
        pages=pages,
        start_page=start_page,
        end_page=end_page,
    )


@mcp.tool()
def clean_bibtex_file(
    bib_path: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Higieniza e normaliza um arquivo BibTeX segundo a ABNT NBR 6023:2018:
    - Converte acentos LaTeX obsoletos para UTF-8 nativo estrito.
    - Normaliza abreviação de meses (incluindo a regra de 'maio' sem ponto).
    - Valida campos obrigatórios por tipo de entrada sem corromper ou perder chaves.
    """
    return clean_bibtex_file_service(bib_path=bib_path, output_path=output_path)


@mcp.tool()
def format_citation(
    authors: list[str],
    year: str | int,
    page: str | None = None,
    style: Literal["in_parentheses", "in_text"] = "in_parentheses",
    quote_type: Literal["direct_short", "direct_long", "indirect"] = "indirect",
    quote_text: str | None = None,
    target_format: Literal["markdown", "latex", "typst", "text"] = "markdown",
) -> dict[str, Any]:
    """
    Formata chamadas de citação rigorosamente conforme a NBR 10520:2023:
    - Sobrenomes em caixa mista/baixa dentro dos parênteses (ex: '(Silva, 2023)' e nunca '(SILVA, 2023)').
    - Citações diretas curtas (<=3 linhas): entre aspas com ponto final APÓS os parênteses.
    - Citações diretas longas (>3 linhas): bloco recuado a 4 cm, fonte 10, espaçamento simples e sem aspas.
    """
    data = CitationInput(
        authors=authors,
        year=year,
        page=page,
        style=style,
        quote_type=quote_type,
        quote_text=quote_text,
        target_format=target_format,
    )
    return format_citation_abnt(data)


@mcp.tool()
def format_reference(
    entry_type: Literal["book", "book_chapter", "journal_article", "website", "thesis", "legislation", "conference", "software"],
    title: str,
    year: str | int,
    subtitle: str | None = None,
    authors: list[dict[str, str]] | None = None,
    edition: str | None = None,
    city: str | None = None,
    publisher: str | None = None,
    journal_name: str | None = None,
    volume: str | None = None,
    number: str | None = None,
    pages: str | None = None,
    url: str | None = None,
    access_date: str | None = None,
    emphasis_style: Literal["bold", "italic"] = "bold",
) -> dict[str, Any]:
    """
    Formata uma referência bibliográfica conforme a ABNT NBR 6023:2018:
    - Alinhamento à margem esquerda.
    - Destaque em negrito/itálico aplicado exclusivamente ao título principal (nunca ao subtítulo).
    - Abreviação correta de meses em língua portuguesa.
    """
    parsed_authors = [Author(**a) for a in authors] if authors else None
    data = ReferenceInput(
        entry_type=entry_type,
        title=title,
        subtitle=subtitle,
        authors=parsed_authors,
        edition=edition,
        city=city,
        publisher=publisher,
        year=year,
        journal_name=journal_name,
        volume=volume,
        number=number,
        pages=pages,
        url=url,
        access_date=access_date,
        emphasis_style=emphasis_style,
    )
    return format_reference_abnt(data)


@mcp.tool()
def analyze_tone(text: str) -> dict[str, Any]:
    """
    Analisa o rigor científico e a impessoalidade da escrita acadêmica:
    - Detecta uso de 1ª pessoa ('eu fiz', 'nós achamos', 'meu trabalho').
    - Sinaliza juízos de valor sem comprovação ('claramente', 'obviamente', 'sem dúvida').
    - Encontra expressões coloquiais e parágrafos desprovidos de citação/fundamentação.
    - Sugere reformulações para voz passiva sintética e terceira pessoa.
    """
    result = analyze_scientific_tone(text)
    return result.model_dump()


@mcp.tool()
def generate_academic_resumo(
    context: str,
    objective: str,
    methodology: str,
    results: str,
    conclusion: str,
    keywords: list[str],
    language: Literal["pt", "en"] = "pt",
) -> dict[str, Any]:
    """
    Gera um Resumo (em português) ou Abstract (em inglês) na estrutura canônica da NBR 6028:2021:
    - Parágrafo único contínuo.
    - Verbos na 3ª pessoa e linguagem impessoal concisa.
    - Avalia a faixa de palavras (150 a 500 para TCC/teses).
    - Formata palavras-chave separadas por ponto e vírgula e terminadas em ponto.
    """
    return generate_abnt_resumo(
        context=context,
        objective=objective,
        methodology=methodology,
        results=results,
        conclusion=conclusion,
        keywords=keywords,
        language=language,
    )


@mcp.tool()
def format_figure(
    image_path: str,
    caption: str,
    source: str | None = None,
    figure_number: int | str = 1,
    target_format: Literal["markdown", "latex", "typst"] = "markdown",
) -> dict[str, Any]:
    """
    Formata uma figura/imagem no padrão da ABNT NBR 14724:
    - Identificação no topo ('Figura X – Título').
    - Imagem centralizada com caminho no computador.
    - Indicação da fonte obrigatória no rodapé (default dinâmico com ano corrente).
    - Fornece exemplo da chamada obrigatória no texto e snippets prontos em Markdown, LaTeX e Typst.
    """
    return format_figure_abnt(
        image_path=image_path,
        caption=caption,
        source=source,
        figure_number=figure_number,
        target_format=target_format,
    )


@mcp.tool()
def format_table(
    title: str,
    headers: list[str],
    rows: list[list[str]],
    source: str | None = None,
    table_number: int | str = 1,
    category: Literal["tabela", "quadro"] = "tabela",
) -> dict[str, Any]:
    """
    Formata dados no padrão das Normas Tabulares do IBGE (1993) e ABNT NBR 14724:
    - 'tabela': para dados numéricos/estatísticos com bordas laterais ABERTAS (padrão IBGE).
    - 'quadro': para dados textuais/qualitativos com bordas fechadas em moldura completa.
    - Gera snippets em Markdown, LaTeX (booktabs para tabelas) e Typst.
    """
    return format_table_abnt(
        title=title,
        headers=headers,
        rows=rows,
        source=source,
        table_number=table_number,
        category=category,
    )


@mcp.tool()
def init_research_spec(
    project_path: str,
    title: str,
    research_problem: str,
    general_objective: str,
    specific_objectives: list[dict[str, Any]],
    methodology_summary: str,
    document_type: Literal["tcc", "dissertacao", "tese", "artigo"] = "tcc",
    author: str | None = None,
    institution: str | None = None,
    course: str | None = None,
    advisor: str | None = None,
    min_references: int | None = None,
    planned_chapters: list[dict[str, Any]] | None = None,
    sample_pdf_path: str | None = None,
    logo_path: str | None = None,
) -> dict[str, Any]:
    """
    Inicializa o manifesto de Especificação Científica (SDD) 'abnt.spec.json' e 'SPEC.md' no projeto:
    - Camada 1: Perfil Normativo e Institucional (com aprendizado automático de PDF modelo da faculdade e cópia de logo).
    - Camada 2: Matriz Científica rastreável (Problema, Objetivo Geral e Objetivos Específicos OBJ-XX).
    - Camada 3: Capítulos planejados com metas mínimas de extensão e citações.
    """
    return init_project_spec(
        project_path=project_path,
        title=title,
        research_problem=research_problem,
        general_objective=general_objective,
        specific_objectives=specific_objectives,
        methodology_summary=methodology_summary,
        document_type=document_type,
        author=author,
        institution=institution,
        course=course,
        advisor=advisor,
        min_references=min_references,
        planned_chapters=planned_chapters,
        sample_pdf_path=sample_pdf_path,
        logo_path=logo_path,
    )


@mcp.tool()
def scaffold_academic_project(
    project_path: str,
    title: str,
    author: str,
    document_type: Literal["tcc", "dissertacao", "tese", "artigo"] = "tcc",
    format: Literal["typst", "latex", "markdown"] = "typst",
    institution: str | None = None,
    course: str | None = None,
    advisor: str | None = None,
    research_problem: str | None = None,
    general_objective: str | None = None,
    specific_objectives: list[dict[str, Any]] | None = None,
    methodology_summary: str | None = None,
    sample_pdf_path: str | None = None,
    logo_path: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Inicializa a árvore completa de diretórios e arquivos de um projeto acadêmico (TCC, Dissertação, Tese ou Artigo):
    - Cria diretórios capitulos/, figuras/, tabelas/, anexos/, apendices/ e .abnt-mcp/.
    - Se sample_pdf_path for fornecido, extrai automaticamente o padrão da universidade (cabeçalho da capa, preâmbulo, seções exigidas e brasão/logo da página 1).
    - Se logo_path for fornecido, copia o arquivo de logotipo para figuras/logo_instituicao.* e referencia-o na capa.
    - Gera abnt.spec.json, SPEC.md, referencias.bib e o arquivo principal (main.typ, main.tex ou main.md).
    """
    result = scaffold_project(
        project_path=project_path,
        title=title,
        author=author,
        document_type=document_type,
        format=format,
        institution=institution,
        course=course,
        advisor=advisor,
        research_problem=research_problem,
        general_objective=general_objective,
        specific_objectives=specific_objectives,
        methodology_summary=methodology_summary,
        sample_pdf_path=sample_pdf_path,
        logo_path=logo_path,
        overwrite=overwrite,
    )
    return result.model_dump()


@mcp.tool()
def audit_research_spec(
    project_path: str,
    spec_path: str | None = None,
) -> dict[str, Any]:
    """
    Audita o manuscrito acadêmico contra o manifesto 'abnt.spec.json' (Spec-Driven Academic Writing):
    - Verifica se cada objetivo específico (OBJ-01, OBJ-02...) foi discutido no texto e respondido na Conclusão.
    - Confere a presença dos capítulos planejados e a meta mínima de referências no .bib.
    - Reporta violações com IDs canônicos de regra (NBR14724-R01, NBR6022-R01, NBR10520-R01, NBR6024-R01).
    """
    result = audit_project_against_spec(project_path=project_path, spec_path=spec_path)
    return result.model_dump()


@mcp.tool()
def simulate_banca(project_path: str) -> dict[str, Any]:
    """
    Executa a simulação de banca examinadora (TCC/Dissertação/Tese/Artigo):
    - Avalia alinhamento entre Introdução, Objetivos Específicos (via abnt.spec.json se presente) e Conclusão.
    - Calcula notas por eixo e formula perguntas críticas de arguição para a defesa oral.
    """
    return simulate_banca_examination(project_path=project_path)


# ==============================================================================
# 2. PROMPTS NATIVOS (@mcp.prompt)
# ==============================================================================

@mcp.prompt()
def revisar_capitulo(texto: str, foco: str = "geral") -> str:
    """
    Prompt acadêmico especializado para revisão aprofundada de um capítulo acadêmico,
    gerando nota qualitativa, diagnóstico de rigor, pontos fortes e lista de melhorias.
    """
    return f"""Atue como um Revisor Acadêmico Sênior e membro de banca examinadora.
Analise detalhadamente o capítulo/trecho abaixo com foco em '{foco}'.

DIRETRIZES DE AVALIAÇÃO:
1. Impessoalidade e Rigor (NBR 14724): Elimine 1ª pessoa ('eu fiz', 'nós observamos') substituindo por voz passiva sintética ('analisou-se', 'observou-se').
2. Juízos de valor: Remova advérbios opinativos ('obviamente', 'claramente', 'com certeza') e exija dados empíricos ou fontes.
3. Citações (NBR 10520:2023): Verifique se os autores entre parênteses estão em caixa baixa/mista (Silva, 2023) e NUNCA em CAIXA ALTA (SILVA, 2023).
4. Coerência lógica: Avalie a transição entre parágrafos e se as alegações técnicas possuem citação.

TEXTO PARA REVISÃO:
---
{texto}
---

FORMATO DA SUA RESPOSTA:
- **Nota Global de Rigor Científico (0 a 100)**
- **Pontos Fortes do Trecho**
- **Inadequações Encontradas (com trecho original e sugestão de correção)**
- **Versão Reescrita e Polida no Padrão ABNT**
"""


@mcp.prompt()
def formatar_citacao(
    trecho: str,
    autor: str,
    ano: str,
    pagina: str = "",
    tipo: str = "direta_curta",
) -> str:
    """
    Prompt para gerar o código exato da citação em LaTeX (abnTeX2), Markdown e Typst
    segundo a NBR 10520:2023.
    """
    page_param = f", pagina='{pagina}'" if pagina else ""
    return f"""Atue como um Especialista em Normas ABNT (NBR 10520:2023).
Gere os snippets exatos de citação para o trecho abaixo:

- Texto da citação: "{trecho}"
- Autor: {autor}
- Ano: {ano}
- Página: {pagina or "Não informada"}
- Tipo: {tipo} (direta curta <= 3 linhas, direta longa > 3 linhas, ou indireta)

REGRAS MANDATÓRIAS (NBR 10520:2023):
- Autores entre parênteses usam apenas inicial maiúscula: ({autor.title()}, {ano}) e NUNCA em CAIXA ALTA.
- Citação direta curta: no corpo do parágrafo, entre aspas, ponto APÓS os parênteses.
- Citação direta longa: bloco recuado a 4 cm, tamanho 10, espaçamento 1,0 simples, SEM aspas.

Forneça os códigos prontos para:
1. **Markdown**
2. **LaTeX (abnTeX2)**
3. **Typst**
"""


@mcp.prompt()
def simular_banca(projeto_path: str) -> str:
    """
    Prompt para simulação de banca examinadora impiedosa e construtiva,
    avaliando congruência entre introdução e conclusão, rigor metodológico e perguntas da defesa.
    """
    return f"""Atue como o Presidente da Banca Examinadora de Defesa de TCC/Mestrado.
O candidato submeteu o projeto localizado em: '{projeto_path}'.

Realize uma arguição rigorosa e construtiva cobrindo:
1. **Alinhamento dos Objetivos:** Os objetivos específicos traçados na introdução foram realmente respondidos na conclusão?
2. **Replicabilidade Metodológica:** A metodologia possui detalhes suficientes para que outro pesquisador replique o experimento?
3. **Atualidade da Literatura:** As referências contemplam artigos recentes com DOI ou estão defasadas?
4. **Armadilhas e Perguntas da Banca:** Formule as 3 perguntas mais difíceis que os membros da banca farão ao estudante na apresentação oral.

Apresente um parecer com: Veredito preliminar, Riscos críticos que podem reprovar o trabalho e Ações imediatas de mitigação.
"""


# ==============================================================================
# 3. RECURSOS (@mcp.resource)
# ==============================================================================

@mcp.resource("abnt://guia/citacoes")
def resource_guia_citacoes() -> str:
    """Guia canônico e síntese das regras da ABNT NBR 10520:2023 (Citações)."""
    return GUIDE_CITATIONS_NBR10520


@mcp.resource("abnt://guia/estrutura")
def resource_guia_estrutura() -> str:
    """Checklist completo da ABNT NBR 14724:2011 (Estrutura e Paginação de Trabalhos Acadêmicos)."""
    return GUIDE_STRUCTURE_NBR14724


@mcp.resource("abnt://guia/referencias")
def resource_guia_referencias() -> str:
    """Síntese das regras da ABNT NBR 6023:2018 (Elaboração de Referências Bibliográficas)."""
    return GUIDE_REFERENCES_NBR6023


@mcp.resource("abnt://guia/sdd")
def resource_guia_sdd() -> str:
    """Guia de Escrita Acadêmica Orientada a Especificações (SDD - Spec-Driven Development)."""
    return GUIDE_SDD_WORKFLOW


@mcp.resource("abnt://template/latex")
def resource_template_latex() -> str:
    """Template funcional completo para monografias/TCCs em LaTeX configurado com abnTeX2."""
    return get_latex_template()


@mcp.resource("abnt://template/typst")
def resource_template_typst() -> str:
    """Template moderno completo para trabalhos acadêmicos em Typst com regras ABNT nativas."""
    return get_typst_template()


@mcp.resource("abnt://template/markdown")
def resource_template_markdown() -> str:
    """Template acadêmico para Pandoc Markdown com cabeçalho YAML e suporte a CSL ABNT."""
    return get_markdown_template()


@mcp.resource("abnt://template/spec")
def resource_template_spec() -> str:
    """Template JSON do manifesto científico SDD (abnt.spec.json) em 3 camadas."""
    return get_spec_template_resource()


def main() -> None:
    """Ponto de entrada para execução via CLI ou uvx abnt-mcp."""
    mcp.run()


if __name__ == "__main__":
    main()
