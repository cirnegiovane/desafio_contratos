"""
Módulo de Visualização e Storytelling de Dados
Gera gráficos executivos em alta resolução (300 DPI) para o relatório final.
"""
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from src.config import FIGURES_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETL_Visualize")

# Configuração de Estilo Visual
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({
    'font.sans-serif': 'Arial',
    'axes.edgecolor': '#cccccc',
    'axes.linewidth': 0.8,
    'grid.color': '#ebebeb',
    'grid.linestyle': '--',
    'figure.autolayout': True
})

def formatar_bilhoes(val, pos):
    """Formata valores em Bilhões de Reais."""
    if abs(val) >= 1e9:
        return f"R$ {val*1e-9:.1f}B"
    elif abs(val) >= 1e6:
        return f"R$ {val*1e-6:.0f}M"
    else:
        return f"R$ {val:,.0f}"

def gerar_grafico_funil_orcamentario(df_contratos: pd.DataFrame, pasta_saida: Path = FIGURES_DIR):
    """Gera visualização do Funil da Execução da Despesa Pública."""
    logger.info("Gerando gráfico: 01_funil_execucao_orcamentaria.png...")
    
    tot_contratado = df_contratos['vl_contrato'].sum()
    tot_empenhado = df_contratos['vl_empenhado_calc'].sum()
    tot_liquidado = df_contratos['vl_liquidado_calc'].sum()
    tot_pago = df_contratos['vl_pago_calc'].sum()
    
    etapas = ['Valor Contratado', 'Valor Empenhado', 'Valor Liquidado', 'Valor Pago']
    valores = [tot_contratado, tot_empenhado, tot_liquidado, tot_pago]
    percentuais = [(v / tot_contratado) * 100 for v in valores]
    
    cores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    barras = ax.bar(etapas, valores, color=cores, width=0.55, edgecolor='none')
    
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(formatar_bilhoes))
    ax.set_title("Funil de Execução da Despesa Pública do Estado do RJ", fontsize=15, fontweight='bold', pad=15)
    ax.set_ylabel("Valor Total Acumulado (R$)", fontsize=12)
    
    for barra, valor, pct in zip(barras, valores, percentuais):
        altura = barra.get_height()
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            altura + (tot_contratado * 0.02),
            f"R$ {valor*1e-9:.2f} B\n({pct:.1f}%)",
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='#222222'
        )
    
    ax.set_ylim(0, tot_contratado * 1.18)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    caminho = pasta_saida / "01_funil_execucao_orcamentaria.png"
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Salvo: {caminho.name}")

def gerar_grafico_top_fornecedores(df_contratos: pd.DataFrame, pasta_saida: Path = FIGURES_DIR):
    """Gera o ranking e a Curva ABC (Pareto) dos 10 maiores fornecedores."""
    logger.info("Gerando gráfico: 02_top_10_fornecedores_pareto.png...")
    
    forn_agg = df_contratos.groupby('fornecedor_nome')['vl_contrato'].sum().reset_index()
    forn_agg = forn_agg.sort_values(by='vl_contrato', ascending=False).reset_index(drop=True)
    
    total_geral = forn_agg['vl_contrato'].sum()
    forn_agg['pct_acumulado'] = (forn_agg['vl_contrato'].cumsum() / total_geral) * 100
    
    top10 = forn_agg.head(10).copy()
    # Encurtar nomes muito longos para legibilidade
    top10['forn_curto'] = top10['fornecedor_nome'].apply(lambda x: x[:32] + '...' if len(x) > 32 else x)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    cores = sns.color_palette("Blues_r", n_colors=10)
    barras = ax1.barh(top10['forn_curto'][::-1], top10['vl_contrato'][::-1], color=cores[::-1], height=0.6)
    
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(formatar_bilhoes))
    ax1.set_xlabel("Valor Total Contratado (R$)", fontsize=12)
    ax1.set_title("Top 10 Fornecedores do Estado do RJ por Valor Contratado", fontsize=15, fontweight='bold', pad=15)
    
    for barra in barras:
        largura = barra.get_width()
        ax1.text(
            largura + (top10['vl_contrato'].max() * 0.01),
            barra.get_y() + barra.get_height() / 2,
            f"R$ {largura*1e-9:.2f} B",
            va='center', ha='left', fontsize=9.5, fontweight='bold'
        )
        
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    caminho = pasta_saida / "02_top_10_fornecedores_pareto.png"
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Salvo: {caminho.name}")

