"""
Módulo de Transformação e Limpeza (Camada Silver)
Padronização de esquemas, parsing monetário, sanitização de documentos,
tratamento de nulos, desduplicação e enriquecimento de dados públicos.
"""
import re
import logging
import numpy as np
import pandas as pd
from src.config import ANO_MINIMO_VALIDO, ANO_MAXIMO_VALIDO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Transform")

# Dicionário descritivo dos Elementos de Despesa Orçamentária (Portaria STN/SOF nº 163)
ELEMENTOS_DESPESA_MAP = {
    "339030": "Material de Consumo",
    "339039": "Outros Serviços de Terceiros - PJ",
    "339040": "Serviços de TIC",
    "449052": "Equipamentos e Material Permanente",
    "339036": "Outros Serviços de Terceiros - PF",
    "339037": "Locação de Mão-de-Obra",
    "339033": "Passagens e Despesas com Locomoção",
    "449051": "Obras e Instalações",
    "339014": "Diárias - Civil",
    "339092": "Despesas de Exercícios Anteriores",
    "339093": "Indenizações e Restituições",
    "339032": "Material, Bem ou Serviço para Distribuição Gratuita"
}

def normalizar_nome_coluna(col: str) -> str:
    """Padroniza nomes de colunas para snake_case sem acentuações ou caracteres especiais."""
    c = str(col).strip().lower()
    c = re.sub(r'[áàâã]', 'a', c)
    c = re.sub(r'[éèê]', 'e', c)
    c = re.sub(r'[íìî]', 'i', c)
    c = re.sub(r'[óòôõ]', 'o', c)
    c = re.sub(r'[úùû]', 'u', c)
    c = re.sub(r'[ç]', 'c', c)
    c = re.sub(r'[^a-z0-9_]', '_', c)
    c = re.sub(r'_+', '_', c).strip('_')
    return c

