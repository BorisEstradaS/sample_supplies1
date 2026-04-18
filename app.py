import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import json

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------
st.set_page_config(
    page_title="Supply Sales Dashboard",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Supply Sales Dashboard")
st.caption("MongoDB Atlas + Streamlit Analytics App")

# --------------------------------------------------
# CONEXIÓN MONGODB
# --------------------------------------------------
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["mongo"]["uri"])

client = init_connection()
collection = client["sample_supplies"]["sales"]

# --------------------------------------------------
# LIMPIEZA DATAFRAME
# --------------------------------------------------
def clean_dataframe(df):

    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, default=str))

    return df


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data
def load_data():

    data = list(collection.find({}, {"_id": 0}).limit(1000))

    df = pd.DataFrame(data)

    df = clean_dataframe(df)

    df["saleDate"] = pd.to_datetime(df["saleDate"])

    return df


df = load_data()

# --------------------------------------------------
# SIDEBAR FILTROS
# --------------------------------------------------
st.sidebar.header("🔎 Filtros")

store = st.sidebar.multiselect(
    "Tienda",
    df["storeLocation"].unique(),
    default=df["storeLocation"].unique()
)

date_range = st.sidebar.date_input(
    "Rango de fechas",
    [df["saleDate"].min(), df["saleDate"].max()]
)

filtered_df = df[
    (df["storeLocation"].isin(store)) &
    (df["saleDate"].dt.date >= date_range[0]) &
    (df["saleDate"].dt.date <= date_range[1])
]

# --------------------------------------------------
# KPIs
# --------------------------------------------------
st.subheader("📊 KPIs Ejecutivos")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Ventas Totales", len(filtered_df))
c2.metric("Tiendas Activas", filtered_df["storeLocation"].nunique())
c3.metric("Métodos Compra", filtered_df["purchaseMethod"].nunique())
c4.metric("Registros Dataset", len(df))

st.divider()

# --------------------------------------------------
# GRÁFICOS
# --------------------------------------------------

col1, col2 = st.columns(2)

# Ventas por tienda
sales_store = (
    filtered_df["storeLocation"]
    .value_counts()
    .reset_index()
)

sales_store.columns = ["Tienda", "Ventas"]

fig_store = px.bar(
    sales_store,
    x="Tienda",
    y="Ventas",
    title="Ventas por Tienda"
)

col1.plotly_chart(fig_store, use_container_width=True)

# Métodos de compra
purchase_method = (
    filtered_df["purchaseMethod"]
    .value_counts()
    .reset_index()
)

purchase_method.columns = ["Metodo", "Cantidad"]

fig_method = px.pie(
    purchase_method,
    names="Metodo",
    values="Cantidad",
    title="Método de Compra"
)

col2.plotly_chart(fig_method, use_container_width=True)

# --------------------------------------------------
# TENDENCIA TEMPORAL
# --------------------------------------------------
st.subheader("📈 Tendencia de Ventas")

trend = (
    filtered_df
    .groupby(filtered_df["saleDate"].dt.date)
    .size()
    .reset_index(name="Ventas")
)

fig_trend = px.line(
    trend,
    x="saleDate",
    y="Ventas",
    markers=True,
    title="Ventas en el Tiempo"
)

st.plotly_chart(fig_trend, use_container_width=True)

# --------------------------------------------------
# TABLA FINAL
# --------------------------------------------------
st.subheader("📋 Detalle de Ventas")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

st.success("✅ Dashboard conectado correctamente a MongoDB Atlas")
