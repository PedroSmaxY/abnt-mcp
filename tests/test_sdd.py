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
import pytest

from abnt_mcp.config import (
    NORMATIVE_RULES,
    get_current_year,
    get_default_author_source,
    validate_safe_path,
)
from abnt_mcp.server import (
    init_research_spec,
    scaffold_academic_project,
    audit_research_spec,
    simulate_banca,
    check_structure,
    audit_illustrations_and_tables,
    validate_citations,
    analyze_tone,
    format_figure,
    format_table,
    clean_bibtex_file,
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
        title="Estudo sobre Artigos Científicos",
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


def test_dynamic_year_and_safe_path_and_bibtex_backup(tmp_path: Path) -> None:
    """Testa ano dinâmico, bloqueio de path traversal e backup automático em .abnt-mcp/backups/."""
    curr_year = str(get_current_year())
    assert curr_year in get_default_author_source()

    fig_res = format_figure(image_path="figuras/arq.png", caption="Arquitetura")
    assert curr_year in fig_res["source"]

    tab_res = format_table(title="Dados", headers=["A", "B"], rows=[["1", "2"]])
    assert curr_year in tab_res["snippets"]["markdown"]

    # Validação de path traversal fora de base_dir e byte nulo
    with pytest.raises(ValueError, match="Path Traversal"):
        validate_safe_path(tmp_path / ".." / "outside.txt", base_dir=tmp_path)

    with pytest.raises(ValueError, match="Caminho inválido"):
        validate_safe_path("   ")

    # Backup automático antes de sobrescrever arquivo .bib existente
    bib_path = tmp_path / "referencias.bib"
    original_bib = "@article{Silva2023,\n  author = {Silva, J.},\n  title = {Teste},\n  month = {mai.},\n  year = {2023}\n}\n"
    bib_path.write_text(original_bib, encoding="utf-8")

    clean_res = clean_bibtex_file(str(bib_path))
    assert clean_res["success"] is True
    assert clean_res["backup_path"] is not None

    backup_file = Path(clean_res["backup_path"])
    assert backup_file.is_file()
    assert backup_file.read_text(encoding="utf-8") == original_bib
    assert "maio" in bib_path.read_text(encoding="utf-8")


def test_unified_diagnostic_item_normative_vs_heuristic(tmp_path: Path) -> None:
    """Verifica a distinção explícita entre violação normativa (ABNT) e heurística editorial."""
    doc_file = tmp_path / "doc.md"
    doc_file.write_text(
        "# 1.1. Introdução\nSegundo (SILVA, 2023) e [@ChaveOrfa], nós fizemos algo obviamente incrível.\n",
        encoding="utf-8",
    )
    (tmp_path / "refs.bib").write_text(
        "@book{ObraNaoCitada2024, author={Autor, A.}, title={Livro}, year={2024}}\n",
        encoding="utf-8",
    )

    # 1. check_structure emite diagnósticos normativos (confidence='high', human_review_required=False)
    struct_res = check_structure(str(tmp_path))
    assert len(struct_res["diagnostics"]) > 0
    assert any(
        d["rule_id"] == "NBR6024-R01"
        and d["nature"] == "normative"
        and d["confidence"] == "high"
        and d["human_review_required"] is False
        for d in struct_res["diagnostics"]
    )

    # 2. validate_citations emite diagnósticos normativos NBR10520-R01 e NBR10520-R02
    cit_res = validate_citations(str(tmp_path))
    diag_ids = {d["rule_id"] for d in cit_res["diagnostics"]}
    assert "NBR10520-R01" in diag_ids
    assert "NBR10520-R02" in diag_ids
    assert all(d["nature"] == "normative" and d["human_review_required"] is False for d in cit_res["diagnostics"])

    # 3. analyze_tone emite diagnósticos heurísticos (nature='heuristic', human_review_required=True)
    tone_res = analyze_tone("Eu fiz uma pesquisa e obviamente a gente achou pra caramba.")
    assert len(tone_res["diagnostics"]) >= 3
    assert all(
        d["nature"] == "heuristic"
        and d["confidence"] == "medium"
        and d["human_review_required"] is True
        for d in tone_res["diagnostics"]
    )


def _build_university_sample_pdf_with_logo(pdf_path: Path) -> None:
    """Constrói um PDF sintético multi-página com brasão (/XObject /Image) na Capa e padrões institucionais."""
    import pypdf
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
        NumberObject,
    )

    writer = pypdf.PdfWriter()

    def _make_text_page(lines: list[str], with_logo: bool = False) -> pypdf.PageObject:
        page = pypdf.PageObject.create_blank_page(width=595, height=842)
        font_dict = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        resources = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font_dict)})
        })

        ops = ["BT", "/F1 12 Tf", "72 780 Td"]
        for idx, ln in enumerate(lines):
            escaped = ln.replace("(", "\\(").replace(")", "\\)")
            if idx > 0:
                ops.append("0 -20 Td")
            ops.append(f"({escaped}) Tj")
        ops.append("ET")

        if with_logo:
            img_stream = DecodedStreamObject()
            img_stream.set_data(b"\x10\x40\x80" * (16 * 16))
            img_stream.update({
                NameObject("/Type"): NameObject("/XObject"),
                NameObject("/Subtype"): NameObject("/Image"),
                NameObject("/Width"): NumberObject(16),
                NameObject("/Height"): NumberObject(16),
                NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
                NameObject("/BitsPerComponent"): NumberObject(8),
            })
            img_ref = writer._add_object(img_stream)
            resources[NameObject("/XObject")] = DictionaryObject({NameObject("/ImLogo"): img_ref})
            ops.insert(0, "q 40 0 0 40 270 800 cm /ImLogo Do Q")

        page[NameObject("/Resources")] = resources
        content_stream = DecodedStreamObject()
        content_stream.set_data("\n".join(ops).encode("latin-1", errors="replace"))
        page[NameObject("/Contents")] = writer._add_object(content_stream)
        return page

    # Página 1: Capa com Brasão + Cabeçalho Institucional
    writer.add_page(_make_text_page([
        "UNIVERSIDADE FEDERAL DE TECNOLOGIA",
        "CENTRO DE INFORMÁTICA E COMPUTAÇÃO",
        "CURSO DE BACHARELADO EM ENGENHARIA DE SOFTWARE",
        "MARIA APARECIDA SILVA",
        "MODELO INSTITUCIONAL DE TCC",
        "2025",
    ], with_logo=True))

    # Página 2: Folha de Rosto com Preâmbulo e Orientador + Ficha Catalográfica + Considerações Finais
    writer.add_page(_make_text_page([
        "MARIA APARECIDA SILVA",
        "Trabalho de Conclusão de Curso apresentado à Universidade Federal de Tecnologia como requisito parcial para obtenção do grau de Bacharel.",
        "Orientador: Prof. Dr. Roberto Almeida",
        "Ficha Catalográfica elaborada pela Biblioteca Central",
        "Folha de Aprovação da Banca Examinadora",
        "5 Considerações Finais",
    ], with_logo=False))

    with open(pdf_path, "wb") as fp:
        writer.write(fp)


