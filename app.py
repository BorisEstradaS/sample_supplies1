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
st.caption("MongoDB Atlas + Streamlit Analytics")

# --------------------------------------------------
# CONEXIÓN MONGODB
# --------------------------------------------------
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["mongo"]["uri"])

client = init_connection()
collection = client["sample_supplies"]["sales"]

# --------------------------------------------------
# LIMPIAR DATAFRAME (FIX ARROW)
# --------------------------------------------------
def clean_dataframe(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, default=str))
    return df

# --------------------------------------------------
# TRANSFORMACIÓN ANALÍTICA
# --------------------------------------------------
def transform_sales(df):

    # ---------- CUSTOMER ----------
    df["gender"] = df["customer"].apply(
        lambda x: json.loads(x)["gender"] if pd.notna(x) else None
    )

    df["age"] = df["customer"].apply(
        lambda x: json.loads(x)["age"] if pd.notna(x) else None
    )

    df["satisfaction"] = df["customer"].apply(
        lambda x: json.loads(x)["satisfaction"] if pd.notna(x) else None
    )

    # ---------- ITEMS ----------
    def item_count(items):
        try:
            items = json.loads(items)
            return sum(i["quantity"] for i in items)
        except:
            return 0

    def total_amount(items):
        try:
            items = json.loads(items)
            return sum(i["price"] * i["quantity"] for i in items)
        except:
            return 0

    df["items_qty"] = df["items"].apply(item_count)
    df["total_sale"] = df["items"].apply(total_amount)

    return df

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data
def load_data():

    data = list(collection.find({}, {"_id": 0}).limit(1000))

    if len(data) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df = clean_dataframe(df)

    df["saleDate"] = pd.to_datetime(df["saleDate"])

    df = transform_sales(df)

    return df


df = load_data()

if df.empty:
    st.error("❌ No hay datos cargados")
    st.stop()

# --------------------------------------------------
# SIDEBAR FILTROS
# --------------------------------------------------
st.sidebar.header("🔎 Filtros")

stores = st.sidebar.multiselect(
    "Tienda",
    df["storeLocation"].unique(),
    default=df["storeLocation"].unique()
)

date_range = st.sidebar.date_input(
    "Rango de fechas",
    [df["saleDate"].min(), df["saleDate"].max()]
)

filtered_df = df[
    (df["storeLocation"].isin(stores)) &
    (df["saleDate"].dt.date >= date_range[0]) &
    (df["saleDate"].dt.date <= date_range[1])
]

# --------------------------------------------------
# KPIs COMERCIALES
# --------------------------------------------------
st.subheader("💰 KPIs Comerciales")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Ventas Totales", len(filtered_df))
k2.metric("Ingresos Totales", f"${filtered_df['total_sale'].sum():,.0f}")
k3.metric("Ticket Promedio", f"${filtered_df['total_sale'].mean():,.2f}")
k4.metric("Items Vendidos", int(filtered_df["items_qty"].sum()))

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

# Método de compra
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
    markers=True
)

st.plotly_chart(fig_trend, use_container_width=True)

# --------------------------------------------------
# TABLA PROFESIONAL
# --------------------------------------------------
st.subheader("📋 Detalle de Ventas")

display_df = filtered_df[
    [
        "saleDate",
        "storeLocation",
        "gender",
        "age",
        "purchaseMethod",
        "couponUsed",
        "items_qty",
        "total_sale",
        "satisfaction",
    ]
].copy()

display_df.columns = [
    "Fecha",
    "Tienda",
    "Cliente",
    "Edad",
    "Método Compra",
    "Cupón",
    "Items",
    "Total Venta ($)",
    "Satisfacción",
]

display_df["Total Venta ($)"] = display_df["Total Venta ($)"].round(2)

st.dataframe(
    display_df.sort_values("Fecha", ascending=False),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.success("✅ Dashboard conectado correctamente a MongoDB Atlas")
