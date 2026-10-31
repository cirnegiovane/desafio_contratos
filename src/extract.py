"""
Módulo de Extração (Camada Bronze)
Responsável pela ingestão resiliente dos dados brutos dos contratos e itens.
"""
import sys
import logging
import pandas as pd
from pathlib import Path
from src.config import CONTRATOS_RAW_PATH, ITENS_RAW_PATH, RAW_ENCODING, RAW_SEP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Extract")

def extrair_contratos(caminho: Path = CONTRATOS_RAW_PATH) -> pd.DataFrame:
    """Extrai os dados brutos de contratos a partir do arquivo CSV."""
    logger.info(f"Iniciando extração de contratos de: {caminho}")
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    df = pd.read_csv(
        caminho,
        encoding=RAW_ENCODING,
        sep=RAW_SEP,
        dtype=str,  # Leitura segura como string para não perder zeros à esquerda
        low_memory=False
    )
    logger.info(f"Contratos extraídos com sucesso: {len(df):,} linhas, {df.shape[1]} colunas.")
    return df

def extrair_itens(caminho: Path = ITENS_RAW_PATH) -> pd.DataFrame:
    """Extrai os dados brutos de itens contratados a partir do arquivo CSV."""
    logger.info(f"Iniciando extração de itens de: {caminho}")
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    df = pd.read_csv(
        caminho,
        encoding=RAW_ENCODING,
        sep=RAW_SEP,
        dtype=str,
        low_memory=False
    )
    logger.info(f"Itens extraídos com sucesso: {len(df):,} linhas, {df.shape[1]} colunas.")
    return df

def executar_extracao():
    """Função orquestradora da etapa de extração."""
    df_contratos = extrair_contratos()
    df_itens = extrair_itens()
    return df_contratos, df_itens

if __name__ == "__main__":
    executar_extracao()
