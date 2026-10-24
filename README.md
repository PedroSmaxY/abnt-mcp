# ABNT-MCP 🎓

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Protocol: MCP](https://img.shields.io/badge/Protocol-MCP-blue.svg)](https://modelcontextprotocol.io)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

> **O copiloto definitivo para TCCs, dissertações, teses e artigos acadêmicos no padrão ABNT via Model Context Protocol (MCP).**

---

## 🚀 O que é o ABNT-MCP?

O **ABNT-MCP** é um servidor MCP desenvolvido em Python moderno com **FastMCP** projetado para ser o braço direito de qualquer estudante, orientador ou pesquisador brasileiro. Ele transforma o seu assistente de IA (Claude Desktop, Cursor, Antigravity, OpenCode, Zed) em um orientador acadêmico e revisor de normas técnicas.

### 🌟 Principais Recursos

1. **Validação Estrutural Rigorosa (NBR 14724):**
   * Identifica elementos pré-textuais, textuais e pós-textuais obrigatórios sem gerar falsos positivos em listas opcionais (como lista de ilustrações ou tabelas).
   * Suporte nativo a **LaTeX** (`abntex2`), **Markdown** (Pandoc) e **Typst**.

2. **Auditoria de Citações Cruzadas:**
   * Cruza o texto com o seu arquivo `.bib` para detectar citações órfãs ou referências não utilizadas.
   * Suporta os comandos do `abntex2` (`\cite`, `\citeonline`, `\apud`, `\citet`, etc.), Markdown (`[@ref]`) e Typst (`@ref`).

3. **Busca e Gestão Bibliográfica:**
   * Busca artigos em bases internacionais e latino-americanas (**Crossref**, **Semantic Scholar** e **SciELO**).
   * Obtenção direta de BibTeX oficial via DOI com proteção contra duplicatas.
   * Higienização de arquivos `.bib` para a **NBR 6023** preservando acentuação em UTF-8 nativo.

4. **Compilação Inteligente com Pré-checagem:**
   * Compilação multi-pass para LaTeX (`latexmk` ou `pdflatex -> bibtex -> pdflatex`) para garantir que nenhuma citação fique como `[?]`.
   * Compilação com Pandoc e Typst.

5. **Prompts e Recursos Nativos:**
   * Simulação de banca examinadora, formatação de citações longas/curtas e revisão de tom acadêmico impessoal.

---

## 📦 Como Usar

### Execução Instantânea com `uv` (Recomendado)

Você não precisa instalar dependências manualmente. Com o [uv](https://github.com/astral-sh/uv), basta configurar no cliente MCP desejado:

#### No Claude Desktop (`claude_desktop_config.json`) ou Antigravity:

```json
{
  "mcpServers": {
    "abnt": {
      "command": "uv",
      "args": [
        "run",
        "--with", "mcp[cli]",
        "--with", "bibtexparser",
        "--with", "requests",
        "--with", "pypdf",
        "python", "-m", "abnt_mcp.server"
      ],
      "env": {
        "ABNT_MCP_EMAIL": "seu.email@academico.br"
      }
    }
  }
}
```

#### No Cursor (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "abnt": {
      "command": "uvx",
      "args": ["abnt-mcp"]
    }
  }
}
```

---

## 🛠️ Ferramentas Disponíveis

| Ferramenta | Descrição |
| :--- | :--- |
| `pesquisar_artigos` | Pesquisa trabalhos científicos no Crossref, Semantic Scholar e SciELO. |
| `buscar_e_adicionar_bibtex` | Obtém BibTeX por DOI e insere de forma atômica no `.bib`. |
| `higienizar_bibtex` | Padroniza o `.bib` conforme NBR 6023 com suporte a UTF-8. |
| `validar_citacoes` | Cruza citações do texto com o `.bib` (LaTeX, Markdown, Typst). |
| `verificar_estrutura_tcc` | Valida conformidade estrutural com a ABNT NBR 14724. |
| `compilar_documento` | Compila o trabalho para PDF via LaTeX multi-pass, Pandoc ou Typst. |
| `extrair_texto_pdf` | Lê e extrai texto de artigos em PDF para revisão ou síntese. |

---

## 🧪 Desenvolvimento & Testes

Para rodar os testes localmente com `uv`:

```bash
uv run --with pytest pytest tests/ -v
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte [LICENSE](LICENSE) para mais informações.