def converter_moeda_br(val) -> float:
    """Converte valores no padrão monetário brasileiro para float."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace('R$', '').replace(' ', '')
    if not s or s.lower() in ('nan', 'none', 'null'):
        return np.nan
    
    # Ex: '1.498.939,00' -> '1498939.00'
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    
    try:
        return float(s)
    except ValueError:
        return np.nan

def sanitizar_documento(doc: str) -> tuple[str, str]:
    """Limpa e formata CPF/CNPJ, recuperando zeros à esquerda perdidos."""
    if pd.isna(doc):
        return "NÃO INFORMADO", "NÃO INFORMADO"
    
    digits = re.sub(r'\D', '', str(doc))
    n = len(digits)
    
    if n == 14:
        return digits, "CNPJ"
    elif n == 13:
        # Zero à esquerda perdido na exportação
        return digits.zfill(14), "CNPJ"
    elif n == 11:
        return digits, "CPF"
    elif n > 0:
        return digits, "OUTROS"
    else:
        return "NÃO INFORMADO", "NÃO INFORMADO"

def sanitizar_data(serie: pd.Series) -> pd.Series:
    """Converte strings para datetime e invalida anos fora da janela plausível."""
    dt = pd.to_datetime(serie, format='%d/%m/%Y', errors='coerce')
    # Anular anomalias de digitação (ex: ano 8202 ou 9201)
    filtro_anomalo = (dt.dt.year < ANO_MINIMO_VALIDO) | (dt.dt.year > ANO_MAXIMO_VALIDO)
    dt[filtro_anomalo] = pd.NaT
    return dt

def categorizar_modalidade(tipo: str) -> str:
    """Classifica a contratação em Competitiva, Direta ou Outros."""
    if not isinstance(tipo, str):
        return "NÃO INFORMADO"
    t = tipo.lower()
    if "preg" in t or "concorr" in t or "licita" in t:
        return "Competitiva (Licitação/Pregão)"
    elif "dispensa" in t or "pequenas compras" in t:
        return "Contratação Direta (Dispensa)"
    elif "inexigibilidade" in t:
        return "Contratação Direta (Inexigibilidade)"
    elif "ades" in t or "ata" in t:
        return "Adesão a Ata (Carona)"
    else:
        return "Outros Procedimentos"

def extrair_sigla_orgao(unidade: str) -> str:
    """Extrai a sigla da secretaria/órgão do texto da Unidade (ex: 'PMERJ - POLICIA MILITAR...')."""
    if not isinstance(unidade, str) or not unidade.strip():
        return "NÃO INFORMADO"
    parts = unidade.split('-')
    if len(parts) > 1 and len(parts[0].strip()) <= 15:
        return parts[0].strip()
    return unidade[:20].strip()

def transformar_contratos(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas as transformações da camada Silver na base de Contratos."""
    logger.info("Iniciando transformação e limpeza de CONTRATOS...")
    df = df_raw.copy()
    
    # 1. Normalização de Nomes de Colunas
    df.columns = [normalizar_nome_coluna(c) for c in df.columns]
    
    # Mapeamento semântico
    rename_dict = {
        'codigo_do_contrato': 'id_contrato_seq',
        'contratacao': 'id_contratacao',
        'unidade': 'unidade_nome',
        'idug': 'id_ug',
        'codug': 'cod_ug',
        'processo': 'numero_processo',
        'objeto': 'objeto_contrato',
        'tipo_de_aquisicao': 'tipo_aquisicao',
        'criterio_de_julgamento': 'criterio_julgamento',
        'id_forn': 'id_fornecedor',
        'fornecedor': 'fornecedor_nome',
        'valor_total_contrato_valor_estimado_para_contratacao_r': 'vl_contrato',
        'valor_total_empenhado_r': 'vl_empenhado',
        'valor_total_liquidado_r': 'vl_liquidado',
        'valor_total_pago_r': 'vl_pago',
        'data_public_deorj': 'data_publicacao_deorj'
    }
    df = df.rename(columns=rename_dict)
    
    # 2. Tipagem Numérica / Financeira
    cols_moeda = ['vl_contrato', 'vl_empenhado', 'vl_liquidado', 'vl_pago']
    for col in cols_moeda:
        if col in df.columns:
            df[col] = df[col].apply(converter_moeda_br)
    
    # Flags de execução orçamentária
    df['possui_empenho'] = df['vl_empenhado'].notna() & (df['vl_empenhado'] > 0)
    df['possui_liquidacao'] = df['vl_liquidado'].notna() & (df['vl_liquidado'] > 0)
    df['possui_pagamento'] = df['vl_pago'].notna() & (df['vl_pago'] > 0)
    
    # Versões zeradas para cálculo contábil
    df['vl_empenhado_calc'] = df['vl_empenhado'].fillna(0.0)
    df['vl_liquidado_calc'] = df['vl_liquidado'].fillna(0.0)
    df['vl_pago_calc'] = df['vl_pago'].fillna(0.0)
    
    # Razão de Execução Financeira (Pago / Contratado)
    df['taxa_execucao_paga_pct'] = np.where(
        df['vl_contrato'] > 0,
        (df['vl_pago_calc'] / df['vl_contrato']) * 100,
        0.0
    ).clip(0, 100)
    
    # 3. Tratamento de Datas
    cols_data = ['data_contratacao', 'data_inicio_vigencia', 'data_fim_vigencia', 'data_publicacao_deorj', 'data_assinatura']
    for col in cols_data:
        if col in df.columns:
            df[col] = sanitizar_data(df[col])
            
    # Variáveis temporais derivadas
    df['ano_contratacao'] = df['data_contratacao'].dt.year
    df['mes_contratacao'] = df['data_contratacao'].dt.month
    df['mes_ano_contratacao'] = df['data_contratacao'].dt.to_period('M').astype(str)
    
    # Duração da vigência em dias
    df['dias_vigencia'] = (df['data_fim_vigencia'] - df['data_inicio_vigencia']).dt.days
    df['vigencia_valida'] = df['dias_vigencia'] >= 0
    df.loc[~df['vigencia_valida'], 'dias_vigencia'] = np.nan
    
    # 4. Sanitização de CPF / CNPJ
    docs_info = df['cpf_cnpj'].apply(sanitizar_documento)
    df['cpf_cnpj_limpo'] = [d[0] for d in docs_info]
    df['tipo_documento'] = [d[1] for d in docs_info]
    
    # 5. Tratamento de Textos e Nulos
    df['fornecedor_nome'] = df['fornecedor_nome'].fillna('NÃO INFORMADO').str.strip().str.upper()
    df['objeto_contrato'] = df['objeto_contrato'].fillna('NÃO INFORMADO').str.strip()
    df['tipo_aquisicao'] = df['tipo_aquisicao'].fillna('NÃO INFORMADO').str.strip()
    df['status_contratacao'] = df['status_contratacao'].fillna('NÃO INFORMADO').str.strip()
    df['regime_juridico'] = df['regimejuridico'].fillna('NÃO INFORMADO').str.strip()
    
    # 6. Enriquecimento de Negócio
    df['sigla_orgao'] = df['unidade_nome'].apply(extrair_sigla_orgao)
    df['categoria_modalidade'] = df['tipo_aquisicao'].apply(categorizar_modalidade)
    
    logger.info(f"Transformação de CONTRATOS concluída: {len(df):,} linhas.")
    return df

