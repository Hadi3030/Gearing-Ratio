import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Dashboard Ekuitas KUR & PEN",
    layout="wide"
)

st.title("📊 Summary Outstanding Penjaminan KUR dan PEN")

# ===============================
# UPLOAD FILE
# ===============================
uploaded_file = st.file_uploader(
    "Upload file Excel / CSV",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("📥 Silakan upload file terlebih dahulu")
    st.stop()

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

df = load_data(uploaded_file)

# ===============================
# PREVIEW
# ===============================
st.subheader("👀 Preview Data")
st.dataframe(df.head(), use_container_width=True)

# ===============================
# VALIDASI KOLOM
# ===============================
required_cols = ["Periode", "Jenis", "Generasi", "Value", "Jumlah Debitur"]
missing = [c for c in required_cols if c not in df.columns]

if missing:
    st.error(f"❌ Kolom tidak ditemukan: {missing}")
    st.stop()

# ===============================
# CLEANING
# ===============================
df["Periode"] = pd.to_datetime(df["Periode"], errors="coerce")

df["Value"] = (
    df["Value"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace(".", "", regex=False)
)
df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
df["Jumlah Debitur"] = pd.to_numeric(df["Jumlah Debitur"], errors="coerce")

df = df.dropna()

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter")

jenis_filter = st.sidebar.multiselect(
    "Jenis",
    df["Jenis"].unique(),
    default=df["Jenis"].unique()
)

gen_filter = st.sidebar.multiselect(
    "Generasi",
    df["Generasi"].unique(),
    default=df["Generasi"].unique()
)

periode_range = st.sidebar.date_input(
    "Periode",
    [df["Periode"].min().date(), df["Periode"].max().date()]
)

# ===============================
# FILTER DATA
# ===============================
df_f = df[
    (df["Jenis"].isin(jenis_filter)) &
    (df["Generasi"].isin(gen_filter)) &
    (df["Periode"].dt.date >= periode_range[0]) &
    (df["Periode"].dt.date <= periode_range[1])
]

if df_f.empty:
    st.warning("⚠️ Data kosong setelah filter")
    st.stop()

# ===============================
# KPI
# ===============================
col1, col2, col3 = st.columns(3)

col1.metric("Total Outstanding", f"{df_f['Value'].sum():,.0f}")
col2.metric("Jumlah Debitur", f"{df_f['Jumlah Debitur'].sum():,.0f}")
col3.metric("Jumlah Data", len(df_f))

# ===============================
# BAR CHART – PORTFOLIO SUMMARY
# ===============================
st.subheader("📊 Portfolio Summary")

summary_df = (
    df_f.groupby("Jenis")[["Value"]]
    .sum()
    .reset_index()
)

fig_bar = px.bar(
    summary_df,
    x="Jenis",
    y="Value",
    text_auto=".2s",
    title="Portfolio Summary"
)

st.plotly_chart(fig_bar, use_container_width=True)

# ===============================
# BAR CHART – JUMLAH DEBITUR
# ===============================
st.subheader("👥 Jumlah Debitur")

debitur_df = (
    df_f.groupby("Jenis")[["Jumlah Debitur"]]
    .sum()
    .reset_index()
)

fig_deb = px.bar(
    debitur_df,
    x="Jenis",
    y="Jumlah Debitur",
    text_auto=True,
    title="Jumlah Debitur"
)

st.plotly_chart(fig_deb, use_container_width=True)

# ===============================
# LINE CHART – TREN
# ===============================
st.subheader("📈 Tren Outstanding")

fig_line = px.line(
    df_f,
    x="Periode",
    y="Value",
    color="Jenis",
    markers=True
)

st.plotly_chart(fig_line, use_container_width=True)

# ===============================
# TABLE
# ===============================
st.subheader("📋 Data Detail")
st.dataframe(df_f, use_container_width=True)

# ===============================
# DOWNLOAD
# ===============================
st.download_button(
    "⬇️ Download Data Filtered",
    df_f.to_csv(index=False).encode("utf-8"),
    "data_filtered.csv",
    "text/csv"
)
