"""
modules/notifikasi.py
======================
FITUR: Kotak Masuk Notifikasi Harian untuk Wali Santri (F-08).
"""

import streamlit as st
import pandas as pd
import database as db

def render(locked_santri_id: int):
    st.title("🔔 Kotak Masuk Notifikasi")
    st.caption("Pemberitahuan aktivitas perkembangan hafalan Ananda tercinta.")

    if not locked_santri_id:
        st.error("Gagal memuat profil santri. Hubungi Admin.")
        return

    santri_df = db.get_santri_by_id(locked_santri_id)
    if santri_df.empty:
        st.error("Data profil Ananda tidak ditemukan.")
        return

    nama_anak = santri_df.iloc[0]["nama_santri"]
    
    st.markdown(f"### Pesan untuk Wali dari **{nama_anak}**")
    
    riwayat = db.get_hafalan_by_santri(locked_santri_id)

    if riwayat.empty:
        st.info("Belum ada notifikasi hafalan. Ustadz/Ustadzah belum memasukkan data setoran baru.")
        return

    # Tampilkan notifikasi dalam format timeline/kartu
    # Urutkan dari yang paling baru
    riwayat["tanggal_setor"] = pd.to_datetime(riwayat["tanggal_setor"])
    riwayat = riwayat.sort_values(by="tanggal_setor", ascending=False).reset_index(drop=True)

    for idx, row in riwayat.iterrows():
        tanggal = row["tanggal_setor"].strftime("%d %B %Y")
        jenis = row["jenis_setoran"]
        surah = row["surah"]
        ayat = row["jumlah_ayat"]
        nilai = row["nilai_setoran"]
        catatan = row["catatan"] if pd.notna(row["catatan"]) and row["catatan"].strip() != "" else "-"

        # Icon berdasarkan jenis setoran
        icon = "📖" if jenis == "Jiyadah" else "🔁"
        
        with st.container():
            st.markdown(f"**{tanggal}**")
            st.info(f"{icon} **{jenis}**: {nama_anak} telah menyetorkan hafalan **Surah {surah}** sebanyak **{ayat} ayat** dengan nilai **{nilai}**.\n\n"
                    f"*Catatan Ustadz*: {catatan}")
            st.write("---")
