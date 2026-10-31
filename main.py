"""
Script Principal de Execução do Pipeline de ETL e Análises
Portal de Compras do Estado do Rio de Janeiro
"""
import sys
import time
import logging
from pathlib import Path

# Adicionar raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.extract import extrair_contratos, extrair_itens
from src.transform import transformar_contratos, transformar_itens
from src.model import criar_dimensoes_e_fatos
from src.load import executar_carga
from src.visualize import executar_visualizacoes
from src.analysis import gerar_relatorio_metricas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Pipeline_Principal")

def main():
    inicio = time.time()
    print("=" * 75)
    print(" PIPELINE DE ETL & ANÁLISE - CONTRATOS PÚBLICOS RJ ")
    print("=" * 75)
    
    # 1. Extração (Bronze)
    print("\n>>> [1/5] ETAPA DE EXTRAÇÃO (Camada Bronze)...")
    df_contratos_raw = extrair_contratos()
    df_itens_raw = extrair_itens()
    
    # 2. Transformação e Qualidade (Silver)
    print("\n>>> [2/5] ETAPA DE TRANSFORMAÇÃO E LIMPEZA (Camada Silver)...")
    df_contratos = transformar_contratos(df_contratos_raw)
    df_itens = transformar_itens(df_itens_raw)
    
    # 3. Modelagem Dimensional (Gold)
    print("\n>>> [3/5] ETAPA DE MODELAGEM DIMENSIONAL (Star Schema)...")
    modelo = criar_dimensoes_e_fatos(df_contratos, df_itens)
    
    # 4. Carga e Persistência
    print("\n>>> [4/5] ETAPA DE CARGA E PERSISTÊNCIA...")
    executar_carga(modelo)
    
    # 5. Visualizações e Storytelling
    print("\n>>> [5/5] ETAPA DE GERAÇÃO DE VISUALIZAÇÕES E STORYTELLING...")
    executar_visualizacoes(df_contratos, df_itens)
    
    # 6. Cálculo de Métricas Executivas
    metricas = gerar_relatorio_metricas(df_contratos, df_itens)
    
    duracao = time.time() - inicio
    print("\n" + "=" * 75)
    print(f" PIPELINE EXECUTADO COM SUCESSO EM {duracao:.2f} SEGUNDOS! ")
    print("=" * 75)
    
    kpis = metricas['kpis_financeiros']
    pareto = metricas['concentracao_pareto']
    print(f"Total de Contratos Processados: {kpis['total_contratos']:,}")
    print(f"Valor Contratado Total:         R$ {kpis['vl_contratado_total']:,.2f}")
    print(f"Valor Empenhado Total:          R$ {kpis['vl_empenhado_total']:,.2f} ({kpis['taxa_empenho_pct']:.1f}%)")
    print(f"Valor Liquidado Total:          R$ {kpis['vl_liquidado_total']:,.2f} ({kpis['taxa_liquidacao_pct']:.1f}%)")
    print(f"Valor Pago Total:               R$ {kpis['vl_pago_total']:,.2f} ({kpis['taxa_pagamento_pct']:.1f}%)")
    print(f"Concentração Top 10 Forn.:      {pareto['top10_fornecedores_share_pct']:.1f}% do valor total")
    print(f"Fornecedores para 80% do Gasto: {pareto['qtd_fornecedores_80pct_gasto']} de {pareto['total_fornecedores_distintos']:,} ({pareto['pct_fornecedores_80pct_gasto']:.1f}%)")
    print("=" * 75)

if __name__ == "__main__":
    main()
