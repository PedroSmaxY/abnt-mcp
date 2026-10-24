"""Template Markdown (Pandoc) estruturado para trabalhos acadêmicos no padrão ABNT."""

MARKDOWN_TEMPLATE = r"""---
title: "Título do Trabalho Acadêmico"
subtitle: "Subtítulo da Pesquisa"
author: "Nome Completo do Autor"
date: "2026"
institution: "Universidade Exemplo do Brasil"
department: "Faculdade de Tecnologia"
course: "Bacharelado em Ciência da Computação"
advisor: "Prof. Dr. Nome do Orientador"
bibliography: referencias.bib
csl: associacao-brasileira-de-normas-tecnicas.csl
geometry: "top=3cm,bottom=2cm,left=3cm,right=2cm,a4paper"
fontsize: 12pt
linestretch: 1.5
indent: true
lang: pt-BR
---

<!-- ======================================================= -->
<!-- ELEMENTOS PRÉ-TEXTUAIS (NBR 14724)                     -->
<!-- ======================================================= -->

# RESUMO {-}

O resumo é um elemento obrigatório redigido em parágrafo único, justificado e sem recuo de primeira linha, compreendendo de 150 a 500 palavras. Deve apresentar de maneira objetiva o contexto, o objetivo geral, o método de investigação adotado, os principais achados quantitativos ou qualitativos e a conclusão alcançada.

**Palavras-chave:** Normas ABNT; Pandoc; Pesquisa Científica; Citações.

\newpage

# ABSTRACT {-}

The abstract is a mandatory element composed of a single justified paragraph without first-line indentation, ranging from 150 to 500 words. It outlines the context, the main research question, the methodology used, primary findings, and the resulting conclusions.

**Keywords:** ABNT Standards; Pandoc; Scientific Research; Citations.

\newpage

<!-- ======================================================= -->
<!-- ELEMENTOS TEXTUAIS                                      -->
<!-- ======================================================= -->

# 1 INTRODUÇÃO

Este capítulo introduz o tema de estudo, delineando a relevância acadêmica e prática da investigação. Conforme destacado por [@silva2023, p. 12], a utilização de ferramentas estruturadas agiliza a padronização bibliográfica.

## 1.1 OBJETIVOS

### 1.1.1 Objetivo Geral

Analisar a aplicabilidade de servidores de contexto para padronização acadêmica.

### 1.1.2 Objetivos Específicos

- Mapear as principais normas da ABNT aplicáveis a trabalhos de pós-graduação e graduação;
- Construir analisadores sintáticos e linters automatizados;
- Validar a precisão das ferramentas em documentos reais.

# 2 METODOLOGIA

Descreve-se os procedimentos técnicos empregados, o universo de análise e os critérios de validação adotados no experimento.

# 3 RESULTADOS E DISCUSSÃO

Apresentam-se os dados coletados de maneira estruturada, com gráficos e tabelas devidamente identificados com título no topo e fonte no rodapé conforme a norma do IBGE.

# 4 CONSIDERAÇÕES FINAIS

Conclui-se que a automação rigorosa elimina falhas recorrentes de citação e eleva a qualidade dos trabalhos acadêmicos submetidos a bancas examinadoras.

<!-- ======================================================= -->
<!-- ELEMENTOS PÓS-TEXTUAIS                                  -->
<!-- ======================================================= -->

# REFERÊNCIAS {-}

<!-- As referências serão geradas automaticamente pelo Pandoc via --citeproc -->
"""


def get_markdown_template() -> str:
    """Retorna o template Markdown (Pandoc) para ABNT."""
    return MARKDOWN_TEMPLATE.strip()