def test_scaffold_academic_project_with_sample_pdf_and_logo_extraction(tmp_path: Path) -> None:
    """Verifica se scaffold_academic_project aprende o padrão e extrai a logo da capa de um PDF da faculdade."""
    sample_pdf = tmp_path / "modelo_faculdade.pdf"
    _build_university_sample_pdf_with_logo(sample_pdf)

    proj_dir = tmp_path / "meu_tcc_typst"
    res = scaffold_academic_project(
        project_path=str(proj_dir),
        title="Arquitetura de Agentes Acadêmicos",
        author="Pedro Henrique Novais",
        document_type="tcc",
        format="typst",
        sample_pdf_path=str(sample_pdf),
    )

    assert res["success"] is True
    assert res["cover_logo_path"] == "figuras/logo_instituicao.png"
    extracted_logo = proj_dir / "figuras" / "logo_instituicao.png"
    assert extracted_logo.is_file()
    assert extracted_logo.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    inferred = res["inferred_institutional_profile"]
    assert inferred is not None
    assert inferred["inferred_from_pdf"] is True
    assert inferred["has_cover_logo"] is True
    assert "UNIVERSIDADE FEDERAL DE TECNOLOGIA" in (inferred["institution"] or "")
    assert "Prof. Dr. Roberto Almeida" in (inferred["advisor"] or "")
    assert "ficha catalografica" in inferred["required_pre_textual"]
    assert "folha de aprovacao" in inferred["required_pre_textual"]
    assert inferred["conclusion_label"] == "Considerações Finais"

    main_typ = (proj_dir / "main.typ").read_text(encoding="utf-8")
    assert '#image("figuras/logo_instituicao.png", width: 3cm)' in main_typ
    assert "CONSIDERAÇÕES FINAIS" in main_typ

    # Proteção contra sobrescrita acidental (overwrite=False)
    with pytest.raises(FileExistsError):
        scaffold_academic_project(
            project_path=str(proj_dir),
            title="Outro Título",
            author="Outro Autor",
            overwrite=False,
        )


