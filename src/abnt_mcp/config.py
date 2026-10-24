"""Configurações, padrões de regex e constantes para o ABNT Copilot MCP."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import re

SERVER_NAME = "abnt-mcp"
SERVER_VERSION = "0.1.0"
DEFAULT_USER_AGENT = f"{SERVER_NAME}/{SERVER_VERSION} (mailto:abnt-copilot@example.com)"


def get_current_year() -> int:
    """Retorna o ano corrente dinamicamente (evita datas hardcoded)."""
    return datetime.now().year


def get_default_author_source() -> str:
    """Retorna a indicação de fonte autoral padrão com o ano corrente."""
    return f"Elaborado pelo autor ({get_current_year()})."


def validate_safe_path(target_path: str | Path, base_dir: str | Path | None = None) -> Path:
    """
    Valida caminhos de arquivo contra caracteres nulos e path traversal fora de base_dir.
    """
    raw_str = str(target_path)
    if "\x00" in raw_str or not raw_str.strip():
        raise ValueError(f"Caminho inválido ou malformado: '{target_path}'")

    resolved = Path(target_path).expanduser().resolve()
    if base_dir is not None:
        base_resolved = Path(base_dir).expanduser().resolve()
        try:
            resolved.relative_to(base_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Operação bloqueada por segurança (Path Traversal): '{resolved}' está fora do diretório base '{base_resolved}'."
            ) from exc
    return resolved

# Catálogo de Regras Normativas Canônicas (Spec-Driven Development)
# Sincronizado com specs/01-normative-catalog.spec.md
NORMATIVE_RULES: dict[str, dict[str, str]] = {
    "NBR14724-R01": {
        "standard": "ABNT NBR 14724:2011",
        "clause": "Seção 4.2",
        "title": "Elementos pré-textuais, textuais e pós-textuais obrigatórios de monografias",
        "severity": "error",
    },
    "NBR14724-R02": {
        "standard": "ABNT NBR 14724:2011",
        "clause": "Seção 5.3",
        "title": "Paginação física: contagem na Folha de Rosto e impressão arábica a partir da Introdução",
        "severity": "critical",
    },
    "NBR14724-R03": {
        "standard": "ABNT NBR 14724:2011",
        "clause": "Seção 5.8",
        "title": "Ilustrações com título superior, chamada textual prévia e fonte inferior",
        "severity": "warning",
    },
    "NBR6022-R01": {
        "standard": "ABNT NBR 6022:2018",
        "clause": "Seção 5",
        "title": "Estrutura de artigo científico periódico (título, resumo, introdução, desenvolvimento, conclusão e referências)",
        "severity": "error",
    },
    "NBR10520-R01": {
        "standard": "ABNT NBR 10520:2023",
        "clause": "Seção 4.2",
        "title": "Sistema autor-data entre parênteses em caixa mista (Silva, 2023), vedada CAIXA ALTA",
        "severity": "error",
    },
    "NBR10520-R02": {
        "standard": "ABNT NBR 10520:2023",
        "clause": "Seção 7.1",
        "title": "Consistência cruzada estrita entre citações no texto e referências no arquivo .bib",
        "severity": "error",
    },
    "NBR10520-R03": {
        "standard": "ABNT NBR 10520:2023",
        "clause": "Seções 5.2 / 5.3",
        "title": "Formatação de citações diretas curtas (<=3 linhas, aspas) e longas (>3 linhas, recuo de 4 cm, fonte 10)",
        "severity": "error",
    },
    "NBR6023-R01": {
        "standard": "ABNT NBR 6023:2018",
        "clause": "Anexo A (A.1)",
        "title": "Abreviatura padronizada de meses (três caracteres com ponto, exceto 'maio' por extenso sem ponto)",
        "severity": "warning",
    },
    "NBR6023-R02": {
        "standard": "ABNT NBR 6023:2018",
        "clause": "Seção 6.2",
        "title": "Alinhamento à margem esquerda e destaque tipográfico exclusivo no título principal",
        "severity": "error",
    },
    "NBR6024-R01": {
        "standard": "ABNT NBR 6024:2012",
        "clause": "Seção 4.1",
        "title": "Numeração progressiva das seções sem ponto final após o último algarismo",
        "severity": "warning",
    },
    "NBR6027-R01": {
        "standard": "ABNT NBR 6027:2012",
        "clause": "Seção 4",
        "title": "Sumário restrito aos elementos textuais e pós-textuais (vedada inclusão de elementos pré-textuais)",
        "severity": "error",
    },
    "NBR6028-R01": {
        "standard": "ABNT NBR 6028:2021",
        "clause": "Seção 3.3",
        "title": "Resumo em parágrafo único contínuo na 3ª pessoa e palavras-chave separadas por ponto e vírgula",
        "severity": "warning",
    },
    "IBGE1993-R01": {
        "standard": "Normas Tabulares IBGE (1993)",
        "clause": "Seção 3.1",
        "title": "Distinção entre Tabela (dados quantitativos, laterais abertas) e Quadro (dados qualitativos, bordas fechadas)",
        "severity": "error",
    },
}

# Abreviatura oficial de meses segundo a NBR 6023:2018 (atenção ao 'maio' sem ponto!)
ABNT_MONTHS: dict[str, str] = {
    "1": "jan.",
    "01": "jan.",
    "jan": "jan.",
    "january": "jan.",
    "janeiro": "jan.",
    "2": "fev.",
    "02": "fev.",
    "feb": "fev.",
    "february": "fev.",
    "fevereiro": "fev.",
    "3": "mar.",
    "03": "mar.",
    "mar": "mar.",
    "march": "mar.",
    "março": "mar.",
    "4": "abr.",
    "04": "abr.",
    "apr": "abr.",
    "april": "abr.",
    "abril": "abr.",
    "5": "maio",
    "05": "maio",
    "may": "maio",
    "mai": "maio",
    "maio": "maio",
    "6": "jun.",
    "06": "jun.",
    "jun": "jun.",
    "june": "jun.",
    "junho": "jun.",
    "7": "jul.",
    "07": "jul.",
    "jul": "jul.",
    "july": "jul.",
    "julho": "jul.",
    "8": "ago.",
    "08": "ago.",
    "aug": "ago.",
    "august": "ago.",
    "agosto": "ago.",
    "9": "set.",
    "09": "set.",
    "sep": "set.",
    "september": "set.",
    "setembro": "set.",
    "10": "out.",
    "oct": "out.",
    "october": "out.",
    "outubro": "out.",
    "11": "nov.",
    "november": "nov.",
    "novembro": "nov.",
    "12": "dez.",
    "dec": "dez.",
    "december": "dez.",
    "dezembro": "dez.",
}

# Regex para detectar autores em CAIXA ALTA entre parênteses (norma antiga NBR 10520:2002)
# Na norma 2023, deve ser (Silva, 2021) e não (SILVA, 2021)
RE_UPPERCASE_CITATION = re.compile(
    r"\(([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,})*(?:;\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,})*)*),\s*(\d{4}[^\)]*)\)"
)

# Regex para ponto final indevido no indicativo numérico de seções (NBR 6024:2012)
# Incorreto: "1.1. Introdução" ou "# 1.1. Introdução"
# Correto: "1.1 Introdução" ou "# 1.1 Introdução"
RE_INVALID_SECTION_DOT = re.compile(
    r"^[ \t]*(?:#+\s*)?(\d+(?:\.\d+)*)\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ].*)$", re.MULTILINE
)

# Regex para maio com ponto (incorreto pela NBR 6023)
RE_MAI_WITH_DOT = re.compile(r"\bmai\.(?!\w)", re.IGNORECASE)

# Lista de termos e pronomes em 1ª pessoa
FIRST_PERSON_PRONOUNS: set[str] = {
    "eu", "me", "mim", "comigo", "meu", "minha", "meus", "minhas",
    "nós", "nos", "conosco", "nosso", "nossa", "nossos", "nossas"
}

# Verbos comuns em 1ª pessoa do singular e plural (passado, presente, futuro)
FIRST_PERSON_VERBS: set[str] = {
    # Singular
    "fiz", "faço", "farei", "analisei", "analiso", "analisarei",
    "observei", "observo", "observarei", "concluo", "concluí", "concluirei",
    "acredito", "acreditei", "acreditarei", "percebo", "percebi", "perceberei",
    "verifico", "verifiquei", "verificarei", "identifico", "identifiquei", "identificarei",
    "utilizei", "utilizo", "utilizarei", "propus", "proponho", "proporei",
    "desenvolvi", "desenvolvo", "desenvolverei", "notei", "noto", "notarei",
    "considerei", "considero", "considerarei", "estudei", "estudo", "estudarei",
    "pretendo", "pretendi", "pretenderei", "apresento", "apresentei",
    # Plural
    "fizemos", "faremos", "analisamos", "analisaremos",
    "observamos", "observaremos", "concluímos", "concluiremos",
    "acreditamos", "acreditaremos", "percebemos", "perceberemos",
    "verificamos", "verificaremos", "identificamos", "identificaremos",
    "utilizamos", "utilizaremos", "propusemos", "proporemos",
    "desenvolvemos", "desenvolveremos", "notamos", "notaremos",
    "consideramos", "consideraremos", "estudamos", "estudaremos",
    "pretendemos", "pretenderemos", "apresentamos", "apresentaremos",
}

# Juízos de valor sem fundamentação e termos dogmáticos
VALUE_JUDGMENTS: list[tuple[str, str]] = [
    ("obviamente", "Substitua por dados empíricos ou referência; o que é 'óbvio' requer demonstração na ciência."),
    ("claramente", "Evite advérbios opinativos. Deixe que os dados demonstrem a conclusão."),
    ("sem dúvida", "Na ciência impera a dúvida metódica; utilize 'evidências apontam' ou cite a fonte."),
    ("sem sombra de dúvida", "Afirmação categórica sem rigor científico."),
    ("indubitavelmente", "Evite certezas absolutas sem citação ou prova matemática."),
    ("com certeza", "Linguagem informal e assertiva sem respaldo."),
    ("é evidente", "Se fosse evidente não necessitaria de fundamentação; apresente a fonte."),
    ("notoriamente", "Apelo ao senso comum; fundamente com citação bibliográfica."),
    ("comprovadamente", "Só utilize se acompanhar a citação comprobatória direta."),
    ("perfeito", "Juízo de valor qualitativo excessivo."),
    ("maravilhoso", "Termo emotivo/qualificativo inadequado ao texto científico."),
    ("fantástico", "Tom hiperbólico desprovido de rigor técnico."),
    ("inquestionável", "No método científico, hipóteses são sempre falseáveis."),
    ("na minha opinião", "Trabalho científico fundamenta-se em fatos e literatura, não em opinião pessoal."),
    ("no meu ponto de vista", "Substitua pela constatação dos dados ou fundamentação teórica."),
    ("a meu ver", "Substitua por constatações impessoais."),
]

# Expressões coloquiais
COLLOQUIALISMS: list[tuple[str, str]] = [
    ("a gente", "Substitua pelo pronome impessoal 'se' ou terceira pessoa ('observa-se')."),
    ("pra caramba", "Expressão de gíria/informal inadequada."),
    ("bater o martelo", "Metáfora informal; use 'decidir', 'definir' ou 'concluir'."),
    ("dar um jeito", "Expressão informal; use 'solucionar' ou 'contornar a limitação'."),
    ("rolar", "Gíria informal; utilize 'ocorrer', 'acontecer' ou 'suceder'."),
    ("rolou", "Gíria informal; utilize 'ocorreu' ou 'aconteceu'."),
    ("ficar de olho", "Linguagem coloquial; utilize 'monitorar' ou 'acompanhar atentamente'."),
    ("por aí vai", "Expressão vaga; use 'entre outros' ou cite os itens pertinentes."),
    ("mais ou menos", "Imprecisão; forneça valores, faixas de incerteza ou margem de erro."),
    ("coisa", "Substantivo genérico vago; especifique o objeto, variável, fenômeno ou elemento."),
    ("coisas", "Termo genérico vago; especifique os elementos ou variáveis."),
    ("tipo assim", "Cacoete de linguagem coloquial."),
    ("troço", "Gíria genérica inadequada."),
    ("pegar pesado", "Metáfora coloquial; use 'ser rigoroso'."),
    ("tirar de letra", "Expressão coloquial inadequada."),
]
