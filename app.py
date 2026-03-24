import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import os

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")
st.title("📊 Dashboard de Consumo - Energia e Água")

# ---------------- CAMINHO DINÂMICO (CORREÇÃO PRINCIPAL) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# tenta encontrar automaticamente o arquivo Excel
arquivos = os.listdir(BASE_DIR)
arquivo_excel = None

for f in arquivos:
    if f.endswith(".xlsx") or f.endswith(".xls"):
        arquivo_excel = os.path.join(BASE_DIR, f)
        break

# validação
if arquivo_excel is None:
    st.error("❌ Nenhum arquivo Excel encontrado na pasta do projeto")
    st.stop()

# DEBUG (pode remover depois)
with st.expander("🔍 Debug (arquivos disponíveis)"):
    st.write("Diretório:", BASE_DIR)
    st.write("Arquivos:", arquivos)
    st.write("Arquivo usado:", arquivo_excel)

# ---------------- LEITURA ----------------
df = pd.read_excel(arquivo_excel, sheet_name='Planilha2', header=[0,1])

# ---------------- FUNÇÃO OUTLIER ----------------
def calcular_outliers(dados):
    if len(dados) < 4:
        return []
    q1 = np.percentile(dados, 25)
    q3 = np.percentile(dados, 75)
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    return [x for x in dados if x < lim_inf or x > lim_sup]

# ---------------- TRANSFORMAR DADOS ----------------
dados = []

for unidade in df.columns.levels[0]:
    try:
        energia = df[unidade]['Energia'].dropna()
        agua = df[unidade]['Agua'].dropna()

        for v in energia:
            dados.append([unidade, 'Energia', v])

        for v in agua:
            dados.append([unidade, 'Água', v])

    except:
        continue

df_long = pd.DataFrame(dados, columns=['Unidade','Tipo','Valor'])

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filtros")

unidades = st.sidebar.multiselect(
    "Selecione as unidades:",
    options=df_long['Unidade'].unique(),
    default=df_long['Unidade'].unique()
)

tipos = st.sidebar.multiselect(
    "Tipo:",
    options=df_long['Tipo'].unique(),
    default=df_long['Tipo'].unique()
)

df_filtrado = df_long[
    (df_long['Unidade'].isin(unidades)) &
    (df_long['Tipo'].isin(tipos))
]

# ---------------- KPIs ----------------
col1, col2, col3 = st.columns(3)

col1.metric("💰 Consumo Médio", f"{df_filtrado['Valor'].mean():,.2f}")
col2.metric("📊 Total Registros", len(df_filtrado))
col3.metric("🏢 Unidades", df_filtrado['Unidade'].nunique())

# ---------------- BOXPLOT ----------------
st.subheader("📦 Boxplot Geral")

fig_box = px.box(
    df_filtrado,
    x="Unidade",
    y="Valor",
    color="Tipo"
)

fig_box.update_layout(xaxis_tickangle=90)

st.plotly_chart(fig_box, width='stretch')

# ---------------- RANKING SEPARADO ----------------
st.subheader("🏆 Ranking por Tipo")

ranking = df_filtrado.groupby(['Unidade','Tipo'])['Valor'].mean().reset_index()

fig_rank = px.bar(
    ranking,
    x='Unidade',
    y='Valor',
    color='Tipo',
    barmode='group'
)

fig_rank.update_layout(xaxis_tickangle=90)

st.plotly_chart(fig_rank, width='stretch')

# ---------------- OUTLIERS POR TIPO ----------------
st.subheader("🚨 Outliers por Unidade e Tipo")

outlier_data = []

for unidade in df_filtrado['Unidade'].unique():
    for tipo in ['Energia', 'Água']:
        dados_u = df_filtrado[
            (df_filtrado['Unidade'] == unidade) &
            (df_filtrado['Tipo'] == tipo)
        ]['Valor']

        out = calcular_outliers(dados_u)

        outlier_data.append([unidade, tipo, len(out)])

df_out = pd.DataFrame(outlier_data, columns=['Unidade','Tipo','Outliers'])

# LIMIAR
limite = st.sidebar.slider("Limite de alerta (outliers)", 0, 20, 2)

df_out['Alerta'] = df_out['Outliers'] > limite

fig_out = px.bar(
    df_out,
    x='Unidade',
    y='Outliers',
    color='Alerta',
    facet_col='Tipo'
)

fig_out.update_layout(xaxis_tickangle=90)

st.plotly_chart(fig_out, width='stretch')

# ---------------- ALERTAS ----------------
st.subheader("⚠️ Alertas Inteligentes")

for _, row in df_out.iterrows():
    if row['Outliers'] > limite:
        st.error(f"🚨 {row['Unidade']} - {row['Tipo']} com {row['Outliers']} outliers")

# ---------------- IA SIMPLES ----------------
st.subheader("🤖 Diagnóstico Inteligente")

for _, row in df_out.iterrows():
    if row['Outliers'] > limite:

        if row['Tipo'] == 'Água':
            causa = "Possível vazamento ou consumo fora do padrão"
        else:
            causa = "Possível uso excessivo ou falha elétrica"

        st.warning(f"{row['Unidade']} ({row['Tipo']}): {causa}")