def test_scaffold_academic_project_latex_and_markdown_with_explicit_logo(tmp_path: Path) -> None:
    """Valida scaffolding nos formatos LaTeX e Markdown com cópia de logo explícita (logo_path)."""
    from abnt_mcp.parsers.pdf_reader import _encode_rgb_png_bytes

    external_logo = tmp_path / "brasao_uf.png"
    external_logo.write_bytes(_encode_rgb_png_bytes(8, 8, b"\x20\x60\xa0" * 64))

    latex_dir = tmp_path / "proj_latex"
    res_tex = scaffold_academic_project(
        project_path=str(latex_dir),
        title="Dissertação em LaTeX",
        author="Ana Beatriz",
        document_type="dissertacao",
        format="latex",
        institution="Universidade de São Paulo",
        logo_path=str(external_logo),
    )
    assert res_tex["success"] is True
    assert (latex_dir / "main.tex").is_file()
    assert (latex_dir / "figuras" / "logo_instituicao.png").is_file()
    assert "logo_instituicao.png" in (latex_dir / "main.tex").read_text(encoding="utf-8")

    md_dir = tmp_path / "proj_md"
    res_md = scaffold_academic_project(
        project_path=str(md_dir),
        title="Artigo em Markdown",
        author="Carlos Silva",
        document_type="artigo",
        format="markdown",
        logo_path=str(external_logo),
    )
    assert res_md["success"] is True
    assert (md_dir / "main.md").is_file()
    assert "![Logotipo Institucional](figuras/logo_instituicao.png)" in (md_dir / "main.md").read_text(encoding="utf-8")


def test_audit_illustrations_and_tables_nbr14724_and_ibge1993(tmp_path: Path) -> None:
    """Valida a auditoria de figuras, tabelas e quadros (chamada prévia, Fonte:, imagem quebrada, sequência e IBGE)."""
    doc = tmp_path / "manuscrito.md"
    doc.write_text(
        """# 1 Resultados

Conforme observa-se na Figura 1, o fluxo está completo.

**Figura 1 – Arquitetura do Sistema**
![Arquitetura](figuras/inexistente.png)
Fonte: Elaborado pelo autor (2026).

**Figura 3 – Diagrama sem chamada prévia e fora de sequência**
![Diagrama](figuras/outro_inexistente.png)

A seguir apresenta-se a Tabela 1 no texto.

**Tabela 1 – Comparativo puramente conceitual sem números**
| Abordagem | Característica |
| :--- | :--- |
| Tradicional | Manual |
| SDD | Automatizada |
Fonte: Elaborado pelo autor (2026).
""",
        encoding="utf-8",
    )

    res = audit_illustrations_and_tables(str(tmp_path))
    assert res["is_valid"] is False
    assert res["total_figures"] == 2
    assert res["total_tables"] == 1
    assert len(res["broken_image_paths"]) == 2
    assert any(u["number"] == 3 and u["type"] == "figura" for u in res["unreferenced_items"])
    assert any(m["number"] == 3 and m["type"] == "figura" for m in res["missing_sources"])
    assert any(n["found_number"] == 3 and n["expected_number"] == 2 for n in res["numbering_issues"])
    assert len(res["quadro_vs_tabela_warnings"]) == 1
    assert any(d["rule_id"] == "IBGE1993-R01" for d in res["diagnostics"])
    assert any(d["rule_id"] == "NBR14724-R03" for d in res["diagnostics"])


