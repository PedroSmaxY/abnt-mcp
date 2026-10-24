"""Configuração e fixtures globais para pytest."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Retorna o diretório de fixtures de teste."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_bib_content() -> str:
    """Conteúdo BibTeX de exemplo com acentos e meses variados."""
    return """
@article{silva2023,
    title = {Avanços em inteligência artificial e processamento de linguagem natural},
    author = {Silva, Carlos and Souza, Mariana},
    journal = {Revista Brasileira de Computação},
    year = {2023},
    volume = {34},
    number = {2},
    pages = {45--62},
    month = {mai.},
    doi = {10.1109/RBC.2023.01}
}

@book{oliveira2022,
    title = {Metodologia Científica Aplicada},
    subtitle = {guia prático para pós-graduandos},
    author = {Oliveira, Roberto},
    publisher = {Atlas},
    year = {2022},
    address = {São Paulo},
    edition = {3. ed.}
}
"""


@pytest.fixture
def sample_tex_content() -> str:
    """Conteúdo LaTeX de exemplo estruturado."""
    return r"""
\documentclass{abntex2}
\begin{document}
\imprimircapa
\imprimirfolhaderosto

\begin{resumo}
Este estudo analisa o impacto da inteligência artificial no suporte a trabalhos acadêmicos no Brasil. O objetivo geral consiste em mapear a conformidade das regras ABNT com analisadores sintáticos. Utilizou-se como metodologia a aplicação de testes unitários automatizados sobre corpora textuais de monografias e dissertações. Os resultados obtidos indicam uma taxa de acerto superior a noventa por cento na detecção de inadequações tipográficas e de autoria. Conclui-se que o uso de ferramentas de suporte eleva a qualidade dos trabalhos e reduz o retrabalho em bancas examinadoras.

\textbf{Palavras-chave}: Normas ABNT; Citações; Inteligência Artificial; Model Context Protocol.
\end{resumo}

\begin{abstract}
This research explores the application of context protocol servers to automate Brazilian academic formatting standards. The primary goal is to ensure full compliance with ABNT regulations.

\textbf{Keywords}: ABNT Standards; Citations; Artificial Intelligence; Model Context Protocol.
\end{abstract}

\tableofcontents

\chapter{Introdução}
O desenvolvimento de pesquisas científicas requer conformidade com as normas institucionais.
Segundo \citeonline{silva2023}, a automação bibliográfica previne falhas recorrentes.

\chapter{Metodologia}
Adotou-se uma abordagem experimental fundamentada em análise de código-fonte.

\chapter{Conclusão}
Os objetivos gerais e específicos delineados na introdução foram cumpridos integralmente.

\bibliography{referencias}
\end{document}
"""
