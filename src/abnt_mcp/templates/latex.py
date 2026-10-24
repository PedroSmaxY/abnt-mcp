"""Template LaTeX pré-configurado com abnTeX2."""

ABNTEX2_TEMPLATE = r"""\documentclass[
    12pt,               % Tamanho da fonte
    openright,          % Capítulos começam em página ímpar
    oneside,            % Para impressão em apenas um lado da folha (anverso)
    a4paper,            % Tamanho do papel
    english,            % Idioma adicional para hifenação
    brazil              % Idioma principal do documento
]{abntex2}

% --- PACOTES BÁSICOS ---
\usepackage{cmap}                   % Mapeamento de caracteres especiais no PDF
\usepackage{lmodern}                % Fonte Latin Modern
\usepackage[T1]{fontenc}            % Codificação de fontes de 8 bits
\usepackage[utf8]{inputenc}         % Codificação de entrada UTF-8
\usepackage{indentfirst}            % Indenta o primeiro parágrafo de cada seção
\usepackage{color}                  % Controle de cores
\usepackage{graphicx}               % Inclusão de gráficos
\usepackage{microtype}              % Para melhorias de justificação
\usepackage{lipsum}                 % Para geração de texto dummy

% --- PACOTE DE CITAÇÕES ABNT ---
\usepackage[brazilian,hyperpageref]{backref}  % Páginas com a citação na bibliografia
\usepackage[alf]{abntex2cite}                 % Citações padrão autor-data (NBR 10520)

% --- CONFIGURAÇÕES DE PACOTES ---
\renewcommand{\backrefpagesname}{Citado na(s) página(s):~}
\renewcommand{\backref}{}
\renewcommand{\backrefalt}[4]{
    \ifcase #1 %
        Nenhuma citação no texto.%
    \or
        Citado na página #2.%
    \else
        Citado #1 vezes nas páginas #2.%
    \fi}%

% --- INFORMAÇÕES DO TRABALHO ---
\titulo{Título do Trabalho: Subtítulo do Trabalho}
\autor{Nome Completo do Autor}
\local{Cidade - UF}
\data{2026}
\orientador{Prof. Dr. Nome do Orientador}
\instituicao{%
  Universidade Exemplo do Brasil
  \par
  Faculdade de Tecnologia
  \par
  Curso de Graduação em Ciência da Computação}
\tipotrabalho{Trabalho de Conclusão de Curso (Graduação)}
\preambulo{Trabalho de Conclusão de Curso apresentado ao Curso de Ciência da Computação como requisito parcial para obtenção do título de Bacharel.}

% --- CONFIGURAÇÕES DE APARÊNCIA DO PDF FINAL ---
\definecolor{blue}{RGB}{41,5,195}
\makeatletter
\hypersetup{
    pdftitle={\@titulo}, 
    pdfauthor={\@autor},
    pdfsubject={\imprimirpreambulo},
    pdfcreator={LaTeX with abnTeX2},
    colorlinks=true,
    linkcolor=blue,
    citecolor=blue,
    filecolor=magenta,
    urlcolor=blue,
    bookmarksdepth=4
}
\makeatother

% --- COMPILAÇÃO DO ÍNDICE ---
\makeindex

% --- INÍCIO DO DOCUMENTO ---
\begin{document}
\selectlanguage{brazil}
\frenchspacing 

% ----------------------------------------------------------
% ELEMENTOS PRÉ-TEXTUAIS (NBR 14724)
% ----------------------------------------------------------

% Capa e Folha de Rosto (Obrigatórios)
\imprimircapa
\imprimirfolhaderosto

% Resumo na Língua Vernácula (Obrigatório)
\setlength{\absparsep}{18pt}
\begin{resumo}
 O resumo deve conter de 150 a 500 palavras em parágrafo único, justificado e sem recuo de primeira linha. Deve contextualizar a pesquisa, apresentar com clareza o objetivo geral, sintetizar a metodologia empregada, destacar os principais resultados quantitativos ou qualitativos alcançados e expor a conclusão principal obtida no estudo. Os verbos devem estar redigidos preferencialmente na terceira pessoa do singular em voz passiva sintética.
 
 \textbf{Palavras-chave}: Inteligência Artificial; Processamento de Linguagem Natural; Normas ABNT; Model Context Protocol.
\end{resumo}

% Resumo em Língua Estrangeira / Abstract (Obrigatório)
\begin{resumo}[Abstract]
 \begin{otherlanguage*}{english}
   The abstract must contain between 150 and 500 words in a single, justified paragraph without first-line indentation. It should establish the context, state the research objective, summarize the methodology, highlight significant results, and present the main conclusion. Verbs should ideally be written in the third person.
   
   \textbf{Keywords}: Artificial Intelligence; Natural Language Processing; ABNT Standards; Model Context Protocol.
 \end{otherlanguage*}
\end{resumo}

% Sumário (Obrigatório)
\pdfbookmark[0]{\contentsname}{toc}
\tableofcontents*
\cleardoublepage

% ----------------------------------------------------------
% ELEMENTOS TEXTUAIS
% ----------------------------------------------------------
\textual

\chapter{Introdução}
Apresentação do tema, justificativa da escolha, contextualização teórica, delimitação do problema e apresentação dos objetivos gerais e específicos da pesquisa.

Conforme aponta \citeonline{silva2023}, o avanço das ferramentas digitais proporcionou saltos na produtividade acadêmica.

\chapter{Metodologia}
Descrição detalhada dos procedimentos, materiais, instrumentos e etapas metodológicas seguidas para responder aos objetivos propostos.

\chapter{Resultados e Discussão}
Apresentação objetiva dos dados coletados, acompanhados de análise crítica e confronto com a literatura existente.

\chapter{Conclusão}
Síntese dos resultados, verificação do cumprimento dos objetivos, limitações da pesquisa e sugestões para trabalhos futuros.

% ----------------------------------------------------------
% ELEMENTOS PÓS-TEXTUAIS
% ----------------------------------------------------------
\postextual

% Referências Bibliográficas (Obrigatório)
\bibliography{referencias}

\end{document}
"""


def get_latex_template() -> str:
    """Retorna o template LaTeX completo configurado para ABNT."""
    return ABNTEX2_TEMPLATE.strip()
