from typing import Any, Union
import duckdb
import polars as pl


def format_rupiah(nilai: Union[int, float]) -> str:
    """Memformat nilai numerik menjadi representasi mata uang Rupiah Indonesia (Rp).

    Args:
        nilai: Angka numerik (integer atau float).

    Returns:
        str: String terformat seperti 'Rp 1.500.000'.
    """
    if nilai is None:
        return "Rp 0"
    return f"Rp {nilai:,.0f}".replace(",", ".")


def format_angka_ringkas(angka: Union[int, float]) -> str:
    """Memformat angka besar menjadi notasi ringkas (K, M, B).

    Args:
        angka: Nilai numerik.

    Returns:
        str: Notasi ringkas misal 1.2M, 500K.
    """
    if angka is None:
        return "0"
    abs_angka = abs(angka)
    if abs_angka >= 1_000_000_000:
        return f"{angka / 1_000_000_000:.2f} B"
    elif abs_angka >= 1_000_000:
        return f"{angka / 1_000_000:.2f} M"
    elif abs_angka >= 1_000:
        return f"{angka / 1_000:.1f} K"
    else:
        return f"{angka:.2f}"


def load_parquet_aman(filepath_glob: str) -> pl.DataFrame:
    """Membaca file Parquet menggunakan Polars scan lazy evaluation yang aman.

    Args:
        filepath_glob: Pola path file (misal 'data/*.parquet').

    Returns:
        pl.DataFrame: Hasil evaluasi DataFrame.
    """
    return pl.scan_parquet(filepath_glob).collect()

