"""
Módulo de Modelagem Dimensional (Camada Gold)
Implementa o relacionamento consistente entre os conjuntos de dados de Contratos e Itens Contratados.
"""
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Model")

def criar_dimensoes_e_fatos(df_contratos: pd.DataFrame, df_itens: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Constrói as tabelas de Dimensão e Fato seguindo a modelagem dimensional.
    """
    logger.info("Iniciando construção do modelo dimensional (Star Schema)...")
    
    dim_fornecedor = df_contratos[[
        'id_fornecedor', 'fornecedor_nome', 'cpf_cnpj_limpo', 'tipo_documento'
    ]].drop_duplicates(subset=['id_fornecedor', 'cpf_cnpj_limpo']).copy()
    dim_fornecedor = dim_fornecedor.reset_index(drop=True)
    
    
    dim_orgao = df_contratos[[
        'id_ug', 'cod_ug', 'unidade_nome', 'sigla_orgao'
    ]].drop_duplicates(subset=['id_ug']).copy()
    dim_orgao = dim_orgao.reset_index(drop=True)
    
    
    datas_unicas = df_contratos['data_contratacao'].dropna().drop_duplicates().sort_values()
    dim_tempo = pd.DataFrame({'data': datas_unicas})
    dim_tempo['ano'] = dim_tempo['data'].dt.year
    dim_tempo['mes'] = dim_tempo['data'].dt.month
    dim_tempo['nome_mes'] = dim_tempo['data'].dt.strftime('%B')
    dim_tempo['trimestre'] = dim_tempo['data'].dt.quarter
    dim_tempo['semestre'] = (dim_tempo['data'].dt.month <= 6).map({True: 1, False: 2})
    dim_tempo['ano_mes'] = dim_tempo['data'].dt.to_period('M').astype(str)
    dim_tempo = dim_tempo.reset_index(drop=True)
    
    
    fato_contratos = df_contratos[[
        'id_contratacao', 'id_contrato_seq', 'id_fornecedor', 'id_ug',
        'data_contratacao', 'status_contratacao', 'regime_juridico',
        'tipo_aquisicao', 'categoria_modalidade', 'criterio_julgamento',
        'vl_contrato', 'vl_empenhado_calc', 'vl_liquidado_calc', 'vl_pago_calc',
        'taxa_execucao_paga_pct', 'dias_vigencia', 'possui_empenho', 'possui_liquidacao', 'possui_pagamento'
    ]].copy()
    fato_contratos = fato_contratos.rename(columns={
        'vl_empenhado_calc': 'vl_empenhado',
        'vl_liquidado_calc': 'vl_liquidado',
        'vl_pago_calc': 'vl_pago'
    })
    
    
    fato_itens = df_itens[[
        'id_contratacao', 'id_item', 'descricao_item', 'id_ata',
        'qtde_original', 'vl_unitario_original', 'vl_total_item',
        'cd_elemento_6d', 'nome_elemento_despesa'
    ]].copy()
    
    
    logger.info("Criando dataset analítico integrado (Contratos + Itens agregados)...")
    itens_resumo = df_itens.groupby('id_contratacao').agg(
        qtd_itens_total=('id_item', 'count'),
        vl_itens_total=('vl_total_item', 'sum'),
        principal_elemento_despesa=('nome_elemento_despesa', lambda x: x.mode().iloc[0] if not x.empty else 'OUTROS')
    ).reset_index()
    
    df_analitico = df_contratos.merge(itens_resumo, on='id_contratacao', how='left')
    df_analitico['vl_itens_total'] = df_analitico['vl_itens_total'].fillna(0.0)
    df_analitico['qtd_itens_total'] = df_analitico['qtd_itens_total'].fillna(0).astype(int)
    
    modelo = {
        'dim_fornecedor': dim_fornecedor,
        'dim_orgao': dim_orgao,
        'dim_tempo': dim_tempo,
        'fato_contratos': fato_contratos,
        'fato_itens': fato_itens,
        'df_analitico': df_analitico
    }
    
    logger.info("Modelagem dimensional concluída com sucesso:")
    for nome, df_tab in modelo.items():
        logger.info(f"  - {nome}: {len(df_tab):,} registros, {df_tab.shape[1]} colunas.")
        
    return modelo
