"""Testes de integração do servidor FastMCP (ferramentas, prompts e recursos)."""

import pytest
from abnt_mcp.server import mcp


@pytest.mark.asyncio
async def test_server_tools_registered():
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    required_tools = [
        "search_academic_papers",
        "fetch_bibtex_by_doi",
        "validate_citations",
        "check_structure",
        "compile_tcc",
        "read_pdf_section",
        "clean_bibtex_file",
        "format_citation",
        "format_reference",
        "analyze_tone",
        "generate_academic_resumo",
    ]
    for r in required_tools:
        assert r in tool_names, f"Ferramenta '{r}' não foi registrada no FastMCP."


@pytest.mark.asyncio
async def test_server_prompts_registered():
    prompts = await mcp.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "revisar_capitulo" in prompt_names
    assert "formatar_citacao" in prompt_names
    assert "simular_banca" in prompt_names


@pytest.mark.asyncio
async def test_server_resources_registered():
    resources = await mcp.list_resources()
    resource_uris = [str(r.uri) for r in resources]
    assert "abnt://guia/citacoes" in resource_uris
    assert "abnt://guia/estrutura" in resource_uris
    assert "abnt://guia/referencias" in resource_uris
    assert "abnt://template/latex" in resource_uris
    assert "abnt://template/typst" in resource_uris
    assert "abnt://template/markdown" in resource_uris


@pytest.mark.asyncio
async def test_call_tool_format_citation():
    # Testa chamada direta de format_citation via call_tool
    res = await mcp.call_tool(
        "format_citation",
        {
            "authors": ["Silva", "Costa"],
            "year": 2024,
            "style": "in_parentheses"
        }
    )
    # FastMCP call_tool retorna objeto de resultado ou lista de conteúdos
    assert res is not None


@pytest.mark.asyncio
async def test_read_resource():
    res = await mcp.read_resource("abnt://guia/citacoes")
    assert res is not None
    assert len(res.contents) > 0
    assert "NBR 10520" in res.contents[0].content


@pytest.mark.asyncio
async def test_render_prompt():
    prompt_res = await mcp.render_prompt(
        "formatar_citacao",
        {
            "trecho": "O protocolo MCP padroniza contexto.",
            "autor": "Silva",
            "ano": "2023",
            "pagina": "12",
            "tipo": "direta_curta"
        }
    )
    assert prompt_res is not None
    assert len(prompt_res.messages) > 0
    text = prompt_res.messages[0].content.text
    assert "NBR 10520:2023" in text
