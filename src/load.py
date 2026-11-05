"""
Módulo de Carga (Camada Gold / Load)
Persistência das tabelas tratadas e modeladas nos formatos Parquet e CSV.
"""
import logging
from pathlib import Path
import pandas as pd
from src.config import PROCESSED_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Load")

def salvar_tabela(df: pd.DataFrame, nome: str, pasta_destino: Path = PROCESSED_DATA_DIR):
    """Salva o DataFrame nos formatos Parquet e CSV."""
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    parquet_path = pasta_destino / f"{nome}.parquet"
    csv_path = pasta_destino / f"{nome}.csv"
    
    df.to_parquet(parquet_path, index=False, engine='pyarrow')
    
    df.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig')
    
    size_parquet_mb = parquet_path.stat().st_size / (1024 * 1024)
    size_csv_mb = csv_path.stat().st_size / (1024 * 1024)
    
    logger.info(f"Tabela '{nome}' gravada com sucesso:")
    logger.info(f"  Parquet: {parquet_path.name} ({size_parquet_mb:.2f} MB)")
    logger.info(f"  CSV:     {csv_path.name} ({size_csv_mb:.2f} MB)")

def executar_carga(modelo: dict[str, pd.DataFrame]):
    """Orquestra a persistência de todas as tabelas do modelo dimensional."""
    logger.info("Iniciando persistência dos dados tratados...")
    for nome, df_tabela in modelo.items():
        salvar_tabela(df_tabela, nome)
    logger.info("Carga concluída com sucesso!")
