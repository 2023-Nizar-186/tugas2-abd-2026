import duckdb
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Big Data Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Dashboard Analitik Big Data Indonesia")
st.markdown("Produk Data Interaktif — Tugas 2 Kuliah Analisis Big Data")

# --- Caching Data Pipeline dengan DuckDB ---
@st.cache_data
def load_and_aggregate_data():
    con = duckdb.connect()

    # Query contoh menggunakan DuckDB in-memory / Parquet reader
    # Mahasiswa mengganti path ini dengan dataset tim masing-masing
    sql_query = """
        SELECT
            'Wilayah ' || (range % 5 + 1) AS wilayah,
            range AS id,
            DATE '2026-01-01' + INTERVAL (range % 365) DAYS AS tanggal,
            ROUND(20.0 + (range % 15) * 1.1 + (range % 3), 2) AS nilai_metrik,
            CASE WHEN range % 7 = 0 THEN 'Kategori A'
                 WHEN range % 7 IN (1, 2) THEN 'Kategori B'
                 ELSE 'Kategori C' END AS kategori
        FROM range(50000);
    """
    try:
        df_hasil = con.sql(sql_query).pl()
    except (AttributeError, Exception):
        df_hasil = pl.from_arrow(con.execute(sql_query).arrow())
    return df_hasil

df = load_and_aggregate_data()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filter Analisis")

daftar_wilayah = sorted(df["wilayah"].unique().to_list())
wilayah_terpilih = st.sidebar.multiselect(
    "Pilih Wilayah:",
    options=daftar_wilayah,
    default=daftar_wilayah[:3]
)

daftar_kategori = sorted(df["kategori"].unique().to_list())
kategori_terpilih = st.sidebar.multiselect(
    "Pilih Kategori:",
    options=daftar_kategori,
    default=daftar_kategori
)

# Filter Dataframe menggunakan Polars
df_terfilter = df.filter(
    (pl.col("wilayah").is_in(wilayah_terpilih)) &
    (pl.col("kategori").is_in(kategori_terpilih))
)

# --- KPI Metric Cards ---
col1, col2, col3, col4 = st.columns(4)

total_baris = df_terfilter.shape[0]
rata_metrik = df_terfilter["nilai_metrik"].mean() if total_baris > 0 else 0.0
maks_metrik = df_terfilter["nilai_metrik"].max() if total_baris > 0 else 0.0
jumlah_wilayah = len(wilayah_terpilih)

col1.metric("Total Data Terfilter", f"{total_baris:,}")
col2.metric("Rata-rata Metrik", f"{rata_metrik:.2f}")
col3.metric("Nilai Maksimum", f"{maks_metrik:.2f}")
col4.metric("Wilayah Aktif", f"{jumlah_wilayah}")

# --- Tab Layout ---
tab1, tab2, tab3 = st.tabs(["📈 Analisis Temporal", "📊 Distribusi & Komposisi", "📋 Tabel Data"])

with tab1:
    st.subheader("Tren Waktu dan Rata-rata Bergerak")
    if total_baris > 0:
        # Agregasi Polars per tanggal
        df_tren = (
            df_terfilter
            .group_by("tanggal")
            .agg(
                [
                    pl.col("nilai_metrik").mean().round(2).alias("rata_nilai"),
                    pl.len().alias("volume")
                ]
            )
            .sort("tanggal")
            .with_columns(
                pl.col("rata_nilai").rolling_mean(window_size=7).round(2).alias("ma_7d")
            )
            .to_pandas()
        )

        fig_tren = go.Figure()
        fig_tren.add_trace(
            go.Scatter(
                x=df_tren["tanggal"],
                y=df_tren["rata_nilai"],
                mode="lines",
                name="Nilai Harian",
                line=dict(color="#93c5fd", width=1)
            )
        )
        fig_tren.add_trace(
            go.Scatter(
                x=df_tren["tanggal"],
                y=df_tren["ma_7d"],
                mode="lines",
                name="Tren 7 Hari (MA)",
                line=dict(color="#1d4ed8", width=2.5)
            )
        )
        fig_tren.update_layout(
            template="plotly_white",
            hovermode="x unified",
            xaxis=dict(rangeslider=dict(visible=True))
        )
        st.plotly_chart(fig_tren, use_container_width=True)
    else:
        st.warning("Tidak ada data yang cocok dengan kombinasi filter terpilih.")

with tab2:
    st.subheader("Distribusi Nilai Berdasarkan Kategori")
    if total_baris > 0:
        fig_box = px.box(
            df_terfilter.to_pandas(),
            x="kategori",
            y="nilai_metrik",
            color="wilayah",
            template="plotly_white"
        )
        st.plotly_chart(fig_box, use_container_width=True)

with tab3:
    st.subheader("Cuplikan Data Terstruktur")
    st.dataframe(df_terfilter.head(100).to_pandas(), use_container_width=True)
