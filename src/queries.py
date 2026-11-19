from typing import List, Optional
import duckdb
import polars as pl


def _execute_to_polars(con: duckdb.DuckDBPyConnection, sql: str) -> pl.DataFrame:
    """Helper konversi kueri SQL DuckDB ke Polars DataFrame yang kompatibel lintas versi DuckDB."""
    try:
        return con.sql(sql).pl()
    except (AttributeError, Exception):
        return pl.from_arrow(con.execute(sql).arrow())


def query_ringkasan_wilayah(con: duckdb.DuckDBPyConnection, table_name: str = "transaksi") -> pl.DataFrame:
    """Melakukan agregasi metrik data berdasarkan wilayah menggunakan DuckDB in-process.

    Args:
        con: Koneksi database DuckDB aktif.
        table_name: Nama tabel atau path file Parquet.

    Returns:
        pl.DataFrame: DataFrame Polars berisi ringkasan agregasi per wilayah.
    """
    sql = f"""
        SELECT
            wilayah,
            COUNT(*) AS total_transaksi,
            ROUND(AVG(nilai_metrik), 2) AS rata_rata_metrik,
            ROUND(MIN(nilai_metrik), 2) AS nilai_minimum,
            ROUND(MAX(nilai_metrik), 2) AS nilai_maksimum,
            ROUND(SUM(nilai_metrik), 2) AS total_metrik
        FROM {table_name}
        GROUP BY wilayah
        ORDER BY total_transaksi DESC;
    """
    return _execute_to_polars(con, sql)


def query_agregasi_temporal(
    con: duckdb.DuckDBPyConnection,
    table_name: str = "transaksi",
    time_col: str = "tanggal",
    interval: str = "1 DAY"
) -> pl.DataFrame:
    """Melakukan windowing agregasi waktu menggunakan DuckDB.

    Args:
        con: Koneksi DuckDB aktif.
        table_name: Nama tabel atau file Parquet.
        time_col: Nama kolom bertipe tanggal/waktu.
        interval: Interval truncating waktu (misal '1 DAY', '1 MONTH').

    Returns:
        pl.DataFrame: Deret waktu hasil agregasi.
    """
    sql = f"""
        SELECT
            date_trunc('{interval.split()[-1].lower()}', {time_col}) AS periode_waktu,
            COUNT(*) AS volume,
            ROUND(AVG(nilai_metrik), 2) AS rata_nilai,
            ROUND(SUM(nilai_metrik), 2) AS total_nilai
        FROM {table_name}
        GROUP BY 1
        ORDER BY 1 ASC;
    """
    return _execute_to_polars(con, sql)


def query_distribusi_kategori(con: duckdb.DuckDBPyConnection, table_name: str = "transaksi") -> pl.DataFrame:
    """Menghitung sebaran frekuensi dan kontribusi persentase per kategori data."""
    sql = f"""
        WITH hitung_total AS (
            SELECT COUNT(*) AS grand_total FROM {table_name}
        )
        SELECT
            t.kategori,
            COUNT(*) AS jumlah_item,
            ROUND(COUNT(*) * 100.0 / h.grand_total, 2) AS persentase_kontribusi,
            ROUND(AVG(t.nilai_metrik), 2) AS rata_rata
        FROM {table_name} t, hitung_total h
        GROUP BY t.kategori, h.grand_total
        ORDER BY jumlah_item DESC;
    """
    return _execute_to_polars(con, sql)


def query_top_n(
    con: duckdb.DuckDBPyConnection,
    table_name: str = "transaksi",
    group_col: str = "wilayah",
    metric_col: str = "nilai_metrik",
    n: int = 10
) -> pl.DataFrame:
    """Mengambil Top-N grup berdasarkan jumlah agregat tertentu."""
    sql = f"""
        SELECT
            {group_col},
            COUNT(*) AS total_frekuensi,
            ROUND(SUM({metric_col}), 2) AS akumulasi_metrik
        FROM {table_name}
        GROUP BY {group_col}
        ORDER BY akumulasi_metrik DESC
        LIMIT {n};
    """
    return _execute_to_polars(con, sql)



def hitung_moving_average_polars(
    df: pl.DataFrame,
    col_name: str = "rata_nilai",
    window_size: int = 7
) -> pl.DataFrame:
    """Menghitung rata-rata bergerak (moving average) menggunakan Polars Expressions.

    Args:
        df: DataFrame input dengan kolom terurut.
        col_name: Nama kolom numerik target.
        window_size: Ukuran jendela geser (misal 7 hari).

    Returns:
        pl.DataFrame: DataFrame dengan kolom baru berisi nilai moving average.
    """
    return df.with_columns(
        pl.col(col_name)
        .rolling_mean(window_size=window_size)
        .round(2)
        .alias(f"ma_{window_size}d")
    )


def deteksi_anomali_iqr_polars(
    df: pl.DataFrame,
    col_name: str = "nilai_metrik",
    multiplier: float = 1.5
) -> pl.DataFrame:
    """Mendeteksi data pencilan (outlier) menggunakan metode Interquartile Range (IQR) di Polars.

    Args:
        df: DataFrame input.
        col_name: Nama kolom numerik.
        multiplier: Faktor pengali IQR (default 1.5).

    Returns:
        pl.DataFrame: DataFrame dengan kolom boolean 'is_outlier'.
    """
    q1 = df[col_name].quantile(0.25)
    q3 = df[col_name].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)

    return df.with_columns(
        ((pl.col(col_name) < lower_bound) | (pl.col(col_name) > upper_bound)).alias("is_outlier")
    )
