import streamlit as st
from pymongo import MongoClient
import pandas as pd

# -----------------------------
# CONFIGURACIÓN APP
# -----------------------------
st.set_page_config(
    page_title="MongoDB Sample Supplies",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Dashboard - Sample Supplies (MongoDB Atlas)")

# -----------------------------
# CONEXIÓN MONGODB
# -----------------------------
@st.cache_resource
def init_connection():
    mongo_uri = st.secrets["mongo"]["uri"]
    client = MongoClient(mongo_uri)
    return client

client = init_connection()

# Base de datos sample
db = client["sample_supplies"]
collection = db["sales"]

# -----------------------------
# CARGAR DATOS
# -----------------------------
@st.cache_data
def load_data():
    data = list(collection.find().limit(500))
    df = pd.DataFrame(data)

    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    return df

df = load_data()

# -----------------------------
# SIDEBAR FILTROS
# -----------------------------
st.sidebar.header("🔎 Filtros")

stores = df["storeLocation"].dropna().unique()

selected_store = st.sidebar.selectbox(
    "Seleccionar tienda",
    options=stores
)

filtered_df = df[df["storeLocation"] == selected_store]

# -----------------------------
# KPIs
# -----------------------------
col1, col2, col3 = st.columns(3)

total_sales = filtered_df["saleDate"].count()
total_items = filtered_df["items"].apply(len).sum()

avg_items = filtered_df["items"].apply(len).mean()

col1.metric("🧾 Ventas", total_sales)
col2.metric("📦 Items vendidos", total_items)
col3.metric("📊 Promedio Items/Venta", round(avg_items,2))

st.divider()

# -----------------------------
# TABLA
# -----------------------------
st.subheader("📋 Ventas Registradas")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# GRÁFICO
# -----------------------------
st.subheader("📈 Ventas por Método de Compra")

purchase_counts = (
    filtered_df["purchaseMethod"]
    .value_counts()
    .reset_index()
)

purchase_counts.columns = ["Metodo", "Cantidad"]

st.bar_chart(
    purchase_counts.set_index("Metodo")
)

# -----------------------------
# FOOTER
# -----------------------------
st.success("✅ Conectado correctamente a MongoDB Atlas sample_supplies")
