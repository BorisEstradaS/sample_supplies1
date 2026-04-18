import streamlit as st
from pymongo import MongoClient
import pandas as pd

# -------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------
st.set_page_config(
    page_title="MongoDB Sample Supplies Dashboard",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Dashboard - Sample Supplies (MongoDB Atlas)")

# -------------------------------------------------
# CONEXIÓN A MONGODB
# -------------------------------------------------
@st.cache_resource
def init_connection():
    if "mongo" not in st.secrets:
        st.error("❌ Secrets de MongoDB no configurados")
        st.stop()

    mongo_uri = st.secrets["mongo"]["uri"]
    client = MongoClient(mongo_uri)
    return client


client = init_connection()

db = client["sample_supplies"]
collection = db["sales"]

# -------------------------------------------------
# CARGA DE DATOS
# -------------------------------------------------
@st.cache_data
def load_data():

    data = list(collection.find({}, {"_id": 0}).limit(500))

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    return df


df = load_data()

# -------------------------------------------------
# VALIDACIONES (ANTI-CRASH)
# -------------------------------------------------
if df.empty:
    st.error("❌ No se cargaron datos desde MongoDB")
    st.stop()

required_columns = ["storeLocation", "purchaseMethod"]

missing_cols = [c for c in required_columns if c not in df.columns]

if missing_cols:
    st.error(f"❌ Columnas faltantes: {missing_cols}")
    st.write("Columnas disponibles:", df.columns)
    st.stop()

# -------------------------------------------------
# SIDEBAR FILTROS
# -------------------------------------------------
st.sidebar.header("🔎 Filtros")

stores = df["storeLocation"].dropna().unique()

selected_store = st.sidebar.selectbox(
    "Seleccionar tienda",
    sorted(stores)
)

filtered_df = df[df["storeLocation"] == selected_store]

# -------------------------------------------------
# KPIs
# -------------------------------------------------
col1, col2, col3 = st.columns(3)

total_sales = len(filtered_df)
total_items = filtered_df["items"].apply(len).sum()
avg_items = filtered_df["items"].apply(len).mean()

col1.metric("🧾 Total Ventas", total_sales)
col2.metric("📦 Items Vendidos", int(total_items))
col3.metric("📊 Promedio Items/Venta", round(avg_items, 2))

st.divider()

# -------------------------------------------------
# TABLA DE DATOS
# -------------------------------------------------
st.subheader("📋 Ventas Registradas")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# -------------------------------------------------
# GRÁFICO
# -------------------------------------------------
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

# -------------------------------------------------
# DEBUG OPCIONAL (puedes borrar luego)
# -------------------------------------------------
with st.expander("🔧 Debug Dataset"):
    st.write("Columnas detectadas:")
    st.write(df.columns)

    st.write("Documento ejemplo:")
    st.write(collection.find_one())

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.success("✅ Conectado correctamente a MongoDB Atlas - sample_supplies.sales")
