import streamlit as st
from pymongo import MongoClient
import pandas as pd
import json

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="MongoDB Sample Supplies",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Dashboard - Sample Supplies")

# -------------------------------------------------
# CONEXIÓN
# -------------------------------------------------
@st.cache_resource
def init_connection():
    mongo_uri = st.secrets["mongo"]["uri"]
    return MongoClient(mongo_uri)

client = init_connection()

db = client["sample_supplies"]
collection = db["sales"]

# -------------------------------------------------
# LIMPIEZA DATAFRAME (FIX ARROW)
# -------------------------------------------------
def clean_dataframe(df):

    for col in df.columns:

        # convertir listas o dicts a string JSON
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(
                lambda x: json.dumps(x, default=str)
            )

    return df


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data
def load_data():

    data = list(collection.find({}, {"_id": 0}).limit(500))

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df = clean_dataframe(df)

    return df


df = load_data()

if df.empty:
    st.error("No hay datos")
    st.stop()

# -------------------------------------------------
# VALIDACIÓN
# -------------------------------------------------
required_columns = ["storeLocation", "purchaseMethod"]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(f"Columnas faltantes: {missing}")
    st.write(df.columns)
    st.stop()

# -------------------------------------------------
# FILTROS
# -------------------------------------------------
st.sidebar.header("🔎 Filtros")

stores = df["storeLocation"].dropna().unique()

selected_store = st.sidebar.selectbox(
    "Tienda",
    sorted(stores)
)

filtered_df = df[df["storeLocation"] == selected_store]

# -------------------------------------------------
# KPIs
# -------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Ventas", len(filtered_df))

col2.metric(
    "Métodos de compra",
    filtered_df["purchaseMethod"].nunique()
)

col3.metric(
    "Registros totales",
    len(df)
)

st.divider()

# -------------------------------------------------
# DATAFRAME (YA NO FALLA)
# -------------------------------------------------
st.subheader("📋 Ventas")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# -------------------------------------------------
# GRÁFICO
# -------------------------------------------------
st.subheader("📈 Método de Compra")

chart = (
    filtered_df["purchaseMethod"]
    .value_counts()
)

st.bar_chart(chart)

# -------------------------------------------------
# DEBUG
# -------------------------------------------------
with st.expander("Debug"):
    st.write(df.dtypes)
