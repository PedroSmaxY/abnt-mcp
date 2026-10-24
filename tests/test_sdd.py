"""Suíte de Testes SDD (Spec-Driven Development) e Trava Anti-Drift.

Valida:
1. Sincronia estrita entre o código-fonte (`config.py`, `server.py`) e os contratos em `specs/`.
2. Presença e integridade dos artefatos de governança (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`).
3. Ciclo completo do manifesto `abnt.spec.json` / `SPEC.md` (`init_research_spec` e `audit_research_spec`).
4. Suporte ao perfil de Artigo Científico (`ABNT_6022`) e rastreabilidade de IDs canônicos (`rule_violations`).
5. Integração da ferramenta `simulate_banca` com os objetivos específicos (`OBJ-XX`) da spec.
"""

from __future__ import annotations
import json
import re
from pathlib import Path

from abnt_mcp.config import NORMATIVE_RULES
from abnt_mcp.server import (
    init_research_spec,
    audit_research_spec,
    simulate_banca,
    check_structure,
    resource_guia_sdd,
    resource_template_spec,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_sdd_anti_drift_normative_rules() -> None:
    """
    TRAVA ANTI-DRIFT 1:
    Garante que todos os IDs em NORMATIVE_RULES (config.py) estão documentados
    em specs/01-normative-catalog.spec.md e vice-versa.
    """
    catalog_spec = REPO_ROOT / "specs" / "01-normative-catalog.spec.md"
    assert catalog_spec.is_file(), "specs/01-normative-catalog.spec.md ausente!"

    spec_text = catalog_spec.read_text(encoding="utf-8")
    spec_rule_ids = set(re.findall(r"\b(?:NBR\d+|IBGE1993)-R\d{2}\b", spec_text))
    code_rule_ids = set(NORMATIVE_RULES.keys())

    assert code_rule_ids == spec_rule_ids, (
        f"Desvio SDD detectado entre config.py e specs/01-normative-catalog.spec.md! "
        f"Apenas no código: {code_rule_ids - spec_rule_ids} | "
        f"Apenas na spec: {spec_rule_ids - code_rule_ids}"
    )


def test_sdd_anti_drift_mcp_surface() -> None:
    """
    TRAVA ANTI-DRIFT 2:
    Garante que todas as @mcp.tool, @mcp.prompt e @mcp.resource de server.py
    estão documentadas em specs/03-mcp-tools-contract.spec.md.
    """
    contract_spec = REPO_ROOT / "specs" / "03-mcp-tools-contract.spec.md"
    server_file = REPO_ROOT / "src" / "abnt_mcp" / "server.py"
    assert contract_spec.is_file(), "specs/03-mcp-tools-contract.spec.md ausente!"

    spec_text = contract_spec.read_text(encoding="utf-8")
    server_text = server_file.read_text(encoding="utf-8")

    # Extrai funções decoradas com @mcp.tool() ou @mcp.prompt()
    tool_and_prompt_names = re.findall(
        r"@mcp\.(?:tool|prompt)\(\)\s*\ndef\s+([a-zA-Z0-9_]+)\s*\(",
        server_text,
    )
    for name in tool_and_prompt_names:
        assert f"`{name}`" in spec_text, (
            f"Interface MCP '{name}' registrada em server.py mas ausente em "
            "specs/03-mcp-tools-contract.spec.md! Atualize a spec."
        )

    # Extrai URIs de @mcp.resource("...")
    resource_uris = re.findall(r'@mcp\.resource\("([^"]+)"\)', server_text)
    for uri in resource_uris:
        assert f"`{uri}`" in spec_text, (
            f"Resource '{uri}' registrado em server.py mas ausente em "
            "specs/03-mcp-tools-contract.spec.md! Atualize a spec."
        )


def test_sdd_governance_documents_exist() -> None:
    """Verifica a presença dos artefatos de governança SDD para agentes de IA e colaboradores."""
    required_files = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "CONTRIBUTING.md",
        REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
        REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "normative_deviation.yml",
        REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_spec.yml",
        REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml",
        REPO_ROOT / "specs" / "02-research-spec-schema.spec.md",
    ]
    for fpath in required_files:
        assert fpath.is_file(), f"Arquivo obrigatório de governança SDD ausente: {fpath}"


