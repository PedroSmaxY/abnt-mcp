"""Pilar 4: Dicas, Mentoria & Banca Examinadora.

Busca de Literatura Científica (Crossref/SciELO), Obtenção e Higienização de BibTeX por DOI (NBR 6023)
e Simulador de Banca Examinadora.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any
import requests

from abnt_mcp.config import DEFAULT_USER_AGENT, validate_safe_path
from abnt_mcp.models import AcademicPaper
from abnt_mcp.parsers.bibtex import (
    sanitize_bibtex_string,
    append_entry_if_absent,
    clean_latex_accents,
)
from abnt_mcp.pillars.diagnostics import check_project_structure, analyze_scientific_tone


def search_academic_literature(
    query: str,
    source: str = "all",
    limit: int = 5
) -> list[dict[str, Any]]:
    """
    Busca artigos científicos recentes com DOI, autores, periódico e resumo
    nas bases Crossref e SciELO.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    results: list[dict[str, Any]] = []
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json"
    }

    # 1. Busca no Crossref
    if source.lower() in {"all", "crossref"}:
        try:
            url = f"https://api.crossref.org/works?query={requests.utils.quote(clean_query)}&rows={limit}&sort=relevance"
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                for item in items:
                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else "Sem título"
                    
                    # Autores
                    author_list = []
                    for a in item.get("author", []):
                        family = a.get("family", "")
                        given = a.get("given", "")
                        if family and given:
                            author_list.append(f"{family}, {given}")
                        elif family:
                            author_list.append(family)

                    # Ano
                    year = None
                    published = item.get("published") or item.get("published-print") or item.get("published-online")
                    if published and "date-parts" in published:
                        year = published["date-parts"][0][0]

                    # Periódico / Container
                    container = item.get("container-title", [])
                    journal = container[0] if container else None

                    doi = item.get("DOI")
                    link = f"https://doi.org/{doi}" if doi else item.get("URL")

                    # Resumo (limpa tags XML comuns como <jats:p>)
                    abstract_raw = item.get("abstract", "")
                    abstract = re.sub(r"<[^>]+>", "", abstract_raw).strip() if abstract_raw else None

                    paper = AcademicPaper(
                        title=title,
                        authors=author_list,
                        year=year,
                        journal=journal,
                        doi=doi,
                        url=link,
                        abstract=abstract[:400] + "..." if abstract and len(abstract) > 400 else abstract,
                        source="Crossref"
                    )
                    results.append(paper.model_dump())
        except Exception:
            pass

    # 2. Busca com filtro para artigos da base SciELO (via Crossref publisher/filter)
    if source.lower() in {"all", "scielo"} and len(results) < limit:
        try:
            needed = limit - len(results)
            scielo_url = f"https://api.crossref.org/works?query={requests.utils.quote(clean_query)}&filter=publisher-name:SciELO&rows={needed}"
            resp = requests.get(scielo_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("message", {}).get("items", [])
                for item in items:
                    doi = item.get("DOI")
                    if any(r.get("doi") == doi for r in results):
                        continue  # evita duplicados

                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else "Sem título"
                    
                    author_list = []
                    for a in item.get("author", []):
                        family = a.get("family", "")
                        given = a.get("given", "")
                        author_list.append(f"{family}, {given}" if given else family)

                    year = None
                    published = item.get("published")
                    if published and "date-parts" in published:
                        year = published["date-parts"][0][0]

                    container = item.get("container-title", [])
                    journal = container[0] if container else "SciELO"

                    results.append(AcademicPaper(
                        title=title,
                        authors=author_list,
                        year=year,
                        journal=journal,
                        doi=doi,
                        url=f"https://doi.org/{doi}" if doi else item.get("URL"),
                        abstract=None,
                        source="SciELO (Crossref)"
                    ).model_dump())
        except Exception:
            pass

    return results[:limit]


def fetch_bibtex_by_doi_service(doi: str, bib_file: str | None = None) -> dict[str, Any]:
    """
    Baixa a entrada BibTeX oficial pelo DOI via negociação de conteúdo (doi.org)
    e opcionalmente anexa ao arquivo .bib do projeto sem duplicar.
    """
    clean_doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip())
    clean_doi = re.sub(r"^doi:\s*", "", clean_doi, flags=re.IGNORECASE)

    url = f"https://doi.org/{clean_doi}"
    headers = {
        "Accept": "application/x-bibtex; charset=utf-8",
        "User-Agent": DEFAULT_USER_AGENT,
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {
                "success": False,
                "doi": clean_doi,
                "error": f"Servidor DOI retornou código HTTP {resp.status_code}. Verifique se o DOI é válido.",
            }

        bibtex_text = resp.content.decode("utf-8", errors="replace")
        bibtex_clean = clean_latex_accents(bibtex_text)

        # Se caminho do arquivo foi informado, anexa com segurança
        file_result = None
        if bib_file:
            path = Path(bib_file)
            file_result = append_entry_if_absent(path, bibtex_clean)

        return {
            "success": True,
            "doi": clean_doi,
            "bibtex": bibtex_clean,
            "saved_to_file": bib_file if file_result and file_result.get("inserted") else None,
            "file_status": file_result.get("message") if file_result else None,
        }

    except requests.Timeout:
        return {
            "success": False,
            "doi": clean_doi,
            "error": "Tempo limite de conexão excedido ao consultar o resolvedor de DOI.",
        }
    except Exception as exc:
        return {
            "success": False,
            "doi": clean_doi,
            "error": f"Erro ao obter BibTeX: {exc}",
        }


def clean_bibtex_file_service(bib_path: str, output_path: str | None = None) -> dict[str, Any]:
    """
    Higieniza um arquivo BibTeX segundo a NBR 6023:
    corrige meses abreviados, limpa acentos corrompidos, verifica campos obrigatórios,
    cria backup automático (.abnt-mcp/backups/) quando sobrescreve arquivo existente
    e salva o arquivo em UTF-8 estrito.
    """
    in_path = validate_safe_path(bib_path)
    if not in_path.is_file():
        raise FileNotFoundError(f"Arquivo BibTeX não encontrado: {in_path}")

    content = in_path.read_text(encoding="utf-8", errors="replace")
    cleaned_text, warnings = sanitize_bibtex_string(content)

    out_file = validate_safe_path(output_path) if output_path else in_path
    out_file.parent.mkdir(parents=True, exist_ok=True)

    backup_path_str: str | None = None
    if out_file.is_file():
        backup_dir = out_file.parent / ".abnt-mcp" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"{out_file.name}.bak"
        backup_file.write_text(out_file.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        backup_path_str = str(backup_file)

    out_file.write_text(cleaned_text, encoding="utf-8")

    return {
        "success": True,
        "input_file": str(in_path),
        "output_file": str(out_file),
        "backup_path": backup_path_str,
        "corrections_made": warnings,
        "total_corrections": len(warnings),
        "message": f"Arquivo BibTeX higienizado com sucesso ({len(warnings)} correções/avisos).",
    }


def simulate_banca_examination(project_path: str) -> dict[str, Any]:
    """
    Simula uma banca examinadora de TCC/Dissertação:
    - Analisa a estrutura e consistência entre Objetivos e Conclusão (com suporte a SDD abnt.spec.json).
    - Avalia replicabilidade e fundamentação metodológica.
    - Identifica deficiências na literatura e tom da redação.
    - Formula perguntas desafiadoras que a banca fará.
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho não encontrado: {path}")

    # 1. Checagem estrutural
    structure_res = check_project_structure(path)

    # 2. Coleta texto completo (ignorando SPEC.md)
    all_text = ""
    if path.is_file():
        all_text = path.read_text(encoding="utf-8", errors="replace")
    else:
        for f in path.rglob("*"):
            if f.is_file() and f.suffix.lower() in {".tex", ".md", ".typ"} and f.name != "SPEC.md":
                all_text += "\n" + f.read_text(encoding="utf-8", errors="replace")

    # 3. Análise de tom científico
    tone_res = analyze_scientific_tone(all_text)

    # 4. Verifica se há manifesto SDD (abnt.spec.json) para auditoria determinística de objetivos
    project_dir = path if path.is_dir() else path.parent
    spec_file = project_dir / "abnt.spec.json"
    spec_audit = None
    if spec_file.is_file():
        try:
            from abnt_mcp.pillars.spec import audit_project_against_spec
            spec_audit = audit_project_against_spec(path, spec_file)
        except Exception:
            spec_audit = None

    # 5. Avaliação de eixos da banca
    axes_scores: dict[str, int] = {}

    # Eixo 1: Alinhamento Objetivos vs Conclusão
    if spec_audit is not None:
        axes_scores["Alinhamento Tema-Objetivos-Conclusão"] = spec_audit.objectives_fulfillment_rate
    else:
        has_obj = bool(re.search(r"objetivo", all_text, re.IGNORECASE))
        has_concl = bool(re.search(r"(conclus[ãa]o|considera[çc][õo]es finais)", all_text, re.IGNORECASE))
        axes_scores["Alinhamento Tema-Objetivos-Conclusão"] = 85 if (has_obj and has_concl) else 50

    # Eixo 2: Rigor e Replicabilidade Metodológica
    has_method = bool(re.search(r"metodologia|materiais e m[ée]todos", all_text, re.IGNORECASE))
    axes_scores["Rigor e Replicabilidade Metodológica"] = 80 if has_method else 45

    # Eixo 3: Fundamentação Teórica
    has_bib = bool(re.search(r"refer[êe]ncias|bibliography", all_text, re.IGNORECASE))
    axes_scores["Fundamentação Teórica e Literatura"] = 90 if has_bib else 40

    # Eixo 4: Normas ABNT
    axes_scores["Conformidade com Normas ABNT"] = structure_res.compliance_score

    # Eixo 5: Clareza e Redação Científica
    axes_scores["Redação e Impessoalidade"] = tone_res.score

    overall_grade = sum(axes_scores.values()) // len(axes_scores)

    # Perguntas típicas que a banca fará (enriquecidas com objetivos órfãos da spec quando presentes)
    banca_questions: list[dict[str, str]] = [
        {
            "examinador": "Prof. Avaliador Metodológico",
            "pergunta": "Como você garante que o método descrito no trabalho pode ser reproduzido de forma independente por outro pesquisador sem ambiguidades?",
            "motivo": "A metodologia precisa detalhar instrumentos, parâmetros e passos procedimentais."
        },
        {
            "examinador": "Prof. Especialista na Área",
            "pergunta": "Os objetivos específicos propostos na introdução foram todos plenamente respondidos nas considerações finais, ou restaram lacunas não discutidas?",
            "motivo": "Muitos trabalhos esquecem de correlacionar cada objetivo específico diretamente com os resultados obtidos."
        },
        {
            "examinador": "Prof. Revisor Teórico",
            "pergunta": "Quais são as principais limitações do seu estudo e quais ameaças à validade interna e externa foram identificadas?",
            "motivo": "Trabalhos sólidos reconhecem abertamente suas próprias limitações metodológicas e amostrais."
        }
    ]

    if spec_audit is not None:
        for obj_item in spec_audit.objectives_audit:
            if obj_item.status != "fulfilled":
                banca_questions.insert(
                    0,
                    {
                        "examinador": f"Presidente da Banca (Auditoria SDD - {obj_item.id})",
                        "pergunta": (
                            f"Na sua especificação científica ({obj_item.id}), você prometeu: '{obj_item.description}'. "
                            "Por que este objetivo específico não foi explicitamente comprovado e respondido na Conclusão?"
                        ),
                        "motivo": obj_item.feedback,
                    },
                )

    veredito = "APROVADO COM DISTINÇÃO" if overall_grade >= 90 else (
        "APROVADO COM RESSALVAS (REVISÃO NECESSÁRIA)" if overall_grade >= 70 else "NECESSITA REFORMULAÇÃO PROFUNDA"
    )

    return {
        "veredito": veredito,
        "nota_global": overall_grade,
        "pontuacao_por_eixo": axes_scores,
        "estrutura_abnt": {
            "conforme": structure_res.is_valid,
            "itens_ausentes": structure_res.missing_mandatory,
        },
        "redacao": {
            "nota": tone_res.score,
            "total_desvios": tone_res.issues_count,
        },
        "spec_alignment": (
            {
                "has_spec": True,
                "spec_compliance_score": spec_audit.spec_compliance_score,
                "objectives_fulfillment_rate": spec_audit.objectives_fulfillment_rate,
                "unfulfilled_objectives": [
                    o.id for o in spec_audit.objectives_audit if o.status != "fulfilled"
                ],
            }
            if spec_audit is not None
            else {"has_spec": False}
        ),
        "perguntas_da_banca": banca_questions,
        "principais_recomendacoes": [
            "Confronte explicitamente os resultados obtidos com os objetivos específicos na Conclusão.",
            "Certifique-se de que cada parágrafo com afirmações conceituais cite uma fonte (NBR 10520).",
            "Elimine construções em 1ª pessoa no texto e use voz passiva sintética.",
        ]
    }
