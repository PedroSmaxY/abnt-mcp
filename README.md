# 🎓 ABNT Copilot MCP (`abnt-mcp`)

> **O servidor Model Context Protocol (MCP) definitivo para estudantes, pesquisadores e orientandos no Brasil.**
> Desenvolvido em Python moderno (>=3.10) utilizando **FastMCP**, pronto para distribuição e execução instantânea via `uvx abnt-mcp`.

---

## 📑 Sumário

- [Visão Geral](#-visão-geral)
- [Os 4 Pilares do MCP](#-os-4-pilares-do-mcp)
- [Instalação e Execução](#-instalação-e-execução)
- [Configuração nos Clientes MCP](#-configuração-nos-clientes-mcp)
  - [Cursor IDE](#1-cursor-ide)
  - [Claude Desktop](#2-claude-desktop)
  - [Google Antigravity](#3-google-antigravity)
- [Catálogo de Ferramentas (Tools)](#-catálogo-de-ferramentas-tools)
- [Catálogo de Prompts Nativos](#-catálogo-de-prompts-nativos)
- [Catálogo de Recursos Nativos (Resources)](#-catálogo-de-recursos-nativos-resources)
- [Atenção à NBR 10520:2023 (Fim da Caixa Alta)](#-atenção-à-nbr-105202023-fim-da-caixa-alta)
- [Testes Automatizados](#-testes-automatizados)
- [Licença](#-licença)

---

## 🌟 Visão Geral

Elaborar um TCC, dissertação, tese ou artigo no Brasil costuma ser um processo desgastante devido às minúcias das normas da **ABNT**. 

O **ABNT Copilot MCP** transforma qualquer assistente de IA conectado via protocolo MCP em um **arquiteto acadêmico e revisor de banca**, garantindo conformidade matemática com as normas vigentes, auditoria de citações, higienização de BibTeX, compilação de documentos e busca de literatura científica.

---

## 🎯 Os 4 Pilares do MCP

### 1. 🔍 Pilar 1: Analisar & Diagnosticar
- **Validação Estrutural (NBR 14724:2011):** Diagnóstico automático dos elementos pré-textuais (capa, folha de rosto, resumo, abstract, sumário), textuais (introdução, desenvolvimento, conclusão) e pós-textuais (referências). Sem falsos positivos: não penaliza ausência de listas opcionais.
- **Auditoria Cruzada de Citações vs Referências:**
  - Identifica **citações órfãs** (chaves citadas no texto que não constam no `.bib`).
  - Identifica **entradas do `.bib` nunca utilizadas** no texto.
  - Suporte nativo a **LaTeX** (`\cite`, `\citeonline`, `\apud`, `\citep`), **Markdown** (`[@ref]`, `@ref`) e **Typst** (`@ref`).
- **Análise de Tom e Rigor Científico:**
  - Varredura de 1ª pessoa (*"eu fiz"*, *"nós achamos"*, *"meu estudo"*).
  - Identificação de juízos de valor sem comprovação (*"claramente"*, *"obviamente"*, *"sem dúvida"*).
  - Detecção de coloquialismos (*"a gente"*, *"pra caramba"*, *"bater o martelo"*, *"coisa"*).
  - Sinalização de parágrafos extensos sem fundamentação bibliográfica.

### 2. ✍️ Pilar 2: Redigir & Reformular
- **Formatador de Citações (NBR 10520:2023):**
  - Citações diretas curtas (até 3 linhas) com pontuação após os parênteses.
  - Citações diretas longas (> 3 linhas) em bloco recuado a 4 cm, fonte 10, espaçamento simples e sem aspas nos formatos Markdown, LaTeX e Typst.
  - Formatação autor-data estritamente em **caixa mista/baixa** `(Silva, 2023)` conforme a atualização de 2023.
- **Formatador de Referências (NBR 6023:2018):**
  - Livros, artigos de revistas, teses, sites e leis.
  - Destaque em negrito **apenas no título principal** (subtítulo após dois pontos nunca recebe destaque).
  - Alinhamento obrigatório à margem esquerda e abreviação correta de meses (`maio` sem ponto).
- **Gerador de Resumo e Abstract (NBR 6028:2021):**
  - Estrutura canônica: Contexto, Objetivo, Metodologia, Resultados e Conclusão.
  - Validação de extensão (150 a 500 palavras).
  - 3 a 5 palavras-chave separadas por ponto e vírgula e terminadas em ponto.

### 3. 🧪 Pilar 3: Testar & Compilar
- **Compilação Multi-engine:**
  - **LaTeX (`abntex2`):** Suporte nativo a `latexmk` ou ciclo multi-pass (`pdflatex -> bibtex -> pdflatex -> pdflatex`) para eliminar referências com `[?]`.
  - **Typst:** Compilação nativa ultra-rápida integrada com `#bibliography`.
  - **Markdown:** Compilação Pandoc com `--citeproc` e estilos CSL.
- **Linter e Pré-checagem de Sintaxe:** Diagnostica ambientes desbalanceados (`\begin{...}` sem `\end{...}`) e caracteres desprotegidos antes de enviar ao compilador, com indicação exata de arquivo e linha.

### 4. 💡 Pilar 4: Dicas, Mentoria & Banca Examinadora
- **Busca de Literatura Científica:** Consulta em tempo real às bases abertas **Crossref** e **SciELO** com retorno de DOI, título, autores, ano, periódico e resumo.
- **Obtenção de BibTeX por DOI:** Download do BibTeX oficial diretamente pelo DOI (`doi.org`) com inserção inteligente no arquivo `.bib` sem duplicatas.
- **Higienizador de BibTeX:** Limpeza de acentos legados de LaTeX para UTF-8 estrito, validação de campos obrigatórios e correção de meses.
- **Simulador de Banca:** Análise impiedosa e construtiva da consistência entre Introdução e Conclusão, rigor metodológico e formulação de perguntas difíceis para a defesa oral.

---

## 🚀 Instalação e Execução

### Execução Instantânea (Recomendada via `uvx`)
Não é necessário instalar nada globalmente se você possui o `uv` instalado:

```bash
uvx abnt-mcp
```

### Instalação via pip / uv
```bash
# Com uv:
uv pip install abnt-mcp

# Com pip:
pip install abnt-mcp

# Executar o servidor:
abnt-mcp
```

---

## ⚙️ Configuração nos Clientes MCP

### 1. Cursor IDE
No diretório do seu projeto ou globalmente, crie ou edite o arquivo `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "abnt-mcp": {
      "command": "uvx",
      "args": ["abnt-mcp"]
    }
  }
}
```

### 2. Claude Desktop
Edite o arquivo de configuração do Claude Desktop (`claude_desktop_config.json`):
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

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

### 3. Google Antigravity
No arquivo de configuração de MCP (`mcp_config.json`):

```json
{
  "mcpServers": {
    "abnt-mcp": {
      "command": "uvx",
      "args": ["abnt-mcp"]
    }
  }
}
```

---

## 🛠️ Catálogo de Ferramentas (Tools)

| Ferramenta | Descrição |
| :--- | :--- |
| `search_academic_papers` | Busca artigos científicos no Crossref e SciELO por palavras-chave com DOI e resumo. |
| `fetch_bibtex_by_doi` | Baixa o BibTeX oficial por DOI e salva no `.bib` sem duplicar. |
| `validate_citations` | Cruza citações do texto (LaTeX, Markdown, Typst) com o `.bib` e aponta órfãs e violações. |
| `check_structure` | Valida conformidade estrutural da NBR 14724 e numeração da NBR 6024. |
| `compile_tcc` | Compila o projeto (LaTeX, Markdown, Typst) com ciclo multi-pass e relatório de erros. |
| `read_pdf_section` | Extrai texto e estatísticas de páginas ou seções de um arquivo PDF via `pypdf`. |
| `clean_bibtex_file` | Higieniza arquivos BibTeX (UTF-8 estrito, meses ABNT, campos obrigatórios). |
| `format_citation` | Gera citação direta ou indireta conforme a NBR 10520:2023 em MD, LaTeX ou Typst. |
| `format_reference` | Gera referência bibliográfica na NBR 6023:2018 com destaque exclusivo no título. |
| `analyze_tone` | Detecta 1ª pessoa, expressões coloquiais e juízos de valor com nota de rigor científico. |
| `generate_academic_resumo` | Gera Resumo ou Abstract (150-500 palavras) com palavras-chave formatadas (NBR 6028). |

---

## 💬 Catálogo de Prompts Nativos

- **`revisar_capitulo(texto, foco)`**: Realiza uma revisão minuciosa com nota de rigor (0 a 100), pontos fortes, desvios apontados e reescrita recomendada.
- **`formatar_citacao(trecho, autor, ano, pagina, tipo)`**: Fornece o código exato da citação para LaTeX (`\begin{citacao}` ou aspas), Markdown ou Typst.
- **`simular_banca(projeto_path)`**: Simula a arguição da banca examinadora, avaliando coerência metodológica, aderência dos objetivos e as 3 perguntas mais difíceis da defesa.

---

## 📚 Catálogo de Recursos Nativos (Resources)

- `abnt://guia/citacoes`: Resumo completo das diretrizes da NBR 10520:2023.
- `abnt://guia/estrutura`: Checklist dos elementos pré-textuais, textuais e pós-textuais (NBR 14724:2011).
- `abnt://guia/referencias`: Regras para elaboração de referências bibliográficas (NBR 6023:2018).
- `abnt://template/latex`: Template funcional completo em LaTeX com abnTeX2.
- `abnt://template/typst`: Template funcional moderno em Typst com margens 3-3-2-2.
- `abnt://template/markdown`: Template em Markdown (Pandoc) com cabeçalho YAML e suporte a CSL.

---

## ⚠️ Atenção à NBR 10520:2023 (Fim da Caixa Alta)

> **AVISO IMPORTANTE:** A norma ABNT NBR 10520 foi atualizada em julho de 2023 e **revogou expressamente** a exigência de sobrenomes em CAIXA ALTA dentro de parênteses.
> 
> - ❌ **Incorreto (Norma antiga 2002):** `(SILVA, 2021, p. 15)` ou `(SANTOS; OLIVEIRA, 2020)`
> - ✅ **Correto (Norma vigente 2023):** `(Silva, 2021, p. 15)` ou `(Santos; Oliveira, 2020)`
> 
> O **ABNT Copilot MCP** fiscaliza ativamente esse vício de linguagem nas IAs e adota o padrão 2023 por padrão.

---

## 🧪 Testes Automatizados

O projeto conta com uma suíte de testes robusta utilizando `pytest`:

```bash
uv run pytest -v
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.
