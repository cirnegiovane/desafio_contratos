"""
Módulo de Análise de Dados e Indicadores de Negócio
Calcula KPIs orçamentários, métricas de concentração e consistência dos dados.
"""
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Analysis")

def calcular_indicadores_financeiros(df_contratos: pd.DataFrame) -> dict:
    """Calcula os principais KPIs de execução orçamentária."""
    vl_contratado_total = df_contratos['vl_contrato'].sum()
    vl_empenhado_total = df_contratos['vl_empenhado_calc'].sum()
    vl_liquidado_total = df_contratos['vl_liquidado_calc'].sum()
    vl_pago_total = df_contratos['vl_pago_calc'].sum()
    
    kpis = {
        'total_contratos': len(df_contratos),
        'vl_contratado_total': vl_contratado_total,
        'vl_empenhado_total': vl_empenhado_total,
        'vl_liquidado_total': vl_liquidado_total,
        'vl_pago_total': vl_pago_total,
        'ticket_medio_contrato': df_contratos['vl_contrato'].mean(),
        'mediana_contrato': df_contratos['vl_contrato'].median(),
        'taxa_empenho_pct': (vl_empenhado_total / vl_contratado_total) * 100,
        'taxa_liquidacao_pct': (vl_liquidado_total / vl_contratado_total) * 100,
        'taxa_pagamento_pct': (vl_pago_total / vl_contratado_total) * 100,
        'taxa_liquidado_sobre_empenhado_pct': (vl_liquidado_total / vl_empenhado_total) * 100,
        'taxa_pago_sobre_liquidado_pct': (vl_pago_total / vl_liquidado_total) * 100
    }
    return kpis

def calcular_concentracao_pareto(df_contratos: pd.DataFrame) -> dict:
    """Calcula indicadores de concentração de fornecedores (Princípio de Pareto)."""
    forn_agg = df_contratos.groupby('fornecedor_nome')['vl_contrato'].sum().sort_values(ascending=False).reset_index()
    total_gasto = forn_agg['vl_contrato'].sum()
    forn_agg['pct_acumulado'] = (forn_agg['vl_contrato'].cumsum() / total_gasto) * 100
    
    qtd_total_forn = len(forn_agg)
    top10_share = forn_agg.head(10)['vl_contrato'].sum() / total_gasto * 100
    top50_share = forn_agg.head(50)['vl_contrato'].sum() / total_gasto * 100
    top100_share = forn_agg.head(100)['vl_contrato'].sum() / total_gasto * 100
    
    # 80% do gasto
    idx_80 = forn_agg[forn_agg['pct_acumulado'] >= 80].index.min() + 1
    pct_forn_80 = (idx_80 / qtd_total_forn) * 100
    
    return {
        'total_fornecedores_distintos': qtd_total_forn,
        'top10_fornecedores_share_pct': top10_share,
        'top50_fornecedores_share_pct': top50_share,
        'top100_fornecedores_share_pct': top100_share,
        'qtd_fornecedores_80pct_gasto': idx_80,
        'pct_fornecedores_80pct_gasto': pct_forn_80
    }

def gerar_relatorio_metricas(df_contratos: pd.DataFrame, df_itens: pd.DataFrame) -> dict:
    """Gera um resumo de todas as métricas para alimentar o relatório."""
    logger.info("Calculando métricas analíticas e de negócio...")
    kpis = calcular_indicadores_financeiros(df_contratos)
    pareto = calcular_concentracao_pareto(df_contratos)
    
    # top5 fornecedores
    top5_forn = df_contratos.groupby('fornecedor_nome')['vl_contrato'].sum().sort_values(ascending=False).head(5)
    
    # top5 órgãos
    top5_orgaos = df_contratos.groupby('sigla_orgao')['vl_contrato'].sum().sort_values(ascending=False).head(5)
    
    # regime jurídico
    regimes = df_contratos.groupby('regime_juridico').agg(
        qtd=('id_contratacao', 'count'),
        valor=('vl_contrato', 'sum')
    ).reset_index()
    
    relatorio = {
        'kpis_financeiros': kpis,
        'concentracao_pareto': pareto,
        'top5_fornecedores': top5_forn.to_dict(),
        'top5_orgaos': top5_orgaos.to_dict(),
        'distribuicao_regimes': regimes.to_dict(orient='records')
    }
    return relatorio
