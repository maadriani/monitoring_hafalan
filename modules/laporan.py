"""
modules/laporan.py
====================
FITUR: Laporan & Ekspor Data (Pure Dataset + Prediksi).
"""

import streamlit as st
import pandas as pd
from io import BytesIO

import database as db

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan Santri")
    return output.getvalue()

def render(scope_kelas: str = None, locked_santri_id: int = None):
    st.title("🧾 Laporan Data & Prediksi Santri")

    df = db.get_all_santri()
    if df.empty:
        st.info("Belum ada data.")
        return

    if scope_kelas:
        df = df[df["kelas"] == scope_kelas]
    if locked_santri_id is not None:
        df = df[df["id"] == locked_santri_id]
        if df.empty:
            st.info("Data anak Anda belum terdaftar.")
            return

    if locked_santri_id is not None:
        kelas_filter = "Semua"
    else:
        kelas_opsi = ["Semua"] + sorted(df["kelas"].dropna().unique().tolist())
        kelas_filter = st.selectbox("Filter Kelas", kelas_opsi)

    hasil = df.copy()
    if kelas_filter != "Semua":
        hasil = hasil[hasil["kelas"] == kelas_filter]

    st.subheader(f"Hasil: {len(hasil)} santri")

    if hasil.empty:
        st.warning("Tidak ada data pada filter ini.")
        return

    kolom_tampil = [
        "nis", "nama_santri", "kelas", "rata_jiyadah", "frekuensi_minggu",
        "total_hafalan", "target_hafalan_ayat", "hafalan_surat", "target_hafalan_juz",
        "rata_nilai", "estimasi_hari_selesai"
    ]
    st.dataframe(hasil[kolom_tampil], use_container_width=True, hide_index=True)

    st.markdown("##### 📌 Ringkasan Statistik")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Santri", len(hasil))
    col2.metric("Rata-rata Nilai Global", round(hasil["rata_nilai"].mean(), 1))
    col3.metric("Total Ayat Dihafal (Kolektif)", int(hasil["total_hafalan"].sum()))

    st.divider()
    st.markdown("##### ⬇️ Unduh Laporan")
    colx, coly = st.columns(2)
    with colx:
        csv = hasil[kolom_tampil].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV", data=csv,
            file_name=f"laporan_dataset_santri.csv",
            mime="text/csv", use_container_width=True,
        )
    with coly:
        excel_bytes = to_excel_bytes(hasil[kolom_tampil])
        st.download_button(
            "⬇️ Download Excel", data=excel_bytes,
            file_name=f"laporan_dataset_santri.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