def transformar_itens(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas as transformações da camada Silver na base de Itens."""
    logger.info("Iniciando transformação e limpeza de ITENS...")
    df = df_raw.copy()
    
    # 1. Normalização de Nomes de Colunas
    df.columns = [normalizar_nome_coluna(c) for c in df.columns]
    
    rename_dict = {
        'contratacao': 'id_contratacao',
        'item': 'descricao_item',
        'vl_unit_original': 'vl_unitario_original',
        'vl_unit_aditivado_suprimido': 'vl_unitario_aditivado',
        'elemento': 'cd_elemento',
        'subelemento': 'cd_subelemento'
    }
    df = df.rename(columns=rename_dict)
    
    # 2. Remoção de Duplicatas Totais
    linhas_antes = len(df)
    df = df.drop_duplicates()
    linhas_removidas = linhas_antes - len(df)
    logger.info(f"Deduplicação: {linhas_removidas:,} linhas 100% duplicadas foram removidas de ITENS.")
    
    # 3. Conversão Numérica
    df['qtde_original'] = df['qtde_original'].apply(converter_moeda_br).fillna(0.0)
    df['vl_unitario_original'] = df['vl_unitario_original'].apply(converter_moeda_br).fillna(0.0)
    df['total_aditivada_suprimida'] = df['total_aditivada_suprimida'].apply(converter_moeda_br).fillna(0.0)
    
    # Valor Total do Item Calculado
    df['vl_total_item'] = (df['qtde_original'] * df['vl_unitario_original']).round(2)
    
    # 4. Tratamento e Mapeamento de Elementos de Despesa
    def parse_codigo_elemento(val):
        if pd.isna(val):
            return "NÃO INFORMADO"
        try:
            # Ex: 33904000.0 -> '339040'
            s = str(int(float(val)))
            return s[:6] if len(s) >= 6 else s
        except (ValueError, TypeError):
            return str(val)[:6]
            
    df['cd_elemento_6d'] = df['cd_elemento'].apply(parse_codigo_elemento)
    df['nome_elemento_despesa'] = df['cd_elemento_6d'].map(ELEMENTOS_DESPESA_MAP).fillna('Outros Elementos Orçamentários')
    
    # Limpeza de texto
    df['descricao_item'] = df['descricao_item'].fillna('NÃO INFORMADO').str.strip().str.upper()
    
    # 5. Consolidação de duplicidades em (id_contratacao, id_item)
    # Agrupar itens com o mesmo ID no mesmo contrato somando quantidades e valor
    dups_count = df.duplicated(subset=['id_contratacao', 'id_item'], keep=False).sum()
    if dups_count > 0:
        logger.info(f"Consolidando {dups_count:,} registros de itens com mesmo (id_contratacao, id_item)...")
        # Manter agregação limpa
        df_agrupado = df.groupby(['id_contratacao', 'id_item'], as_index=False).agg({
            'descricao_item': 'first',
            'id_ata': 'first',
            'qtde_original': 'sum',
            'vl_total_item': 'sum',
            'total_aditivada_suprimida': 'sum',
            'cd_elemento_6d': 'first',
            'nome_elemento_despesa': 'first',
            'data_extracao': 'first'
        })
        # Recalcular valor unitário médio ponderado
        df_agrupado['vl_unitario_original'] = np.where(
            df_agrupado['qtde_original'] > 0,
            (df_agrupado['vl_total_item'] / df_agrupado['qtde_original']).round(4),
            0.0
        )
        df = df_agrupado
    
    logger.info(f"Transformação de ITENS concluída: {len(df):,} linhas válidas.")
    return df

def executar_transformacao(df_contratos_raw: pd.DataFrame, df_itens_raw: pd.DataFrame):
    """Função orquestradora da etapa de transformação."""
    df_contratos = transformar_contratos(df_contratos_raw)
    df_itens = transformar_itens(df_itens_raw)
    return df_contratos, df_itens
