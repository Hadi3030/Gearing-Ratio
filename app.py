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

df = load_data(uploaded_file)

# ===============================
# VALIDASI KOLOM
# ===============================
for col in ["Periode", "Value"]:
    if col not in df.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan")
        st.stop()

# ===============================
# SIMPAN PERIODE ASLI
# ===============================
df["Periode_Raw"] = df["Periode"].astype(str)

# ===============================
# PARSING PERIODE STRING
# ===============================
bulan_map = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "mei": 5, "jun": 6, "jul": 7,
    "aug": 8, "agu": 8, "sep": 9,
    "oct": 10, "okt": 10,
    "nov": 11, "dec": 12
}

def parse_periode(val):
    try:
        dt = pd.to_datetime(val)
        return dt.year, dt.month
    except:
        pass

    text = str(val).lower()
    for b, m in bulan_map.items():
        if b in text:
            y = int(re.search(r"(20\d{2}|\d{2})", text).group())
            if y < 100:
                y += 2000
            return y, m
    return None, None

df[["Year", "Month"]] = df["Periode_Raw"].apply(
    lambda x: pd.Series(parse_periode(x))
)

df = df.dropna(subset=["Year", "Month"])
df["SortKey"] = df["Year"] * 100 + df["Month"]

# ===============================
# LABEL PERIODE
# ===============================
bulan_id = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
}

df["Periode_Label"] = (
    df["Month"].map(bulan_id) + " " + df["Year"].astype(int).astype(str)
)

# ===============================
# CLEAN VALUE (ANTI SALAH FORMAT)
# ===============================
def parse_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)

    text = str(val).strip()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text:
        text = text.replace(".", "")

    return float(text)

df["Value"] = df["Value"].apply(parse_value)

# ===============================
# SIDEBAR FILTER (UMUM)
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

# ===============================
# PREVIEW DATA (MENTAH)
# ===============================
st.subheader("👀 Preview Data (Raw)")
st.dataframe(
    df_f.style.format({"Value": "Rp {:,.2f}"}),
    use_container_width=True
)

# ===============================
# AREA CHART – OS PENJAMINAN KUR
# ===============================
st.subheader("📈 OS Penjaminan KUR")

df_kur = df[
    df["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])
]

agg_chart = (
    df_kur
    .groupby(["SortKey", "Periode_Label"], as_index=False)["Value"]
    .sum()
    .sort_values("SortKey")
)

agg_chart["Value_T"] = agg_chart["Value"] / 1_000_000_000_000

fig = px.area(
    agg_chart,
    x="Periode_Label",
    y="Value_T",
    markers=True
)

fig.update_layout(
    xaxis_title="Periode",
    yaxis_title="Outstanding (Triliun)",
    yaxis=dict(ticksuffix=" T"),
    hovermode="x unified"
)

fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=agg_chart["Periode_Label"],
    tickangle=-45
)

st.plotly_chart(fig, use_container_width=True)

# ===============================
# TABLE HASIL OLAHAN (KUR ONLY)
# ===============================
st.subheader("📋 Tabel Hasil Olahan – OS Penjaminan KUR")

pivot = (
    df_kur
    .pivot_table(
        index=["SortKey", "Periode_Label"],
        columns="Jenis",
        values="Value",
        aggfunc="sum"
    )
    .reset_index()
    .sort_values("SortKey")
)

pivot["Total OS KUR"] = (
    pivot.get("KUR Gen 1", 0).fillna(0) +
    pivot.get("KUR Gen 2", 0).fillna(0)
)

st.dataframe(
    pivot.style.format("Rp {:,.2f}"),
    use_container_width=True
)

# ===============================
# DOWNLOAD
# ===============================
st.download_button(
    "⬇️ Download Tabel OS KUR",
    pivot.to_csv(index=False).encode("utf-8"),
    "os_penjaminan_kur.csv",
    "text/csv"
)
