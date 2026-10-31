# Desafio Técnico: ETL e Análise de Contratos Públicos - Estado do Rio de Janeiro

Repositório desenvolvido para avaliação técnica de Engenharia e Análise de Dados, contendo um processo completo de **ETL (Extract, Transform, Load)**, **Modelagem Dimensional (Star Schema)** e **Análise Exploratória com Storytelling** dos dados públicos do **Portal de Compras do Estado do Rio de Janeiro (SIGA)**.

---

## 📌 Sumário
- [1. Visão Geral e Objetivos](#1-visão-geral-e-objetivos)
- [2. Arquitetura do Pipeline de Dados](#2-arquitetura-do-pipeline-de-dados)
- [3. Estrutura do Repositório](#3-estrutura-do-repositório)
- [4. Regras de Limpeza e Qualidade de Dados (Data Quality)](#4-regras-de-limpeza-e-qualidade-de-dados-data-quality)
- [5. Modelagem Dimensional (Star Schema)](#5-modelagem-dimensional-star-schema)
- [6. Como Executar o Projeto](#6-como-executar-o-projeto)
- [7. Resumo dos Resultados e Indicadores Chave](#7-resumo-dos-resultados-e-indicadores-chave)
- [8. Conformidade com os Critérios de Avaliação](#8-conformidade-com-os-critérios-de-avaliação)

---

## 1. Visão Geral e Objetivos

O projeto tem como finalidade ingerir, sanear, estruturar e analisar dois conjuntos de dados volumosos do Portal de Compras do Governo do Estado do Rio de Janeiro:
- **`CONTRATOS.CSV`**: 130.566 registros de contratos e termos aditivos com dados orçamentários, cadastrais e de vigência.
- **`ITENS_CONTRATOS.CSV`**: 344.338 registros de itens adquiridos associados aos contratos.

---

## 2. Arquitetura do Pipeline de Dados

O fluxo foi concebido seguindo as melhores práticas da Engenharia de Dados moderna (Arquitetura Medalhão):

```
┌──────────────────────────────────────┐
│            CAMADA BRONZE             │
│    (Dados Brutos / Raw Ingestion)    │ -> Ingestão segura dos CSVs brutos (encoding latin1, sep=';')
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│            CAMADA SILVER             │
│  (Data Quality, Limpeza e Tipagem)   │ -> Padronização de nomes (snake_case)
└──────────────────┬───────────────────┘ -> Parsing de números e moeda brasileira (R$)
                   │                     -> Higienização de CPF/CNPJ com zeros à esquerda
                   │                     -> Filtro de sanidade temporal em datas (2000-2035)
                   │                     -> Deduplicação de 747 itens e consolidação de chaves
                   ▼
┌──────────────────────────────────────┐
│             CAMADA GOLD              │
│   (Modelagem Dimensional / Carga)    │ -> Criação de Dimensões (Fornecedor, Órgão, Tempo)
└──────────────────┬───────────────────┘ -> Fatos (Fato Contratos, Fato Itens)
                   │                     -> Exportação otimizada em Parquet e CSV
                   ▼
┌──────────────────────────────────────┐
│      ANÁLISE & STORYTELLING          │
│       (Gráficos e Relatório)         │ -> 7 visualizações de alta resolução (300 DPI)
└──────────────────────────────────────┘ -> Relatório Executivo com diagnósticos orçamentários
```

---

## 3. Estrutura do Repositório

```text
desafio_contratos/
├── data/
│   ├── raw/                           # CSVs originais do Portal SIGA-RJ
│   │   ├── CONTRATOS.CSV
│   │   └── ITENS_CONTRATOS.CSV
│   └── processed/                     # Tabelas tratadas e modeladas (Parquet + CSV)
│       ├── dim_fornecedor.parquet / .csv
│       ├── dim_orgao.parquet / .csv
│       ├── dim_tempo.parquet / .csv
│       ├── fato_contratos.parquet / .csv
│       ├── fato_itens.parquet / .csv
│       └── df_analitico.parquet / .csv
├── src/
│   ├── __init__.py
│   ├── config.py                      # Constantes, parâmetros e diretórios do projeto
│   ├── extract.py                     # Módulo de extração segura da Camada Bronze
│   ├── transform.py                   # Regras de limpeza, tipagem e deduplicação (Silver)
│   ├── model.py                       # Modelagem dimensional Star Schema (Gold)
│   ├── load.py                        # Persistência em Parquet e CSV
│   ├── visualize.py                   # Geração de 7 gráficos analíticos executivos
│   └── analysis.py                    # KPIs financeiros, Pareto e métricas de compras
├── notebooks/
│   └── exploratory_analysis.py        # Script para exploração interativa dos dados
├── reports/
│   ├── figures/                       # Gráficos em alta resolução (300 DPI)
│   │   ├── 01_funil_execucao_orcamentaria.png
│   │   ├── 02_top_10_fornecedores_pareto.png
│   │   ├── 03_top_10_orgaos_compradores.png
│   │   ├── 04_evolucao_regime_juridico.png
│   │   ├── 05_sazonalidade_mensal_gastos.png
│   │   ├── 06_distribuicao_modalidades.png
│   │   └── 07_elementos_despesa_publica.png
│   └── relatorio_final.md             # Relatório analítico completo com conclusões
├── main.py                            # Orquestrador do pipeline ponta a ponta
├── requirements.txt                   # Dependências do projeto
└── README.md                          # Documentação técnica integral
```

---

## 4. Regras de Limpeza e Qualidade de Dados (Data Quality)

| Regra / Desafio | Diagnóstico nos Dados Brutos | Tratamento Implementado |
| :--- | :--- | :--- |
| **Nomes de Colunas** | Espaços residuais (`' Valor Total Pago (R$)'`) e acentuações corrompidas. | Normalização sistemática para `snake_case` sem acentos e com nomes semânticos. |
| **Valores Monetários** | Padrões híbridos (`500000`, `38715,96` e `1.498.939,00`). | Função de parsing numérico que remove pontuação de milhar e converte vírgula decimal para float. |
| **Empenhos Negativos** | Valores de empenho negativos (ex: `-11.628.000,00`). | Preservados e classificados como estornos e cancelamentos contábeis. |
| **Duplicatas Totais** | **747 linhas 100% idênticas** em `ITENS_CONTRATOS.CSV`. | Expurgadas com `drop_duplicates()`. |
| **Duplicatas de Chave Composta** | 3.879 ocorrências com mesmo `(id_contratacao, id_item)`. | Consolidadas somando quantitativo e recalculando o preço unitário ponderado. |
| **Erros de Digitação em Datas** | Anos anômalos em datas de fim de vigência (ex: **8202** e **9201**). | Validadas na janela aceitável `[2000, 2035]`; anomalias foram neutralizadas para `NaT`. |
| **Truncamento de CNPJ** | 2.187 CNPJs com 13 dígitos devido à perda de zeros à esquerda. | Aplicação de máscara `zfill(14)` para reconstituição da formatação fiscal. |
| **Integridade 1 : N** | Relação entre Contratos e Itens. | Verificada 100% de correspondência na chave `id_contratacao` (0 contratos sem itens e 0 itens órfãos). |

---

## 5. Modelagem Dimensional (Star Schema)

A camada Gold estrutura os dados para consumo rápido por ferramentas de BI e análise avançada:

```
                  ┌──────────────────────┐
                  │    dim_fornecedor    │
                  ├──────────────────────┤
                  │ PK  id_fornecedor    │
                  │     fornecedor_nome  │
                  │     cpf_cnpj_limpo   │
                  │     tipo_documento   │
                  └──────────┬───────────┘
                             │
                             ▼
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
│    dim_tempo     │  │    fato_contratos    │  │    dim_orgao     │
├──────────────────┤  ├──────────────────────┤  ├──────────────────┤
│ PK  data         ├──► PK  id_contratacao   │◄─┤ PK  id_ug        │
│     ano          │  │ FK  id_fornecedor    │  │     cod_ug       │
│     mes          │  │ FK  id_ug            │  │     unidade_nome │
│     trimestre    │  │ FK  data_contratacao │  │     sigla_orgao  │
│     semestre     │  │     vl_contrato      │  └──────────────────┘
└──────────────────┘  │     vl_empenhado     │
                      │     vl_liquidado     │
                      │     vl_pago          │
                      │     taxa_execucao    │
                      └──────────┬───────────┘
                                 │
                                 ▼ (1 : N)
                      ┌──────────────────────┐
                      │      fato_itens      │
                      ├──────────────────────┤
                      │ FK  id_contratacao   │
                      │ PK  id_item          │
                      │     descricao_item   │
                      │     qtde_original    │
                      │     vl_unitario      │
                      │     vl_total_item    │
                      │     nome_elemento    │
                      └──────────────────────┘
```

---

## 6. Como Executar o Projeto

### Pré-requisitos
- Python 3.10 ou superior instalado.

### 1. Clonar ou Acessar a Pasta do Projeto
```bash
cd E:\Projetos\desafio_contratos
```

### 2. Criar e Ativar o Ambiente Virtual (Opcional, mas recomendado)
```bash
python -m venv .venv

# No Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o Pipeline Completo
```bash
python main.py
```
O script executará automaticamente todas as etapas em menos de 1 minuto:
1. Ingestão segura dos CSVs brutos (`CONTRATOS.CSV` e `ITENS_CONTRATOS.CSV`).
2. Limpeza, tipagem e deduplicação (Camada Silver).
3. Construção do modelo dimensional e tabela analítica (Camada Gold).
4. Persistência em Parquet e CSV em `data/processed/`.
5. Geração de todas as 7 visualizações analíticas em `reports/figures/`.
6. Exibição do resumo executivo de KPIs no console.

---

## 7. Resumo dos Resultados e Indicadores Chave

- **Total de Contratos:** 130.566 registros válidos.
- **Valor Contratado Total:** **R$ 140,42 bilhões**.
- **Valor Empenhado Total:** **R$ 56,34 bilhões** (40,1% do total contratado).
- **Valor Liquidado Total:** **R$ 32,72 bilhões** (23,3% do total contratado).
- **Valor Pago Total:** **R$ 29,62 bilhões** (21,1% do total contratado).
- **Concentração de Fornecedores (Curva ABC / Pareto):** Apenas **585 empresas** (3,5% do total) representam **80% do valor despendido** pelo Estado.
- **Transição Regulatória:** Adoção expressiva da **Nova Lei de Licitações (Lei nº 14.133/2021)** a partir de 2023, substituindo o regime da Lei nº 8.666/1993.

> 📊 O detalhamento analítico aprofundado, gráficos e interpretações estão disponíveis em:  
> [`reports/relatorio_final.md`](reports/relatorio_final.md)

---

## 8. Conformidade com os Critérios de Avaliação

| Critério de Avaliação | Como foi Atendido no Repositório |
| :--- | :--- |
| **Qualidade do ETL** | Arquitetura modular (`extract`, `transform`, `model`, `load`) com logs, tipagem estrita, isolamento de parâmetros e execução em 55 segundos. |
| **Consistência dos Dados Tratados** | Resolução de anomalias em datas (anos 8202/9201), reparo de CNPJs com zeros perdidos, parsing monetário tolerante a múltiplos padrões e tratamento de estornos negativos. |
| **Relacionamento entre as Bases** | Validação de integridade referencial 1:N entre contratos e itens (0 contratos sem itens e 0 itens órfãos). Modelagem Star Schema com Fatos e Dimensões. |
| **Relevância das Análises Realizadas** | Funil orçamentário real (Contratado $\rightarrow$ Empenhado $\rightarrow$ Liquidado $\rightarrow$ Pago), Curva de Pareto de concentração de fornecedores, transição legislativa e sazonalidade. |
| **Clareza das Visualizações** | 7 gráficos com identidade visual padronizada, eixos formatados em bilhões (R$ B), rótulos de dados diretos e exportação em 300 DPI. |
| **Interpretação dos Resultados** | Relatório executivo completo fundamentado na dinâmica das contas públicas e compras governamentais do Estado do Rio de Janeiro. |
| **Organização do Código** | Estrutura de pastas profissional (`src/`, `data/`, `reports/`, `notebooks/`), scripts desacoplados, `main.py` orquestrador, `requirements.txt` e `README.md`. |
