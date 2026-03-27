import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Dashboard Excel",
    layout="wide"
)

st.title("📊 Dashboard - Leitura de Excel (GitHub)")

# ---------------- FUNÇÃO COM CACHE ----------------
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Sebsjr/Dashboard/main/dados.xls"

    try:
        df = pd.read_excel(
            url,
            sheet_name='Planilha2',
            header=[0, 1],
            engine='xlrd'  # necessário para .xls
        )
        return df

    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

# ---------------- CARREGAMENTO ----------------
df = carregar_dados()

# ---------------- EXIBIÇÃO ----------------
if df is not None:

    st.success("✅ Arquivo carregado com sucesso!")

    # Mostrar colunas
    st.subheader("📌 Colunas do dataset")
    st.write(df.columns)

    # Mostrar dados
    st.subheader("📊 Pré-visualização dos dados")
    st.dataframe(df)

else:
    st.warning("⚠️ Não foi possível carregar os dados.")

# ---------------- DEBUG (opcional) ----------------
with st.expander("🔍 Debug"):
    st.write("Teste de leitura sem parâmetros:")

    try:
        url = "https://raw.githubusercontent.com/Sebsjr/Dashboard/main/dados.xls"
        df_teste = pd.read_excel(url)
        st.write("Abas disponíveis:", df_teste.keys())
    except Exception as e:
        st.error(e)
