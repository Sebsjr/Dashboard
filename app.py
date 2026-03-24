import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# 🎨 Tema escuro
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

# ---------------- FUNÇÃO OUTLIER ----------------
def calcular_outliers(dados):
    q1 = np.percentile(dados, 25)
    q3 = np.percentile(dados, 75)
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    return [x for x in dados if x < lim_inf or x > lim_sup]

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

            dados_u = df_filtrado[
                (df_filtrado['Unidade'] == unidade) &
                (df_filtrado['Tipo'] == tipo)
            ]['Valor']

            if len(dados_u) == 0:
                continue

            out = calcular_outliers(dados_u)
            qtd = len(out)

            outlier_data.append([unidade, tipo, qtd])

            if qtd > 0:
                if qtd >= LIMITE_OUTLIERS:
                    alertas.append(("critico", unidade, tipo, qtd))
                else:
                    alertas.append(("normal", unidade, tipo, qtd))

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

    for nivel, u, t, q in alertas:
        if nivel == "critico":
            st.error(f"🔥 {u} | {t}: {q} outliers")
        else:
            st.warning(f"⚠️ {u} | {t}: {q} outliers")

# ================= DIAGNÓSTICO =================
with tab4:
    st.subheader("🤖 Diagnóstico Inteligente")

    for nivel, u, t, q in alertas:
        if q == 0:
            continue

        if t == "Água":
            causa = "Possível vazamento ou erro de medição"
        else:
            causa = "Possível problema elétrico ou equipamento"

        if nivel == "critico":
            st.error(f"{u} | {t} → {causa}")
        else:
            st.warning(f"{u} | {t} → {causa}")

# ================= PREVISÃO =================
with tab5:
    st.subheader("📈 Previsão de Consumo (Machine Learning)")

    unidade_sel = st.selectbox("Unidade", df_filtrado['Unidade'].unique())
    tipo_sel = st.selectbox("Tipo", ['Energia','Água'])

    dados_ml = df_filtrado[
        (df_filtrado['Unidade'] == unidade_sel) &
        (df_filtrado['Tipo'] == tipo_sel)
    ]

    if len(dados_ml) < 3:
        st.warning("Poucos dados para previsão")
    else:
        X = dados_ml['Mes'].values.reshape(-1,1)
        y = dados_ml['Valor'].values

        modelo = LinearRegression()
        modelo.fit(X, y)

        futuros = np.arange(
            dados_ml['Mes'].max()+1,
            dados_ml['Mes'].max()+7
        ).reshape(-1,1)

        previsao = modelo.predict(futuros)

        df_prev = pd.DataFrame({
            'Mes': list(dados_ml['Mes']) + list(futuros.flatten()),
            'Valor': list(y) + list(previsao),
            'Tipo': ['Real']*len(y) + ['Previsto']*len(previsao)
        })

        fig = px.line(
            df_prev,
            x='Mes',
            y='Valor',
            color='Tipo',
            markers=True,
            title=f"{unidade_sel} - {tipo_sel}"
        )

        st.plotly_chart(fig, width='stretch')

        st.info(f"Tendência: {'Alta 📈' if modelo.coef_[0] > 0 else 'Queda 📉'}")

# ================= EXPORT =================
st.sidebar.subheader("📥 Exportar")

if st.sidebar.button("Exportar Excel"):
    df_filtrado.to_excel("dados_filtrados.xlsx", index=False)
    st.sidebar.success("Arquivo exportado!")