def test_comprehensive_spec_audit_institutional_rules_and_persistent_reports(tmp_path: Path) -> None:
    """Valida auditoria integrada (regras institucionais, prontidão de entrega e relatórios em .abnt-mcp/)."""
    sample_pdf = tmp_path / "modelo_uf.pdf"
    _build_university_sample_pdf_with_logo(sample_pdf)

    proj_dir = tmp_path / "tcc_integrado"
    scaffold_academic_project(
        project_path=str(proj_dir),
        title="Auditoria Acadêmica Orientada a Especificação",
        author="Pedro Henrique Novais",
        document_type="tcc",
        format="typst",
        sample_pdf_path=str(sample_pdf),
    )

    # 0. O scaffold dinâmico já injeta ficha catalográfica e folha de aprovação de imediato
    audit_0 = audit_research_spec(str(proj_dir))
    assert audit_0["institutional_compliance"]["is_compliant"] is True
    assert audit_0["institutional_compliance"]["missing_pre_textual"] == []

    # 1. Simula adição de requisito institucional ("epigrafe") ainda ausente no manuscrito
    spec_file = proj_dir / "abnt.spec.json"
    spec_data = json.loads(spec_file.read_text(encoding="utf-8"))
    spec_data["profile"]["required_pre_textual"].append("epigrafe")
    spec_file.write_text(json.dumps(spec_data, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_1 = audit_research_spec(str(proj_dir))
    assert audit_1["submission_readiness"] == "NOT_READY"
    assert audit_1["institutional_compliance"]["is_compliant"] is False
    assert "epigrafe" in audit_1["institutional_compliance"]["missing_pre_textual"]
    assert any(d["rule_id"] == "INST-PROFILE-PRETEXTUAL" and d["nature"] == "institutional" for d in audit_1["diagnostics"])

    # Verifica persistência dos relatórios em .abnt-mcp/
    json_report = Path(audit_1["saved_report_paths"]["json"])
    md_report = Path(audit_1["saved_report_paths"]["markdown"])
    assert json_report.is_file()
    assert md_report.is_file()
    assert "Relatório de Conformidade Acadêmica (SDD)" in md_report.read_text(encoding="utf-8")

    # 2. Corrige as pendências institucionais e ajusta min_references=1 na spec
    spec_data["profile"]["min_references"] = 1
    spec_file.write_text(json.dumps(spec_data, indent=2, ensure_ascii=False), encoding="utf-8")

    main_typ = proj_dir / "main.typ"
    main_typ.write_text(
        main_typ.read_text(encoding="utf-8")
        + "\n// Epígrafe institucional adicionada\n",
        encoding="utf-8",
    )

    audit_2 = audit_research_spec(str(proj_dir))
    assert audit_2["institutional_compliance"]["is_compliant"] is True
    assert audit_2["is_compliant"] is True
    assert audit_2["submission_readiness"] in {"READY", "READY_WITH_WARNINGS"}


def test_scaffold_academic_project_renders_all_inferred_pre_textual_elements(tmp_path: Path) -> None:
    """
    Valida que scaffold_academic_project renderiza dinamicamente todos os 9 elementos pré-textuais
    inferidos do PDF institucional (em Typst, LaTeX e Markdown), para a varredura ao atingir o Sumário/Introdução,
    passa em check_structure e mantém NBR14724-R02 intacta (sem números de página visíveis nas pré-textuais).
    """
    import pypdf
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    from abnt_mcp.parsers.pdf_reader import extract_institutional_pattern_from_pdf
    from abnt_mcp.server import compile_tcc

    def _create_pdf_with_pages(pdf_file: Path, pages_lines: list[list[str]]) -> None:
        writer = pypdf.PdfWriter()
        for lines in pages_lines:
            page = pypdf.PageObject.create_blank_page(width=595, height=842)
            font_dict = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })
            resources = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font_dict)})
            })
            ops = ["BT", "/F1 12 Tf", "72 780 Td"]
            for idx, ln in enumerate(lines):
                escaped = ln.replace("(", "\\(").replace(")", "\\)")
                if idx > 0:
                    ops.append("0 -20 Td")
                ops.append(f"({escaped}) Tj")
            ops.append("ET")
            page[NameObject("/Resources")] = resources
            stream = DecodedStreamObject()
            stream.set_data("\n".join(ops).encode("latin-1", errors="replace"))
            page[NameObject("/Contents")] = writer._add_object(stream)
            writer.add_page(page)
        with open(pdf_file, "wb") as fp:
            writer.write(fp)

    # 1. Verifica que menções no corpo do texto (após Sumário / 1 INTRODUÇÃO) NÃO geram falso-positivo pré-textual
    sample_stop = tmp_path / "modelo_stop_scan.pdf"
    _create_pdf_with_pages(sample_stop, [
        ["UNIVERSIDADE ESTADUAL", "JOAO SILVA", "TITULO DO TCC", "2025"],
        ["Folha de Aprovacao", "Agradecimentos", "SUMARIO"],
        ["1 INTRODUCAO", "Neste capitulo discutimos a Lista de Tabelas e a Epigrafe do autor."],
    ])
    stop_pattern = extract_institutional_pattern_from_pdf(sample_stop)
    assert stop_pattern["required_pre_textual"] == ["folha de aprovacao", "agradecimentos"]
    assert "lista de tabelas" not in stop_pattern["required_pre_textual"]
    assert "epigrafe" not in stop_pattern["required_pre_textual"]

    # 2. PDF completo com todos os 9 elementos pré-textuais do catálogo antes do Sumário
    sample_full = tmp_path / "modelo_9_elementos.pdf"
    _create_pdf_with_pages(sample_full, [
        ["UNIVERSIDADE FEDERAL DO BRASIL", "FACULDade DE ENGENHARIA", "CURSO DE COMPUTACAO", "ANA SOUZA", "TCC COMPLETO", "2025"],
        [
            "Ficha Catalografica",
            "Folha de Aprovacao",
            "Dedicatoria",
            "Agradecimentos",
            "Epigrafe",
            "Lista de Ilustracoes",
            "Lista de Tabelas",
            "Lista de Quadros",
            "Lista de Abreviaturas e Siglas",
            "SUMARIO",
        ],
    ])

    expected_all_9 = [
        "ficha catalografica",
        "folha de aprovacao",
        "dedicatoria",
        "agradecimentos",
        "epigrafe",
        "lista de ilustracoes",
        "lista de tabelas",
        "lista de quadros",
        "lista de abreviaturas",
    ]

    for fmt, ext in [("typst", "main.typ"), ("latex", "main.tex"), ("markdown", "main.md")]:
        proj_dir = tmp_path / f"proj_{fmt}"
        res = scaffold_academic_project(
            project_path=str(proj_dir),
            title="Sistema de Verificação Normativa ABNT",
            author="Pedro Henrique Novais",
            document_type="tcc",
            format=fmt,
            sample_pdf_path=str(sample_full),
        )
        assert res["success"] is True
        assert res["inferred_institutional_profile"]["required_pre_textual"] == expected_all_9

        content = (proj_dir / ext).read_text(encoding="utf-8")
        lowered = content.lower()
        assert "ficha catalogr" in lowered
        assert "aprovado em:" in lowered
        assert "dedico este trabalho" in lowered
        assert "agradecimentos" in lowered
        assert "epígrafe" in lowered or "epigrafe" in lowered
        assert "lista de ilustrações" in lowered or "\\listoffigures" in lowered
        assert "lista de tabelas" in lowered or "\\listoftables" in lowered
        assert "lista de quadros" in lowered
        assert "lista de abreviaturas" in lowered or "siglas" in lowered

        # Verifica aprovação estrutural e de auditoria SDD imediata
        struct = check_structure(str(proj_dir))
        assert struct["is_valid"] is True, f"Falha estrutural em {fmt}: {struct}"
        assert set(expected_all_9).issubset(set(struct["optional_elements_present"]))

        audit = audit_research_spec(str(proj_dir))
        assert audit["institutional_compliance"]["is_compliant"] is True, (
            f"Inconformidade institucional pós-scaffold em {fmt}: {audit['institutional_compliance']}"
        )

    # 3. Compila o projeto Typst e garante que a paginação obedece estritamente à NBR14724-R02
    from abnt_mcp.parsers.pdf_reader import audit_pdf_pagination

    typst_proj = tmp_path / "proj_typst"
    comp = compile_tcc(str(typst_proj), engine="typst")
    if comp.get("success") is True and comp.get("pdf_generated"):
        pag_audit = audit_pdf_pagination(comp["pdf_generated"])
        assert pag_audit["is_compliant"] is True, (
            f"Violação NBR14724-R02 nas folhas pré-textuais dinâmicas: {pag_audit}"
        )


