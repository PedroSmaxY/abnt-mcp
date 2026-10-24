"""Recursos estáticos e guias canônicos das normas ABNT para o MCP."""

GUIDE_CITATIONS_NBR10520 = """# GUIA ABNT NBR 10520:2023 — CITAÇÕES EM DOCUMENTOS

Esta edição atualizada substitui integralmente a versão de 2002.

## 1. FIM DA CAIXA ALTA NOS PARÊNTESES (A MUDANÇA CRÍTICA)
- Na norma antiga (2002): (SILVA, 2020, p. 15)
- Na NORMA VIGENTE (2023): (Silva, 2020, p. 15)
- Dois autores: (Silva; Santos, 2020)
- Três autores: (Silva; Santos; Costa, 2020)
- Quatro ou mais autores: (Silva et al., 2020)
*ALERTA:* Nunca utilize sobrenomes em caixa alta dentro de parênteses.

## 2. PONTUAÇÃO NA CITAÇÃO DIRETA CURTA (ATÉ 3 LINHAS)
- Inserida no fluxo normal do parágrafo, entre aspas duplas ("...").
- O ponto final fica SEMPRE APÓS os parênteses da fonte:
  "O aprendizado de máquina revolucionou o setor" (Silva, 2021, p. 45).

## 3. CITAÇÃO DIRETA LONGA (MAIS DE 3 LINHAS)
- Bloco isolado com recuo de 4,0 cm da margem esquerda.
- Fonte menor (tamanho 10).
- Espaçamento entrelinhas simples (1,0).
- NÃO se utilizam aspas.
- Ponto final após a indicação da fonte.

## 4. CITAÇÃO INDIRETA (PARÁFRASE)
- Reprodução das ideias com as próprias palavras.
- No texto: Conforme Oliveira (2022)...
- Entre parênteses: (Oliveira, 2022).
- Página é opcional na paráfrase.

## 5. CITAÇÃO DE CITAÇÃO (APUD)
- Utilizada apenas quando a fonte primária for inacessível.
- Exemplo: Segundo Vygotsky (1934 apud Oliveira, 2018, p. 25)...
- Na lista de referências final, lista-se APENAS a obra consultada (Oliveira, 2018).
"""

GUIDE_STRUCTURE_NBR14724 = """# GUIA ABNT NBR 14724:2011 — ESTRUTURA E FORMATAÇÃO DE TRABALHOS ACADÊMICOS

## 1. PARÂMETROS FÍSICOS E TIPOGRAFIA
- Papel: A4 (210 x 297 mm), cor branca.
- Margens: Superior 3 cm, Esquerda 3 cm, Inferior 2 cm, Direita 2 cm (Regra 3-3-2-2).
- Fonte: Tamanho 12 (Arial ou Times New Roman) para o texto principal.
- Fonte Menor: Tamanho 10 para citações longas, notas de rodapé, paginação e legendas.
- Espaçamento: 1,5 linha para o texto; 1,0 simples para citações longas e referências.
- Recuo de Parágrafo: 1,25 cm na primeira linha.
- Alinhamento: Justificado no corpo; Referências alinhadas À ESQUERDA.

## 2. PAGINAÇÃO
- Contagem: Inicia-se na Folha de Rosto (a Capa não conta nem numera).
- Exibição: O número só é impresso a partir da primeira folha da parte textual (Introdução).
- Posição: Canto superior direito, a 2,0 cm das bordas superior e direita.

## 3. DIVISÃO DOS ELEMENTOS
- Pré-textuais Obrigatórios: Capa, Folha de Rosto, Folha de Aprovação (versão final), Resumo (vernaculo), Abstract (língua estrangeira), Sumário.
- Pré-textuais Opcionais: Dedicatória, Agradecimentos, Epígrafe, Listas de Figuras/Tabelas/Siglas.
- Textuais: Introdução, Desenvolvimento (Fundamentação, Metodologia, Resultados), Conclusão.
- Pós-textuais: Referências (Obrigatório), Apêndices e Anexos (Opcionais).

## 4. NUMERAÇÃO DE SEÇÕES (NBR 6024)
- Sem ponto final: 1 Introdução, 1.1 Objetivos (NUNCA 1.1. com ponto!).
- Limite hierárquico: Até a seção quinária (5 níveis: 1.1.1.1.1).
"""

