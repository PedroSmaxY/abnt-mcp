"""Template Typst pré-configurado conforme as normas ABNT NBR 14724."""

TYPST_TEMPLATE = r"""// =============================================================================
// TEMPLATE ABNT EM TYPST (NBR 14724 / NBR 10520 / NBR 6023)
// =============================================================================

#set document(title: "Título do Trabalho Acadêmico", author: "Nome do Autor")

// Configurações Físicas: Papel A4 e Margens 3-3-2-2 (Superior 3cm, Esquerda 3cm, Inferior 2cm, Direita 2cm)
#set page(
  paper: "a4",
  margin: (top: 3cm, left: 3cm, bottom: 2cm, right: 2cm),
  header: locate(loc => {
    // A numeração de página só aparece a partir da parte textual (Introdução)
    let page_num = loc.page()
    if page_num > 3 [
      #align(right)[#text(size: 10pt)[#page_num]]
    ]
  })
)

// Tipografia: Arial ou Times New Roman, Tamanho 12pt, Espaçamento 1.5x, Recuo 1.25cm
#set text(font: "Times New Roman", size: 12pt, lang: "pt", region: "BR")
#set par(justify: true, leading: 1.5em, first-line-indent: 1.25cm)

// Formatação de Títulos (NBR 6024)
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(1cm)
  text(weight: "bold")[#upper(it)]
  v(1cm)
}

// -----------------------------------------------------------------------------
// ELEMENTOS PRÉ-TEXTUAIS
// -----------------------------------------------------------------------------

// Capa (Obrigatório)
#align(center)[
  #text(weight: "bold", size: 12pt)[UNIVERSIDADE EXEMPLO DO BRASIL]\
  #text(size: 12pt)[FACULDADE DE TECNOLOGIA]\
  #text(size: 12pt)[CURSO DE CIÊNCIA DA COMPUTAÇÃO]

  #v(5cm)
  #text(weight: "bold", size: 14pt)[NOME COMPLETO DO AUTOR]

  #v(4cm)
  #text(weight: "bold", size: 16pt)[TÍTULO DO TRABALHO: SUBTÍTULO]

  #v(1fr)
  #text(size: 12pt)[CIDADE - UF\ 2026]
]

#pagebreak()

// Folha de Rosto (Obrigatório)
#align(center)[
  #text(size: 12pt)[NOME COMPLETO DO AUTOR]
  #v(4cm)
  #text(weight: "bold", size: 14pt)[TÍTULO DO TRABALHO: SUBTÍTULO]
  
  #v(2cm)
  #align(right)[
    #block(width: 50%)[
      #set text(size: 10pt)
      #set par(leading: 1em, justify: true)
      Trabalho de Conclusão de Curso apresentado ao Curso de Ciência da Computação da Universidade Exemplo como requisito parcial para obtenção do título de Bacharel.\
      \
      Orientador: Prof. Dr. Nome do Orientador
    ]
  ]

  #v(1fr)
  #text(size: 12pt)[CIDADE - UF\ 2026]
]

#pagebreak()

// Resumo (Obrigatório - NBR 6028)
#align(center)[#text(weight: "bold")[RESUMO]]
#v(1cm)
#set par(first-line-indent: 0cm, justify: true)
Este trabalho sintetiza o desenvolvimento de ferramentas baseadas no Model Context Protocol. Apresenta-se o objetivo de aprimorar a automação de escrita técnica segundo a NBR 14724. Utilizou-se como metodologia a análise de conformidade de código e testes automatizados. Os resultados demonstram redução significativa de erros de citação e inconsistências tipográficas. Conclui-se que a padronização orientada a ferramentas inteligentes potencializa o rigor e a produtividade científica.

#v(1cm)
*Palavras-chave:* Normas ABNT; Model Context Protocol; Escrita Científica; Automação Acadêmica.

#pagebreak()

// Sumário (Obrigatório - NBR 6027)
#outline(title: [SUMÁRIO], indent: auto)

#pagebreak()

// -----------------------------------------------------------------------------
// ELEMENTOS TEXTUAIS
// -----------------------------------------------------------------------------
#set par(first-line-indent: 1.25cm)

= Introdução

A produção de trabalhos científicos exige rigor metodológico e estrita observância às normas da ABNT. Conforme destaca @silva2023, o uso de automação reduz falhas em citações e referências bibliográficas.

= Metodologia

Descrevem-se aqui os passos do estudo, os critérios de amostragem e as ferramentas computacionais empregadas na análise dos dados.

= Resultados e Discussão

Os experimentos realizados evidenciaram alta taxa de precisão nas verificações gramaticais e estruturais.

= Conclusão

Os objetivos estabelecidos foram integralmente cumpridos, oferecendo uma base reproduzível para futuras pesquisas na área de inteligência artificial aplicada.

// -----------------------------------------------------------------------------
// ELEMENTOS PÓS-TEXTUAIS
// -----------------------------------------------------------------------------

#bibliography("referencias.bib", title: "REFERÊNCIAS", style: "associacao-brasileira-de-normas-tecnicas")
"""


def get_typst_template() -> str:
    """Retorna o template Typst para ABNT."""
    return TYPST_TEMPLATE.strip()
