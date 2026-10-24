"""Motor de Escrita Acadêmica Orientada a Especificações (SDD - Spec-Driven Development).

Gerencia a criação, leitura, sincronização Markdown e auditoria cruzada do manifesto
científico `abnt.spec.json` / `SPEC.md` em três camadas:
1. Perfil Normativo (ABNT NBR 14724 vs NBR 6022, referências mínimas, rigor científico)
2. Matriz Científica Rastreável (Problema, Objetivo Geral e Objetivos Específicos OBJ-XX)
3. Estrutura de Capítulos Planejados
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Literal

from abnt_mcp.config import NORMATIVE_RULES
from abnt_mcp.models import (
    ResearchSpec,
    NormativeProfile,
    SpecificObjective,
    PlannedChapter,
    ObjectiveAuditItem,
    ChapterAuditItem,
    SpecAuditResult,
)
from abnt_mcp.pillars.diagnostics import (
    check_project_structure,
    audit_citations_and_references,
    analyze_scientific_tone,
)


DEFAULT_PLANNED_CHAPTERS_TCC: list[dict[str, Any]] = [
    {"number": "1", "title": "Introdução", "min_words": 250, "min_citations": 1},
    {"number": "2", "title": "Fundamentação Teórica", "min_words": 500, "min_citations": 3},
    {"number": "3", "title": "Metodologia", "min_words": 300, "min_citations": 1},
    {"number": "4", "title": "Resultados e Discussão", "min_words": 400, "min_citations": 1},
    {"number": "5", "title": "Conclusão", "min_words": 200, "min_citations": 0},
]

DEFAULT_PLANNED_CHAPTERS_ARTIGO: list[dict[str, Any]] = [
    {"number": "1", "title": "Introdução", "min_words": 150, "min_citations": 1},
    {"number": "2", "title": "Metodologia", "min_words": 150, "min_citations": 1},
    {"number": "3", "title": "Resultados e Discussão", "min_words": 250, "min_citations": 1},
    {"number": "4", "title": "Considerações Finais", "min_words": 100, "min_citations": 0},
]


def render_spec_markdown(spec: ResearchSpec) -> str:
    """Renderiza uma visualização Markdown legível (`SPEC.md`) a partir de `ResearchSpec`."""
    lines = [
        f"# Especificação Científica (SDD): {spec.title}",
        "",
        f"- **Versão da Spec:** `{spec.spec_version}`",
        f"- **Autor(a):** {spec.author or 'Não informado'}",
        f"- **Tipo Documental:** `{spec.profile.document_type.upper()}`",
        f"- **Norma Estrutural:** `{spec.profile.standard}`",
        f"- **Instituição / Periódico:** {spec.profile.institution or 'Padrão Geral ABNT'}",
        f"- **Meta Mínima de Referências (`.bib`):** {spec.profile.min_references}",
        f"- **Meta de Rigor Científico:** {spec.profile.min_scientific_tone_score}/100",
        "",
        "---",
        "",
        "## 1. Matriz Científica",
        "",
        "### 1.1 Problema de Pesquisa",
        f"> {spec.research_problem}",
        "",
        "### 1.2 Objetivo Geral",
        f"{spec.general_objective}",
        "",
        "### 1.3 Síntese Metodológica",
        f"{spec.methodology_summary}",
        "",
        "### 1.4 Objetivos Específicos Rastreáveis",
        "",
        "| ID | Objetivo Específico | Palavras-Chave de Validação | Seção Alvo |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for obj in spec.specific_objectives:
        kw_str = ", ".join(f"`{k}`" for k in obj.keywords) if obj.keywords else "*Auto-extraídas*"
        sec_str = obj.target_section or "Desenvolvimento"
        lines.append(f"| `{obj.id}` | {obj.description} | {kw_str} | {sec_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Arquitetura de Capítulos Planejados",
        "",
        "| Seção | Título Planejado | Mín. Palavras | Mín. Citações |",
        "| :--- | :--- | :---: | :---: |",
    ])

    for ch in spec.planned_chapters:
        lines.append(f"| `{ch.number}` | {ch.title} | {ch.min_words} | {ch.min_citations} |")

    lines.append("")
    return "\n".join(lines)


def init_project_spec(
    project_path: str | Path,
    title: str,
    research_problem: str,
    general_objective: str,
    specific_objectives: list[dict[str, Any]],
    methodology_summary: str,
    document_type: Literal["tcc", "dissertacao", "tese", "artigo"] = "tcc",
    author: str | None = None,
    institution: str | None = None,
    min_references: int | None = None,
    planned_chapters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Inicializa e persiste o manifesto `abnt.spec.json` e o documento `SPEC.md`
    no diretório do projeto acadêmico.
    """
    path = Path(project_path)
    target_dir = path if (path.exists() and path.is_dir()) else (path.parent if path.suffix else path)
    target_dir.mkdir(parents=True, exist_ok=True)

    standard: Literal["ABNT_14724", "ABNT_6022"] = (
        "ABNT_6022" if document_type == "artigo" else "ABNT_14724"
    )
    effective_min_refs = (
        min_references
        if min_references is not None
        else (5 if document_type == "artigo" else 15)
    )

    parsed_objectives: list[SpecificObjective] = []
    for idx, raw_obj in enumerate(specific_objectives, start=1):
        obj_id = raw_obj.get("id") or f"OBJ-{idx:02d}"
        desc = raw_obj.get("description", "").strip()
        kws = raw_obj.get("keywords") or _extract_candidate_keywords(desc)
        parsed_objectives.append(
            SpecificObjective(
                id=obj_id,
                description=desc,
                keywords=kws,
                target_section=raw_obj.get("target_section"),
            )
        )

    raw_chapters = (
        planned_chapters
        if planned_chapters is not None
        else (DEFAULT_PLANNED_CHAPTERS_ARTIGO if document_type == "artigo" else DEFAULT_PLANNED_CHAPTERS_TCC)
    )
    parsed_chapters = [PlannedChapter(**ch) for ch in raw_chapters]

    profile = NormativeProfile(
        document_type=document_type,
        standard=standard,
        institution=institution,
        min_references=effective_min_refs,
    )

    spec = ResearchSpec(
        title=title,
        author=author,
        research_problem=research_problem,
        general_objective=general_objective,
        methodology_summary=methodology_summary,
        specific_objectives=parsed_objectives,
        profile=profile,
        planned_chapters=parsed_chapters,
    )

    spec_json_path = target_dir / "abnt.spec.json"
    spec_md_path = target_dir / "SPEC.md"

    spec_json_path.write_text(
        json.dumps(spec.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    spec_md_path.write_text(render_spec_markdown(spec), encoding="utf-8")

    return {
        "success": True,
        "spec_json_path": str(spec_json_path),
        "spec_md_path": str(spec_md_path),
        "spec": spec.model_dump(),
        "message": (
            f"Especificação SDD inicializada com sucesso ({len(parsed_objectives)} objetivos "
            f"específicos e {len(parsed_chapters)} capítulos planejados sob {standard})."
        ),
    }


def load_project_spec(project_path: str | Path, spec_path: str | Path | None = None) -> tuple[ResearchSpec, Path]:
    """Carrega e valida `abnt.spec.json` a partir do diretório do projeto ou caminho explícito."""
    if spec_path:
        sp = Path(spec_path)
    else:
        base = Path(project_path)
        proj_dir = base if base.is_dir() else base.parent
        sp = proj_dir / "abnt.spec.json"

    if not sp.is_file():
        raise FileNotFoundError(
            f"Manifesto de especificação 'abnt.spec.json' não encontrado em '{sp}'. "
            "Execute a ferramenta 'init_research_spec' para criar a especificação do projeto."
        )

    raw_data = json.loads(sp.read_text(encoding="utf-8"))
    return ResearchSpec(**raw_data), sp


def _extract_candidate_keywords(text: str) -> list[str]:
    """Extrai palavras substantivas (>= 5 letras) de um objetivo quando keywords não são fornecidas."""
    stopwords = {
        "sobre", "entre", "para", "como", "pelos", "pelas", "através", "partir",
        "estudo", "trabalho", "pesquisa", "forma", "meio", "dados", "análise",
        "analisar", "avaliar", "investigar", "desenvolver", "propor", "verificar",
        "identificar", "mapear", "compreender", "realizar", "elaborar", "implementar",
    }
    tokens = re.findall(r"[a-záéíóúâêôãõç0-9]{5,}", text.lower())
    keywords: list[str] = []
    for t in tokens:
        if t not in stopwords and t not in keywords:
            keywords.append(t)
        if len(keywords) >= 5:
            break
    return keywords


def _collect_manuscript_text(project_path: Path) -> str:
    """Coleta todo o texto do manuscrito ignorando SPEC.md e arquivos ocultos."""
    if project_path.is_file():
        if project_path.suffix.lower() == ".pdf":
            from abnt_mcp.parsers.pdf_reader import extract_pdf_section
            return extract_pdf_section(project_path)["text"]
        return project_path.read_text(encoding="utf-8", errors="replace")

    chunks: list[str] = []
    for f in sorted(project_path.rglob("*")):
        if (
            f.is_file()
            and f.suffix.lower() in {".tex", ".md", ".typ"}
            and f.name != "SPEC.md"
            and not any(p.startswith(".") or p in {"build", "dist", ".venv"} for p in f.parts)
        ):
            try:
                chunks.append(f.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
    return "\n\n".join(chunks)


def _split_body_and_conclusion(full_text: str) -> tuple[str, str]:
    """Separa o corpo do manuscrito e a seção de Conclusão / Considerações Finais."""
    concl_pattern = re.compile(
        r"(?:\\chapter\{[^}]*(?:conclus[ãa]o|considera[çc][õo]es\s+finais)[^}]*\}"
        r"|#+\s*\d*\s*(?:conclus[ãa]o|considera[çc][õo]es\s+finais)"
        r"|^=\s*\d*\s*(?:conclus[ãa]o|considera[çc][õo]es\s+finais)"
        r"|\b\d+\s+(?:CONCLUS[ÃA]O|CONSIDERA[ÇC][ÕO]ES\s+FINAIS)\b)",
        re.IGNORECASE | re.MULTILINE,
    )
    matches = list(concl_pattern.finditer(full_text))
    if not matches:
        return full_text, ""

    # Usa a última ocorrência (para não confundir com o Sumário)
    last_match = matches[-1]
    body_text = full_text[:last_match.start()]
    conclusion_text = full_text[last_match.start():]
    return body_text, conclusion_text


def audit_project_against_spec(
    project_path: str | Path,
    spec_path: str | Path | None = None,
) -> SpecAuditResult:
    """
    Executa a auditoria SDD completa confrontando o manuscrito acadêmico com o
    manifesto `abnt.spec.json` nas 3 camadas (Perfil Normativo, Objetivos Específicos e Capítulos).
    """
    path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError(f"Caminho do projeto não encontrado: {path}")

    spec, resolved_spec_path = load_project_spec(path, spec_path)

    # 1. Auditoria da Camada 1: Estrutura, Citações e Tom Científico
    structure_res = check_project_structure(path, standard=spec.profile.standard)
    citations_res = audit_citations_and_references(path)
    full_text = _collect_manuscript_text(path)
    tone_res = analyze_scientific_tone(full_text)

    body_text, conclusion_text = _split_body_and_conclusion(full_text)
    body_lower = body_text.lower()
    concl_lower = conclusion_text.lower()

    # 2. Auditoria da Camada 2: Matriz Científica (Objetivos Específicos OBJ-XX)
    objectives_audit: list[ObjectiveAuditItem] = []
    fulfilled_points = 0.0

    for obj in spec.specific_objectives:
        kws = obj.keywords or _extract_candidate_keywords(obj.description)
        matched_in_body = [k for k in kws if k.lower() in body_lower]
        matched_in_concl = [k for k in kws if k.lower() in concl_lower]

        covered_in_body = len(matched_in_body) > 0 if kws else bool(body_text.strip())
        answered_in_conclusion = len(matched_in_concl) > 0 if kws else bool(conclusion_text.strip())

        matched_all = sorted(list(set(matched_in_body + matched_in_concl)))
        missing_all = [k for k in kws if k not in matched_all]

        if covered_in_body and answered_in_conclusion:
            status: Literal["fulfilled", "partial", "missing"] = "fulfilled"
            fulfilled_points += 1.0
            feedback = (
                f"Objetivo {obj.id} desenvolvido no texto e respondido na Conclusão "
                f"(termos validados: {', '.join(matched_all)})."
            )
        elif covered_in_body or answered_in_conclusion:
            status = "partial"
            fulfilled_points += 0.5
            if not answered_in_conclusion:
                feedback = (
                    f"Objetivo {obj.id} abordado no desenvolvimento, mas NÃO retomado explicitamente "
                    f"na Conclusão/Considerações Finais."
                )
            else:
                feedback = f"Objetivo {obj.id} mencionado na conclusão, mas pouco aprofundado no corpo textual."
        else:
            status = "missing"
            feedback = (
                f"Objetivo {obj.id} órfão: termos-chave ({', '.join(kws)}) não foram encontrados "
                "nem no desenvolvimento nem na conclusão."
            )

        objectives_audit.append(
            ObjectiveAuditItem(
                id=obj.id,
                description=obj.description,
                status=status,
                covered_in_body=covered_in_body,
                answered_in_conclusion=answered_in_conclusion,
                matched_keywords=matched_all,
                missing_keywords=missing_all,
                feedback=feedback,
            )
        )

    total_objs = len(spec.specific_objectives)
    objectives_fulfillment_rate = int((fulfilled_points / total_objs) * 100) if total_objs else 100

    # 3. Auditoria da Camada 3: Capítulos Planejados
    chapters_audit: list[ChapterAuditItem] = []
    found_chapters_count = 0
    full_lower = full_text.lower()

    for ch in spec.planned_chapters:
        title_clean = ch.title.strip().lower()
        found = title_clean in full_lower
        if found:
            found_chapters_count += 1
            ch_feedback = f"Seção '{ch.number} {ch.title}' localizada no manuscrito."
        else:
            ch_feedback = f"Seção planejada '{ch.number} {ch.title}' ausente no manuscrito."
        chapters_audit.append(
            ChapterAuditItem(
                number=ch.number,
                title=ch.title,
                found_in_document=found,
                feedback=ch_feedback,
            )
        )

    total_chapters = len(spec.planned_chapters)
    chapters_rate = int((found_chapters_count / total_chapters) * 100) if total_chapters else 100

    # 4. Consolidação de Violações Normativas Rastreáveis
    normative_issues: list[dict[str, str]] = list(structure_res.rule_violations)

    if citations_res.uppercase_violations:
        normative_issues.append({
            "rule_id": "NBR10520-R01",
            "standard": NORMATIVE_RULES["NBR10520-R01"]["standard"],
            "severity": "error",
            "message": f"Encontradas {len(citations_res.uppercase_violations)} citações em CAIXA ALTA entre parênteses.",
        })

    if citations_res.orphan_citations:
        normative_issues.append({
            "rule_id": "NBR10520-R02",
            "standard": NORMATIVE_RULES["NBR10520-R02"]["standard"],
            "severity": "error",
            "message": f"Encontradas {len(citations_res.orphan_citations)} citações órfãs no texto sem correspondente no .bib.",
        })

    if citations_res.total_references_in_bib < spec.profile.min_references:
        normative_issues.append({
            "rule_id": "NBR6023-R02",
            "standard": NORMATIVE_RULES["NBR6023-R02"]["standard"],
            "severity": "warning",
            "message": (
                f"Quantidade de referências no .bib ({citations_res.total_references_in_bib}) "
                f"inferior à meta da spec ({spec.profile.min_references})."
            ),
        })

    # 5. Cálculo do spec_compliance_score (0 a 100)
    ref_ratio = min(1.0, citations_res.total_references_in_bib / max(1, spec.profile.min_references))
    rigor_and_refs_score = int((tone_res.score * 0.6) + (ref_ratio * 100 * 0.4))

    spec_compliance_score = int(
        (structure_res.compliance_score * 0.35)
        + (objectives_fulfillment_rate * 0.40)
        + (chapters_rate * 0.15)
        + (rigor_and_refs_score * 0.10)
    )

    recommendations: list[str] = list(structure_res.recommendations)
    for item in objectives_audit:
        if item.status != "fulfilled":
            recommendations.append(
                f"[{item.id}] Retome os conceitos ({', '.join(item.missing_keywords or [item.description[:40]])}) "
                "no Desenvolvimento e responda-os diretamente na Conclusão."
            )
    for ch_item in chapters_audit:
        if not ch_item.found_in_document:
            recommendations.append(f"Adicione o capítulo planejado '{ch_item.number} {ch_item.title}'.")
    if citations_res.total_references_in_bib < spec.profile.min_references:
        recommendations.append(
            f"Amplie a revisão bibliográfica no arquivo .bib de {citations_res.total_references_in_bib} "
            f"para pelo menos {spec.profile.min_references} referências."
        )

    is_compliant = (
        structure_res.is_valid
        and objectives_fulfillment_rate >= 80
        and citations_res.is_consistent
        and spec_compliance_score >= 80
    )

    return SpecAuditResult(
        spec_path=str(resolved_spec_path),
        title=spec.title,
        document_type=spec.profile.document_type,
        standard_applied=structure_res.standard,
        is_compliant=is_compliant,
        spec_compliance_score=spec_compliance_score,
        structure_score=structure_res.compliance_score,
        objectives_fulfillment_rate=objectives_fulfillment_rate,
        tone_score=tone_res.score,
        references_count=citations_res.total_references_in_bib,
        min_references_required=spec.profile.min_references,
        objectives_audit=objectives_audit,
        chapters_audit=chapters_audit,
        normative_issues=normative_issues,
        recommendations=recommendations,
    )


def get_spec_template_resource() -> str:
    """Retorna o template JSON comentado para o resource `abnt://template/spec`."""
    template_obj = {
        "spec_version": "1.0",
        "title": "Título Completo do Trabalho Acadêmico ou Artigo Científico",
        "author": "Nome Completo do Autor",
        "research_problem": "Qual pergunta científica o estudo responde?",
        "general_objective": "Analisar/Desenvolver/Avaliar...",
        "methodology_summary": "Pesquisa aplicada, exploratória, revisão sistemática ou estudo de caso...",
        "profile": {
            "document_type": "tcc",
            "standard": "ABNT_14724",
            "institution": "Universidade / Instituição",
            "emphasis_style": "bold",
            "min_references": 15,
            "min_scientific_tone_score": 80,
        },
        "specific_objectives": [
            {
                "id": "OBJ-01",
                "description": "Mapear o referencial teórico e as normas técnicas aplicáveis ao domínio.",
                "keywords": ["referencial", "normas", "mapeamento"],
                "target_section": "Fundamentação Teórica",
            },
            {
                "id": "OBJ-02",
                "description": "Avaliar empiricamente os resultados obtidos frente às hipóteses iniciais.",
                "keywords": ["resultados", "avaliação", "empírico"],
                "target_section": "Resultados e Discussão",
            },
        ],
        "planned_chapters": DEFAULT_PLANNED_CHAPTERS_TCC,
    }
    return json.dumps(template_obj, indent=2, ensure_ascii=False)