def test_init_and_audit_research_spec_fulfilled(tmp_path: Path) -> None:
    """Testa a criação de abnt.spec.json / SPEC.md e auditoria de um projeto 100% aderente."""
    init_res = init_research_spec(
        project_path=str(tmp_path),
        title="Auditoria SDD de Monografias ABNT",
        research_problem="Como garantir alinhamento entre objetivos específicos e conclusão?",
        general_objective="Desenvolver um validador orientado a especificações para trabalhos acadêmicos.",
        specific_objectives=[
            {
                "id": "OBJ-01",
                "description": "Mapear as regras normativas de citações e referências.",
                "keywords": ["citações", "referências"],
                "target_section": "Fundamentação Teórica",
            },
            {
                "id": "OBJ-02",
                "description": "Validar a compilação tipográfica automatizada em Typst.",
                "keywords": ["compilação", "typst"],
                "target_section": "Metodologia",
            },
        ],
        methodology_summary="Pesquisa aplicada experimental.",
        document_type="tcc",
        author="Pedro Henrique da Silva Novais",
        min_references=2,
    )

    assert init_res["success"] is True
    assert (tmp_path / "abnt.spec.json").is_file()
    assert (tmp_path / "SPEC.md").is_file()

    # Cria manuscrito completo que cumpre todos os capítulos, estrutura e objetivos na conclusão
    manuscript = tmp_path / "main.md"
    manuscript.write_text(
        """# Universidade Federal
Folha de Rosto - Trabalho de Conclusão de Curso - Orientador: Prof. Dr. Teste

# Resumo
Este estudo analisa citações e referências bem como a compilação em typst.

# Abstract
This study analyzes citations and references as well as typst compilation.

# Sumário

# 1 Introdução
Apresenta-se a contextualização conforme (Silva, 2023) e (Santos, 2024).

# 2 Fundamentação Teórica
Discutem-se profundamente as regras de citações e referências da ABNT (Silva, 2023).

# 3 Metodologia
Implementou-se o motor de compilação baseado em typst (Santos, 2024).

# 4 Resultados e Discussão
Os testes comprovaram a eficácia da validação de citações, referências e compilação typst.

# 5 Conclusão
Conclui-se que o mapeamento de citações e referências (OBJ-01) e o motor de compilação em typst (OBJ-02) atenderam integralmente às metas propostas.

# Referências
""",
        encoding="utf-8",
    )

    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(
        """@article{Silva2023,
  author = {Silva, João},
  title = {Normas ABNT},
  journal = {Revista Brasileira},
  year = {2023}
}
@book{Santos2024,
  author = {Santos, Maria},
  title = {Tipografia Digital},
  publisher = {Editora Acadêmica},
  year = {2024}
}
""",
        encoding="utf-8",
    )

    audit_res = audit_research_spec(str(tmp_path))
    assert audit_res["is_compliant"] is True
    assert audit_res["objectives_fulfillment_rate"] == 100
    assert audit_res["spec_compliance_score"] >= 85
    assert all(obj["status"] == "fulfilled" for obj in audit_res["objectives_audit"])


def test_audit_research_spec_detects_unfulfilled_objective_and_banca_questions(tmp_path: Path) -> None:
    """Verifica se objetivos não respondidos na Conclusão são sinalizados na auditoria e na banca."""
    init_research_spec(
        project_path=str(tmp_path),
        title="Estudo sobreArtigos Científicos",
        research_problem="Como estruturar artigos segundo a NBR 6022?",
        general_objective="Avaliar a conformidade de artigos científicos periódicos.",
        specific_objectives=[
            {
                "id": "OBJ-01",
                "description": "Analisar a estrutura textual da NBR 6022.",
                "keywords": ["estrutura", "periódico"],
            },
            {
                "id": "OBJ-02",
                "description": "Avaliar o desempenho quântico em redes neurais.",
                "keywords": ["quântico", "neurais"],
            },
        ],
        methodology_summary="Estudo comparativo.",
        document_type="artigo",
        min_references=1,
    )

    # Manuscrito de artigo (sem capa, sem folha de rosto, sem sumário — válido pela NBR 6022!)
    # Porém esquece totalmente o OBJ-02 (quântico / neurais)
    article_file = tmp_path / "artigo.md"
    article_file.write_text(
        """# Resumo
Estudo sobre a estrutura de artigo em periódico segundo a norma vigente.

# Abstract
Study on journal article structure.

# 1 Introdução
A estrutura de publicação em periódico exige rigor (Silva, 2023).

# 2 Metodologia
Analisou-se a estrutura documental de cada periódico selecionado (Silva, 2023).

# 3 Resultados e Discussão
A estrutura avaliada no periódico mostrou alta aderência.

# 4 Considerações Finais
Conclui-se que a estrutura do periódico atende à NBR 6022.

# Referências
""",
        encoding="utf-8",
    )
    (tmp_path / "refs.bib").write_text(
        "@article{Silva2023, author={Silva, A.}, title={Artigo}, year={2023}}\n",
        encoding="utf-8",
    )

    # 1. check_structure deve auto-detectar ABNT_6022 do abnt.spec.json e aprovar sem exigir capa/sumário
    struct_res = check_structure(str(tmp_path))
    assert struct_res["standard"] == "NBR 6022:2018"
    assert struct_res["is_valid"] is True

    # 2. audit_research_spec deve apontar OBJ-01 fulfilled e OBJ-02 missing
    audit_res = audit_research_spec(str(tmp_path))
    statuses = {item["id"]: item["status"] for item in audit_res["objectives_audit"]}
    assert statuses["OBJ-01"] == "fulfilled"
    assert statuses["OBJ-02"] == "missing"
    assert audit_res["objectives_fulfillment_rate"] == 50

    # 3. simulate_banca deve incluir pergunta específica cobrando o OBJ-02
    banca_res = simulate_banca(str(tmp_path))
    assert banca_res["spec_alignment"]["has_spec"] is True
    assert "OBJ-02" in banca_res["spec_alignment"]["unfulfilled_objectives"]
    assert any("OBJ-02" in q["examinador"] for q in banca_res["perguntas_da_banca"])


def test_sdd_resources_content() -> None:
    """Valida o retorno dos resources abnt://guia/sdd e abnt://template/spec."""
    guia = resource_guia_sdd()
    assert "SPEC-DRIVEN" in guia
    assert "abnt.spec.json" in guia

    tmpl_raw = resource_template_spec()
    tmpl_json = json.loads(tmpl_raw)
    assert tmpl_json["spec_version"] == "1.0"
    assert len(tmpl_json["specific_objectives"]) >= 2
