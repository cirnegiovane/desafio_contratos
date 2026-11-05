"""
Notebook Script: Análise Exploratória Interativa de Dados
Portal de Compras do Estado do Rio de Janeiro
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

def main():
    print("=== Carregando Tabelas Tratadas (Camada Gold) ===")
    df_contratos = pd.read_parquet(PROCESSED_DIR / "fato_contratos.parquet")
    df_fornecedores = pd.read_parquet(PROCESSED_DIR / "dim_fornecedor.parquet")
    df_orgaos = pd.read_parquet(PROCESSED_DIR / "dim_orgao.parquet")
    df_itens = pd.read_parquet(PROCESSED_DIR / "fato_itens.parquet")
    
    print(f"Contratos: {len(df_contratos):,} linhas")
    print(f"Fornecedores: {len(df_fornecedores):,} linhas")
    print(f"Órgãos: {len(df_orgaos):,} linhas")
    print(f"Itens: {len(df_itens):,} linhas")
    
    print("\n--- Estatísticas Descritivas dos Valores dos Contratos ---")
    print(df_contratos[['vl_contrato', 'vl_empenhado', 'vl_liquidado', 'vl_pago']].describe())

if __name__ == "__main__":
    main()
