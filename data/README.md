# Panduan Dataset — Tugas 2 (Data Product)

Folder ini digunakan untuk menempatkan dataset yang dipakai dalam dashboard analitik.

> **PENTING:** Jangan pernah melakukan `git commit` atau `git push` file dataset besar (>100MB) langsung ke repository GitHub! File data besar harus diabaikan melalui `.gitignore`.

---

## Informasi Dataset Kelompok

- **Nama Dataset:** [Isi nama dataset]
- **Sumber Data:** [Tautan sumber resmi / URL portal]
- **Ukuran File Mentah:** [Ukuran dalam MB / GB]
- **Jumlah Baris:** [Jumlah baris data, minimal >500 MB atau >1 Juta Baris]
- **Format File:** [CSV / Parquet]

---

## Instruksi Pengunduhan & Penyiapan Data

Tuliskan perintah atau script untuk mengunduh dataset secara otomatis:

```bash
# Contoh pengunduhan menggunakan curl / wget:
# curl -L -o data/dataset_mentah.parquet https://url-sumber-data.com/data.parquet
```

---

## Skema Struktur Kolom Data

| Nama Kolom | Tipe Data | Deskripsi Makna Bisnis |
|------------|:---------:|------------------------|
| `timestamp` | Datetime | Waktu pencatatan observasi |
| `wilayah` | Utf8 | Nama provinsi / kota / stasiun |
| `kategori` | Utf8 | Pengelompokan jenis data |
| `nilai_metrik` | Float64 | Angka pengukuran utama |