def test_typst_abnt_spacing_top_caption_and_reactive_outlines(tmp_path: Path) -> None:
    """
    Garante as regras de diagramação ABNT no Typst:
    1. Recuo de 1,25 cm em todos os parágrafos (first-line-indent com all: true);
    2. Identificação de figuras e tabelas no topo (caption position top);
    3. Quebra obrigatória de seções primárias em folha distinta (heading level 1 pagebreak weak);
    4. Listas pré-textuais reativas: só se materializam no PDF se houver figuras/tabelas/quadros no documento.
    """
    import io
    import pypdf
    from abnt_mcp.server import compile_tcc
    from abnt_mcp.templates.typst import get_typst_template

    # 1. Verifica paridade no template canônico exportado por abnt://template/typst
    canonical_tpl = get_typst_template()
    assert "first-line-indent: (amount: 1.25cm, all: true)" in canonical_tpl
    assert "figure.caption(position: top)" in canonical_tpl
    assert "pagebreak(weak: true)" in canonical_tpl
    assert "let tabs = query(figure.where(kind: table))" in canonical_tpl

    # 2. Scaffolding de um projeto Typst padrão (sem ilustrações/tabelas)
    proj_dir = tmp_path / "typst_reativo"
    scaffold_academic_project(
        project_path=str(proj_dir),
        title="Estudo sobre Tipografia e Diagramação ABNT",
        author="Pedro Henrique Novais",
        document_type="tcc",
        format="typst",
    )

    main_typ_path = proj_dir / "main.typ"
    main_typ = main_typ_path.read_text(encoding="utf-8")
    assert "first-line-indent: (amount: 1.25cm, all: true)" in main_typ
    assert "figure.caption(position: top)" in main_typ
    assert "pagebreak(weak: true)" in main_typ
    assert "leading: 0.8em" in main_typ

    # Compilação limpa sem figuras nem tabelas: nenhuma lista vazia deve ser gerada
    comp_clean = compile_tcc(str(proj_dir), engine="typst")
    assert comp_clean["success"] is True
    pdf_clean_bytes = Path(comp_clean["pdf_generated"]).read_bytes()
    reader_clean = pypdf.PdfReader(io.BytesIO(pdf_clean_bytes))
    clean_text = "".join(p.extract_text() for p in reader_clean.pages)
    assert "LISTA DE ILUSTRAÇÕES" not in clean_text
    assert "LISTA DE TABELAS" not in clean_text
    assert "LISTA DE QUADROS" not in clean_text

    # 3. Adiciona uma Tabela e um Quadro ao manuscrito no corpo do texto
    table_and_quadro_snippet = """
#figure(
  table(
    columns: 2,
    stroke: (x, y) => if x == 0 or x == 2 { none } else { 0.5pt },
    [Parâmetro], [Valor],
    [Amostra], [100],
    [Acurácia], [98.5%]
  ),
  caption: [Resultados Quantitativos da Amostra],
) <tab1>
#align(center)[#text(size: 10pt)[Fonte: Dados da pesquisa (2026).]]

#figure(
  table(
    columns: 2,
    stroke: 0.5pt,
    [Dimensão], [Definição Conceitual],
    [SDD], [Spec-Driven Development],
    [MCP], [Model Context Protocol]
  ),
  caption: [Matriz Conceitual Comparativa],
  kind: "quadro",
  supplement: [Quadro],
) <qua1>
#align(center)[#text(size: 10pt)[Fonte: Elaborado pelo autor (2026).]]
"""
    updated_main = main_typ.replace(
        "= RESULTADOS E DISCUSSÃO",
        "= RESULTADOS E DISCUSSÃO\n" + table_and_quadro_snippet
    )
    main_typ_path.write_text(updated_main, encoding="utf-8")

    comp_rich = compile_tcc(str(proj_dir), engine="typst")
    assert comp_rich["success"] is True
    pdf_rich_bytes = Path(comp_rich["pdf_generated"]).read_bytes()
    reader_rich = pypdf.PdfReader(io.BytesIO(pdf_rich_bytes))

    # As listas de tabelas e quadros agora se materializam reativamente!
    rich_text = "".join(p.extract_text() for p in reader_rich.pages)
    assert "LISTA DE TABELAS" in rich_text
    assert "LISTA DE QUADROS" in rich_text
    assert "Resultados Quantitativos da Amostra" in rich_text
    assert "Matriz Conceitual Comparativa" in rich_text
    # Lista de ilustrações permanece omitida porque não há imagens
    assert "LISTA DE ILUSTRAÇÕES" not in rich_text

    # Verifica que capítulos primários estão em páginas diferentes (pagebreak weak)
    pages_headings = {}
    for idx, page in enumerate(reader_rich.pages):
        txt = page.extract_text()
        for heading in ["1 INTRODUÇÃO", "2 FUNDAMENTAÇÃO TEÓRICA", "3 METODOLOGIA", "4 RESULTADOS E DISCUSSÃO", "5 CONCLUSÃO"]:
            if heading in txt:
                pages_headings[heading] = idx + 1

    assert pages_headings["1 INTRODUÇÃO"] < pages_headings["2 FUNDAMENTAÇÃO TEÓRICA"]
    assert pages_headings["2 FUNDAMENTAÇÃO TEÓRICA"] < pages_headings["3 METODOLOGIA"]
    assert pages_headings["3 METODOLOGIA"] < pages_headings["4 RESULTADOS E DISCUSSÃO"]
    assert pages_headings["4 RESULTADOS E DISCUSSÃO"] < pages_headings["5 CONCLUSÃO"]

    # Paginação ABNT permanece 100% em conformidade com NBR 14724 item 5.3
    from abnt_mcp.parsers.pdf_reader import audit_pdf_pagination
    pag_check = audit_pdf_pagination(comp_rich["pdf_generated"])
    assert pag_check["is_compliant"] is True


