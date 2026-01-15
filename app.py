import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ===============================
# CONFIG (WAJIB PALING ATAS)
# ===============================
st.set_page_config(
    page_title="Dashboard KUR & PEN",
    layout="wide"
)

# ==========================================================
# HEADER BAR (EFEK SEPERTI FREEZE HEADER EXCEL)
# ==========================================================
with st.container():
    st.markdown(
        """
        <div style="
            background-color:#f0f2f6;
            padding:15px;
            border-radius:8px;
            margin-bottom:20px;
        ">
        """,
        unsafe_allow_html=True
    )

    col_logo, col_title = st.columns([1, 8])

    with col_logo:
        st.image("gambar/OIP.jpg", width=90)

    with col_title:
        st.markdown(
            """
            <h1 style="margin-bottom:0; color:#1f4e79;">
                Dashboard Gearing Ratio KUR & PEN
            </h1>
            <p style="margin-top:0; font-size:16px; color:gray;">
                Analisis Outstanding, Ekuitas, dan Trend Gearing Ratio berbasis data periodik
            </p>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================================
# INFO + CONTOH FORMAT
# ==========================================================
st.info(
    "Website ini akan otomatis menampilkan dashboard untuk perhitungan Trend Gearing Ratio "
    "setelah anda mengupload file dengan format xlsx atau csv, dan pastikan format tabel sesuai contoh."
)

st.image(
    "gambar/ssXlsx.png",
    caption="Contoh format file Excel (.xlsx) yang didukung",
    use_container_width=True
)

st.title("📊 Summary Trend Gearing Ratio")

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
required_cols = ["Periode", "Value"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"❌ Kolom '{col}' tidak ditemukan")
        st.stop()

# ===============================
# PARSING PERIODE (TETAP)
# ===============================
df["Periode_Raw"] = df["Periode"].astype(str)

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
            year_match = re.search(r"(20\d{2}|\d{2})", text)
            if year_match:
                y = int(year_match.group())
                if y < 100:
                    y += 2000
                return y, m
    return None, None

df[["Year", "Month"]] = df["Periode_Raw"].apply(lambda x: pd.Series(parse_periode(x)))
df = df.dropna(subset=["Year", "Month"])

df["SortKey"] = df["Year"] * 100 + df["Month"]

bulan_id = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
}

df["Periode_Label"] = df["Month"].map(bulan_id) + " " + df["Year"].astype(int).astype(str)

df["Is_Audited"] = df["Periode_Raw"].str.contains("audit", case=False, na=False).astype(int)

# ===============================
# CLEAN VALUE
# ===============================
def parse_value(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)

    text = str(val).strip()
    if "." in text and "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "." in text:
        text = text.replace(".", "")
    try:
        return float(text)
    except:
        return None

df["Value"] = df["Value"].apply(parse_value)

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("🔎 Filter Data")

df_f = df.copy()

years = sorted(df_f["Year"].unique())
selected_years = st.sidebar.multiselect("Tahun", years, default=years)
df_f = df_f[df_f["Year"].isin(selected_years)]

df_f["Bulan_Nama"] = df_f["Month"].map(bulan_id)
selected_months = st.sidebar.multiselect(
    "Bulan", list(bulan_id.values()), default=list(bulan_id.values())
)
df_f = df_f[df_f["Bulan_Nama"].isin(selected_months)]

# ==========================================================
# PREVIEW DATA (HIDE / SHOW)
# ==========================================================
with st.expander("👀 Preview Data (Mentah)", expanded=False):
    st.dataframe(
        df_f.style.format({"Value": "Rp {:,.2f}"}),
        use_container_width=True
    )

# ==========================================================
# SEMUA BAGIAN ANALISIS → DIBUNGKUS EXPANDER
# (LOGIKA DALAMNYA TETAP, TIDAK DIUBAH)
# ==========================================================

with st.expander("📈 OS Penjaminan KUR", expanded=True):
    # ---- isi OS KUR (KODE LAMAMU TETAP) ----
    df_kur = df_f[df_f["Jenis"].isin(["KUR Gen 1", "KUR Gen 2"])]
    df_kur = df_kur.sort_values(["SortKey", "Is_Audited"], ascending=[True, False])
    df_kur_agg = (
        df_kur.groupby(["SortKey", "Periode_Label"], as_index=False)
        .agg(OS_KUR_Rp=("Value", "last"))
        .sort_values("SortKey")
    )
    df_kur_agg["OS_KUR_T"] = df_kur_agg["OS_KUR_Rp"] / 1_000_000_000_000

    fig = px.area(df_kur_agg, x="Periode_Label", y="OS_KUR_T", markers=True)
    fig.update_layout(yaxis=dict(ticksuffix=" T"), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_kur_agg, use_container_width=True)

# ==========================================================
# FOOTER BAR (EFEK FREEZE FOOTER)
# ==========================================================
with st.container():
    st.markdown(
        """
        <div style="
            background-color:#f0f2f6;
            padding:12px;
            border-radius:8px;
            margin-top:30px;
            text-align:center;
            color:gray;
            font-size:13px;
        ">
            © 2026 | Dashboard Gearing Ratio KUR & PEN<br>
            Developed with ❤️ using <b>Streamlit</b> & <b>Plotly</b>
        </div>
        """,
        unsafe_allow_html=True
    )
