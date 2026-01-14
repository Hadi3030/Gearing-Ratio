import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Dashboard KUR & PEN",
    layout="wide"
)

st.title("📊 Summary Outstanding Penjaminan KUR & PEN")

# ===============================
# UPLOAD FILE
# ===============================
uploaded_file = st.file_uploader(
    "📥 Upload file Excel / CSV",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("Silakan upload file terlebih dahulu")
    st.stop()

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(f"❌ Gagal membaca file: {e}")
    st.stop()

# ===============================
# BASIC CLEANING
# ===============================
if "Value" in df.columns:
    df["Value"] = (
        df["Value"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(".", "", regex=False)
    )
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

if "Jumlah Debitur" in df.columns:
    df["Jumlah Debitur"] = pd.to_numeric(df["Jumlah Debitur"], errors="coerce")

# ===============================
# PERIODE HANDLING (AMAN UNTUK STRING)
# ===============================
# simpan periode mentah
df["Periode_Raw"] = df["Periode"]

# coba parsing datetime TANPA merusak string
df["Periode_DT"] = pd.to_datetime(df["Periode_Raw"], errors="coerce")

bulan_map = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "mei": 5,
    "jun": 6, "jul": 7,
    "aug": 8, "agu": 8,
    "sep": 9,
    "oct": 10, "okt": 10,
    "nov": 11,
    "dec": 12, "des": 12
}

def extract_month_year(raw, dt):
    # kalau datetime valid → pakai datetime
    if pd.notna(dt):
        return dt.month, dt.year

    # fallback ke string
    if pd.isna(raw):
        return None, None

    text = str(raw).lower()

    # bulan
    month = None
    for k, v in bulan_map.items():
        if k in text:
            month = v
            break

    # tahun (2 / 4 digit)
    year = None
    m = re.search(r"(20\d{2}|\d{2})", text)
    if m:
        y = int(m.group())
        year = 2000 + y if y < 100 else y

    return month, year

df[["Month", "Year"]] = df.apply(
    lambda r: pd.Series(extract_month_year(r["Periode_Raw"], r["Periode_DT"])),
    axis=1
)

df["SortKey"] = df["Year"] * 100 + df["Month"]
df["Periode_Label"] = df["Periode_Raw"].astype(str)

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter Data")

df_f = df.copy()

if "Jenis" in df_f.columns:
    jenis_filter = st.sidebar.multiselect(
        "Jenis",
        sorted(df_f["Jenis"].dropna().unique()),
        default=sorted(df_f["Jenis"].dropna().unique())
    )
    df_f = df_f[df_f["Jenis"].isin(jenis_filter)]

if "Generasi" in df_f.columns:
    gen_filter = st.sidebar.multiselect(
        "Generasi",
        sorted(df_f["Generasi"].dropna().unique()),
        default=sorted(df_f["Generasi"].dropna().unique())
    )
    df_f = df_f[df_f["Generasi"].isin(gen_filter)]

# ===============================
# PREVIEW DATA
# ===============================
st.subheader("👀 Preview Data (Filtered)")
st.dataframe(
    df_f.style.format({"Value": "Rp {:,.0f}"}),
    use_container_width=True
)

# ===============================
# BAR CHART – JUMLAH DEBITUR
# ===============================
st.subheader("👥 Jumlah Debitur")

if {"Jenis", "Jumlah Debitur"}.issubset(df_f.columns):
    deb_df = df_f.groupby("Jenis", as_index=False)["Jumlah Debitur"].sum()

    fig = px.bar(
        deb_df,
        x="Jenis",
        y="Jumlah Debitur",
        text_auto=True
    )

    fig.update_xaxes(type="category")
    st.plotly_chart(fig, use_container_width=True)

# ===============================
# AREA CHART – OUTSTANDING PER PERIODE
# ===============================
st.subheader("📈 Outstanding per Periode")

if {"Periode_Label", "SortKey", "Value"}.issubset(df_f.columns):

    agg_df = (
        df_f
        .dropna(subset=["SortKey"])
        .groupby(["SortKey", "Periode_Label"], as_index=False)["Value"]
        .sum()
        .sort_values("SortKey")
    )

    agg_df["Value_T"] = agg_df["Value"] / 1_000_000_000_000_000

    fig = px.area(
        agg_df,
        x="Periode_Label",
        y="Value_T",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Periode",
        yaxis_title="Outstanding (T)",
        yaxis=dict(ticksuffix="T"),
        hovermode="x unified"
    )

    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=agg_df["Periode_Label"].tolist(),
        tickmode="array",
        tickvals=agg_df["Periode_Label"].tolist(),
        ticktext=agg_df["Periode_Label"].tolist(),
        tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABLE DETAIL
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