def gerar_grafico_top_orgaos(df_contratos: pd.DataFrame, pasta_saida: Path = FIGURES_DIR):
    """Gera visualização dos 10 maiores órgãos compradores."""
    logger.info("Gerando gráfico: 03_top_10_orgaos_compradores.png...")
    
    orgaos_agg = df_contratos.groupby('sigla_orgao').agg(
        vl_total=('vl_contrato', 'sum'),
        qtd_contratos=('id_contratacao', 'count')
    ).reset_index()
    
    # Remover órgãos não identificados
    orgaos_agg = orgaos_agg[orgaos_agg['sigla_orgao'] != 'NÃO INFORMADO']
    top10_orgaos = orgaos_agg.sort_values(by='vl_total', ascending=False).head(10).reset_index(drop=True)
    
    fig, ax = plt.subplots(figsize=(11, 6))
    barras = ax.bar(top10_orgaos['sigla_orgao'], top10_orgaos['vl_total'], color='#2b5c8f', width=0.6)
    
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(formatar_bilhoes))
    ax.set_title("Top 10 Órgãos / Secretarias com Maior Volume Contratado", fontsize=15, fontweight='bold', pad=15)
    ax.set_ylabel("Valor Contratado (R$)", fontsize=12)
    plt.xticks(rotation=30, ha='right', fontsize=10)
    
    for barra in barras:
        altura = barra.get_height()
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            altura + (top10_orgaos['vl_total'].max() * 0.015),
            f"R$ {altura*1e-9:.2f}B",
            ha='center', va='bottom', fontsize=9.5, fontweight='bold'
        )
        
    ax.set_ylim(0, top10_orgaos['vl_total'].max() * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    caminho = pasta_saida / "03_top_10_orgaos_compradores.png"
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Salvo: {caminho.name}")

def gerar_grafico_evolucao_regime(df_contratos: pd.DataFrame, pasta_saida: Path = FIGURES_DIR):
    """Gera visualização da transição regulatória (Lei 8.666/93 vs Lei 14.133/21)."""
    logger.info("Gerando gráfico: 04_evolucao_regime_juridico.png...")
    
    df_temp = df_contratos[(df_contratos['ano_contratacao'] >= 2018) & (df_contratos['ano_contratacao'] <= 2026)].copy()
    
    reg_ano = df_temp.groupby(['ano_contratacao', 'regime_juridico'])['id_contratacao'].count().unstack().fillna(0)
    
    fig, ax = plt.subplots(figsize=(11, 6))
    reg_ano.plot(kind='bar', stacked=True, ax=ax, colormap='tab10', width=0.65)
    
    ax.set_title("Transição do Marco Regulatório nas Compras Públicas (2018 - 2026)", fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel("Ano da Contratação", fontsize=12)
    ax.set_ylabel("Quantidade de Contratos", fontsize=12)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    plt.xticks(rotation=0)
    ax.legend(title="Regime Jurídico", loc="upper left", frameon=True)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    caminho = pasta_saida / "04_evolucao_regime_juridico.png"
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Salvo: {caminho.name}")

def gerar_grafico_sazonalidade(df_contratos: pd.DataFrame, pasta_saida: Path = FIGURES_DIR):
    """Gera visualização do volume contratado por mês (corrida orçamentária)."""
    logger.info("Gerando gráfico: 05_sazonalidade_mensal_gastos.png...")
    
    df_valid = df_contratos[df_contratos['mes_contratacao'].notna()].copy()
    meses_agg = df_valid.groupby('mes_contratacao')['vl_contrato'].sum().reset_index()
    
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    meses_agg['nome_mes'] = meses_agg['mes_contratacao'].apply(lambda m: nomes_meses[int(m)-1])
    
    fig, ax = plt.subplots(figsize=(11, 6))
    # Destacar o mês de pico (Dezembro/Novembro) com cor contrastante
    max_val = meses_agg['vl_contrato'].max()
    cores = ['#d9534f' if v == max_val else '#337ab7' for v in meses_agg['vl_contrato']]
    
    barras = ax.bar(meses_agg['nome_mes'], meses_agg['vl_contrato'], color=cores, width=0.6)
    
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(formatar_bilhoes))
    ax.set_title("Sazonalidade das Contratações: Volume Financeiro por Mês do Ano", fontsize=15, fontweight='bold', pad=15)
    ax.set_ylabel("Valor Total Contratado (R$)", fontsize=12)
    ax.set_xlabel("Mês do Calendário", fontsize=12)
    
    for barra in barras:
        altura = barra.get_height()
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            altura + (max_val * 0.015),
            f"R$ {altura*1e-9:.1f}B",
            ha='center', va='bottom', fontsize=9, fontweight='bold'
        )
        
    ax.set_ylim(0, max_val * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    caminho = pasta_saida / "05_sazonalidade_mensal_gastos.png"
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Salvo: {caminho.name}")

def gerar_grafico_modalidades(df_contratos: pd.DataFrame, pasta_saida: Path = FIGURES_DIR):
    """Gera visualização da distribuição das modalidades de contratação."""
    logger.info("Gerando gráfico: 06_distribuicao_modalidades.png...")
    
    mod_agg = df_contratos.groupby('categoria_modalidade').agg(
        qtd=('id_contratacao', 'count'),
        valor=('vl_contrato', 'sum')
    ).reset_index().sort_values(by='valor', ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Gráfico 1: Quantidade
    cores = sns.color_palette("Set2", n_colors=len(mod_agg))
    ax1.pie(
        mod_agg['qtd'],
        labels=mod_agg['categoria_modalidade'],
        autopct='%1.1f%%',
        startangle=140,
        colors=cores,
        textprops={'fontsize': 10}
    )
    ax1.set_title("Distribuição por Quantidade de Contratos", fontsize=13, fontweight='bold')
    
    # Gráfico 2: Valor Financeiro
    ax2.pie(
        mod_agg['valor'],
        labels=mod_agg['categoria_modalidade'],
        autopct='%1.1f%%',
        startangle=140,
        colors=cores,
        textprops={'fontsize': 10}
    )
    ax2.set_title("Distribuição por Volume Financeiro (R$)", fontsize=13, fontweight='bold')
    
    fig.suptitle("Procedimentos de Aquisição: Competitivos vs Contratação Direta", fontsize=15, fontweight='bold', y=1.02)
    
    caminho = pasta_saida / "06_distribuicao_modalidades.png"
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Salvo: {caminho.name}")

def gerar_grafico_elementos_despesa(df_itens: pd.DataFrame, pasta_saida: Path = FIGURES_DIR):
    """Gera visualização dos gastos por Classificação Orçamentária da Despesa."""
    logger.info("Gerando gráfico: 07_elementos_despesa_publica.png...")
    
    elem_agg = df_itens.groupby('nome_elemento_despesa')['vl_total_item'].sum().reset_index()
    elem_agg = elem_agg.sort_values(by='vl_total_item', ascending=False).head(8)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    barras = ax.barh(elem_agg['nome_elemento_despesa'][::-1], elem_agg['vl_total_item'][::-1], color='#3b7a57', height=0.6)
    
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(formatar_bilhoes))
    ax.set_title("Maiores Grupos de Despesa Orçamentária nos Itens Contratados", fontsize=15, fontweight='bold', pad=15)
    ax.set_xlabel("Valor Total dos Itens (R$)", fontsize=12)
    
    for barra in barras:
        largura = barra.get_width()
        ax.text(
            largura + (elem_agg['vl_total_item'].max() * 0.01),
            barra.get_y() + barra.get_height() / 2,
            f"R$ {largura*1e-9:.2f} B",
            va='center', ha='left', fontsize=9.5, fontweight='bold'
        )
        
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    caminho = pasta_saida / "07_elementos_despesa_publica.png"
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Salvo: {caminho.name}")

def executar_visualizacoes(df_contratos: pd.DataFrame, df_itens: pd.DataFrame):
    """Orquestrador da geração de todas as visualizações executivas."""
    logger.info("Iniciando geração de gráficos em alta resolução...")
    gerar_grafico_funil_orcamentario(df_contratos)
    gerar_grafico_top_fornecedores(df_contratos)
    gerar_grafico_top_orgaos(df_contratos)
    gerar_grafico_evolucao_regime(df_contratos)
    gerar_grafico_sazonalidade(df_contratos)
    gerar_grafico_modalidades(df_contratos)
    gerar_grafico_elementos_despesa(df_itens)
    logger.info("Todas as 7 visualizações foram geradas com sucesso!")
