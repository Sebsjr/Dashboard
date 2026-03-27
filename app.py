import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Inteligente - Energia e Água")

arquivo_excel = r'C:\boxplot\dados.xlsx'
LIMITE_OUTLIERS = 3

# ---------------- LEITURA ----------------
df = pd.read_excel(arquivo_excel, sheet_name='Planilha2', header=[0,1])

# ---------------- TRANSFORMAR DADOS ----------------
dados = []

for unidade in df.columns.levels[0]:
    try:
        energia = df[unidade]['Energia'].dropna().reset_index(drop=True)
        agua = df[unidade]['Agua'].dropna().reset_index(drop=True)

        for i, v in enumerate(energia):
            dados.append([unidade, 'Energia', v, i+1])

        for i, v in enumerate(agua):
            dados.append([unidade, 'Água', v, i+1])

    except:
        continue

df_long = pd.DataFrame(dados, columns=['Unidade','Tipo','Valor','Mes'])

# 🔥 MAPA DE MESES
mapa_meses = {
    1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr',
    5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago',
    9:'Set', 10:'Out', 11:'Nov', 12:'Dez'
}

df_long['Mes_nome'] = df_long['Mes'].map(mapa_meses)

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filtros")

unidades = st.sidebar.multiselect(
    "Unidades",
    df_long['Unidade'].unique(),
    default=df_long['Unidade'].unique()
)

tipos = st.sidebar.multiselect(
    "Tipo",
    df_long['Tipo'].unique(),
    default=df_long['Tipo'].unique()
)

meses = st.sidebar.slider(
    "Período (Meses)",
    int(df_long['Mes'].min()),
    int(df_long['Mes'].max()),
    (1, int(df_long['Mes'].max()))
)

df_filtrado = df_long[
    (df_long['Unidade'].isin(unidades)) &
    (df_long['Tipo'].isin(tipos)) &
    (df_long['Mes'] >= meses[0]) &
    (df_long['Mes'] <= meses[1])
]

# ---------------- ABAS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Dashboard", "🏆 Ranking", "🚨 Alertas", "🤖 Diagnóstico IA", "📈 Previsão"]
)

# ================= DASHBOARD =================
with tab1:
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Média", f"{df_filtrado['Valor'].mean():,.2f}")
    col2.metric("📊 Registros", len(df_filtrado))
    col3.metric("🏢 Unidades", df_filtrado['Unidade'].nunique())

    fig = px.box(df_filtrado, y="Unidade", x="Valor", color="Tipo", orientation='h')
    fig.update_layout(height=1000)

    st.plotly_chart(fig, width='stretch')

# ================= RANKING =================
with tab2:
    col1, col2 = st.columns(2)

    for tipo, col in zip(['Energia','Água'], [col1, col2]):
        with col:
            df_tipo = df_filtrado[df_filtrado['Tipo'] == tipo]
            ranking = df_tipo.groupby('Unidade')['Valor'].mean().reset_index()
            ranking = ranking.sort_values(by='Valor', ascending=True)

            fig = px.bar(ranking, y='Unidade', x='Valor', orientation='h', title=tipo)
            fig.update_layout(height=800)

            st.plotly_chart(fig, width='stretch')

# ================= ALERTAS =================
with tab3:
    outlier_data = []
    alertas = []

    for unidade in df_filtrado['Unidade'].unique():
        for tipo in ['Energia','Água']:

            df_u = df_filtrado[
                (df_filtrado['Unidade'] == unidade) &
                (df_filtrado['Tipo'] == tipo)
            ]

            if len(df_u) == 0:
                continue

            valores = df_u['Valor'].values

            q1 = np.percentile(valores, 25)
            q3 = np.percentile(valores, 75)
            iqr = q3 - q1
            lim_inf = q1 - 1.5 * iqr
            lim_sup = q3 + 1.5 * iqr

            outliers_df = df_u[
                (df_u['Valor'] < lim_inf) | (df_u['Valor'] > lim_sup)
            ]

            qtd = len(outliers_df)

            outlier_data.append([unidade, tipo, qtd])

            if qtd > 0:
                meses_outliers = list(outliers_df['Mes_nome'])
                valores_outliers = list(outliers_df['Valor'])

                nivel = "critico" if qtd >= LIMITE_OUTLIERS else "normal"

                alertas.append({
                    "nivel": nivel,
                    "unidade": unidade,
                    "tipo": tipo,
                    "quantidade": qtd,
                    "meses": meses_outliers,
                    "valores": valores_outliers
                })

    df_out = pd.DataFrame(outlier_data, columns=['Unidade','Tipo','Outliers'])

    df_out['Nivel'] = df_out['Outliers'].apply(
        lambda x: 'Crítico' if x >= LIMITE_OUTLIERS else 'Normal'
    )

    fig = px.bar(
        df_out,
        y='Unidade',
        x='Outliers',
        color='Nivel',
        orientation='h',
        barmode='group',
        color_discrete_map={'Crítico':'red','Normal':'orange'}
    )

    fig.update_layout(height=1000)
    st.plotly_chart(fig, width='stretch')

    st.subheader("📅 Meses com Outliers")

    for alerta in alertas:
        texto_meses = ", ".join(
            [f"{m} ({v:.2f})" for m, v in zip(alerta['meses'], alerta['valores'])]
        )

        if alerta["nivel"] == "critico":
            st.error(
                f"🔥 {alerta['unidade']} | {alerta['tipo']} → "
                f"{alerta['quantidade']} outliers\n\n"
                f"Meses: {texto_meses}"
            )
        else:
            st.warning(
                f"⚠️ {alerta['unidade']} | {alerta['tipo']} → "
                f"{alerta['quantidade']} outliers\n\n"
                f"Meses: {texto_meses}"
            )
