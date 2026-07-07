"""
modules/laporan.py
====================
FITUR: Laporan & Ekspor Data (filter periode/kelas + download CSV/Excel).
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from io import BytesIO

import database as db


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan Hafalan")
    return output.getvalue()


def render(scope_kelas: str = None, locked_santri_id: int = None):
    st.title("🧾 Laporan Hafalan")

    df = db.get_all_hafalan()
    if df.empty:
        st.info("Belum ada data setoran hafalan.")
        return

    df["tanggal_setor"] = pd.to_datetime(df["tanggal_setor"])

    if scope_kelas:
        df = df[df["kelas"] == scope_kelas]
    if locked_santri_id is not None:
        df = df[df["santri_id"] == locked_santri_id]
        if df.empty:
            st.info("Anak Anda belum memiliki riwayat setoran hafalan.")
            return

    c1, c2, c3 = st.columns(3)
    tgl_mulai = c1.date_input("Dari Tanggal", value=date.today() - timedelta(days=30))
    tgl_akhir = c2.date_input("Sampai Tanggal", value=date.today())

    if locked_santri_id is not None:
        kelas_filter = "Semua"  # wali santri tidak butuh filter kelas
    else:
        kelas_opsi = ["Semua"] + sorted(df["kelas"].dropna().unique().tolist())
        kelas_filter = c3.selectbox("Filter Kelas", kelas_opsi)

    hasil = df[
        (df["tanggal_setor"].dt.date >= tgl_mulai) & (df["tanggal_setor"].dt.date <= tgl_akhir)
    ]
    if kelas_filter != "Semua":
        hasil = hasil[hasil["kelas"] == kelas_filter]

    st.subheader(f"Hasil: {len(hasil)} data setoran")

    if hasil.empty:
        st.warning("Tidak ada data pada rentang/filter ini.")
        return

    kolom_tampil = [
        "nama_santri", "kelas", "surah", "juz", "ayat_mulai", "ayat_selesai",
        "tanggal_setor", "nilai_kelancaran", "nilai_tajwid", "nilai_makhraj",
        "durasi_menit", "jumlah_kesalahan", "status_setoran",
    ]
    st.dataframe(hasil[kolom_tampil], use_container_width=True, hide_index=True)

    st.markdown("##### 📌 Ringkasan Statistik")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Setoran", len(hasil))
    col2.metric("Rata-rata Kelancaran", round(hasil["nilai_kelancaran"].mean(), 1))
    col3.metric("Rata-rata Tajwid", round(hasil["nilai_tajwid"].mean(), 1))
    col4.metric("Rata-rata Makhraj", round(hasil["nilai_makhraj"].mean(), 1))

    st.divider()
    st.markdown("##### ⬇️ Unduh Laporan")
    colx, coly = st.columns(2)
    with colx:
        csv = hasil[kolom_tampil].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV", data=csv,
            file_name=f"laporan_hafalan_{tgl_mulai}_{tgl_akhir}.csv",
            mime="text/csv", use_container_width=True,
        )
    with coly:
        excel_bytes = to_excel_bytes(hasil[kolom_tampil])
        st.download_button(
            "⬇️ Download Excel", data=excel_bytes,
            file_name=f"laporan_hafalan_{tgl_mulai}_{tgl_akhir}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