GUIDE_REFERENCES_NBR6023 = """# GUIA ABNT NBR 6023:2018 — REFERÊNCIAS BIBLIOGRÁFICAS

## 1. REGRAS FUNDAMENTAIS
- Alinhamento: À margem esquerda (NUNCA JUSTIFICADO).
- Espaçamento interno: Simples (1,0).
- Separação entre referências: 1 linha em branco (espaço simples).
- Destaque tipográfico: Apenas no TÍTULO principal (Negrito ou Itálico).
  O subtítulo (após dois pontos :) NUNCA recebe destaque tipográfico.

## 2. ABREVIAÇÃO DE MESES
jan., fev., mar., abr., maio (sem ponto!), jun., jul., ago., set., out., nov., dez.

## 3. EXEMPLOS POR TIPO
- LIVRO:
  SOBRENOME, Nome. **Título**: subtítulo. 2. ed. São Paulo: Atlas, 2021.
- ARTIGO DE PERIÓDICO:
  SOBRENOME, Nome. Título do artigo. **Nome da Revista**, Local, v. 10, n. 2, p. 15-30, jun. 2023. DOI: https://doi.org/...
- TCC/DISSERTAÇÃO/TESE:
  SOBRENOME, Nome. **Título**: subtítulo. 2024. 120 f. Dissertação (Mestrado em Computação) – Universidade Federal, Cidade, 2024.
"""

GUIDE_SDD_WORKFLOW = """# GUIA SDD (SPEC-DRIVEN ACADEMIC WRITING) — ABNT COPILOT MCP

O fluxo **Spec-Driven Development (SDD)** transforma a elaboração do trabalho acadêmico em um contrato verificável entre a Introdução, o Desenvolvimento e a Conclusão.

## 1. AS TRÊS CAMADAS DO MANIFESTO (`abnt.spec.json` & `SPEC.md`)
1. **Camada 1 — Perfil Normativo (`profile`):**
   - `document_type`: `"tcc"`, `"dissertacao"`, `"tese"` (validados sob a **ABNT NBR 14724**) ou `"artigo"` (validado sob a **ABNT NBR 6022**, sem exigir capa, folha de rosto ou sumário).
   - `min_references`: Meta mínima de entradas no arquivo `.bib`.
   - `min_scientific_tone_score`: Índice mínimo de rigor e impessoalidade (0 a 100).
2. **Camada 2 — Matriz Científica Rastreável (`specific_objectives`):**
   - Cada objetivo específico recebe um ID canônico (`OBJ-01`, `OBJ-02`, ...), descrição formal e lista de `keywords` que comprovam sua discussão no texto e sua resposta explícita na Conclusão.
3. **Camada 3 — Capítulos Planejados (`planned_chapters`):**
   - Lista de seções previstas (com numeração NBR 6024 e metas mínimas).

## 2. CICLO OPERACIONAL RECOMENDADO
1. **Inicializar a Especificação:** Execute a tool `init_research_spec` no início da pesquisa para criar `abnt.spec.json` e `SPEC.md`.
2. **Redigir e Formatar:** Utilize `format_citation`, `format_reference`, `format_figure` e `format_table` para redigir os capítulos.
3. **Auditar contra a Spec:** Execute `audit_research_spec` para verificar se todos os `OBJ-XX` foram respondidos na Conclusão e se todas as regras canônicas (`NBR14724-R01`, `NBR10520-R01`, `NBR6024-R01`, etc.) foram cumpridas.
4. **Simular Banca Examinadora:** Execute `simulate_banca` para obter arguição focada nos objetivos específicos pendentes antes da entrega final.
"""