def test_sdd_release_version_changelog_and_privacy_invariants() -> None:
    """
    Garante:
    1. Paridade estrita entre pyproject.toml, abnt_mcp.__version__ e CHANGELOG.md;
    2. Presença da seção [Unreleased] e da versão atual no CHANGELOG.md;
    3. Ausência de e-mail pessoal exposto em authors no pyproject.toml (PEP 621 privacy);
    4. Existência dos artefatos de automação de Release (.github/workflows/release.yml e .github/release.yml).
    """
    from abnt_mcp import __version__

    pyproject_file = REPO_ROOT / "pyproject.toml"
    changelog_file = REPO_ROOT / "CHANGELOG.md"
    release_wf = REPO_ROOT / ".github" / "workflows" / "release.yml"
    release_cfg = REPO_ROOT / ".github" / "release.yml"

    assert pyproject_file.is_file()
    assert changelog_file.is_file()
    assert release_wf.is_file()
    assert release_cfg.is_file()

    pyproject_text = pyproject_file.read_text(encoding="utf-8")
    m_ver = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    assert m_ver is not None, "Campo version não encontrado no pyproject.toml"
    pyproject_version = m_ver.group(1)

    assert pyproject_version == __version__, (
        f"Desvio de versão: pyproject.toml ({pyproject_version}) != abnt_mcp.__version__ ({__version__})"
    )

    # Verifica que authors no pyproject.toml NÃO expõe campo email (anti-spam PEP 621)
    m_authors = re.search(r"authors\s*=\s*\[(.*?)\]", pyproject_text, re.DOTALL)
    assert m_authors is not None
    assert "email" not in m_authors.group(1).lower(), (
        "Violação de privacidade: não inclua 'email' em authors no pyproject.toml."
    )

    changelog_text = changelog_file.read_text(encoding="utf-8")
    assert "## [Unreleased]" in changelog_text, "CHANGELOG.md deve manter a seção '## [Unreleased]'."
    assert f"## [{__version__}]" in changelog_text, (
        f"A versão atual ({__version__}) deve estar documentada em '## [{__version__}]' no CHANGELOG.md."
    )
