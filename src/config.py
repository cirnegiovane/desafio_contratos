"""
Módulo de Configurações e Parâmetros do Projeto
ETL e Análise de Contratos Públicos - Estado do Rio de Janeiro
"""
from pathlib import Path

# diretorios
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

# arquivos raw
CONTRATOS_RAW_PATH = RAW_DATA_DIR / "CONTRATOS.CSV"
ITENS_RAW_PATH = RAW_DATA_DIR / "ITENS_CONTRATOS.CSV"

# leitura
RAW_ENCODING = "latin1"
RAW_SEP = ";"

# limite cronológico
ANO_MINIMO_VALIDO = 2000
ANO_MAXIMO_VALIDO = 2035

# existência das pastas
for folder in [RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR, NOTEBOOKS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
