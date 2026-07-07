"""
modules/hafalan.py
====================
FITUR: Input Setoran Hafalan Harian (Jiyadah & Murojaah).
"""

import streamlit as st
from datetime import date
import database as db

DAFTAR_SURAH = [
    "Al-Fatihah", "An-Naba", "An-Nazi'at", "Al-Infitar", "Al-Inshiqaq",
    "Al-Buruj", "Al-A'la", "Al-Ghashiyah", "Al-Fajr", "Al-Balad",
    "Asy-Syams", "Al-Lail", "Adh-Dhuha", "Al-Insyirah", "At-Tin",
    "Al-'Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-'Adiyat",
    "Al-Qari'ah", "At-Takatsur", "Al-'Asr", "Al-Humazah", "Al-Fil",
    "Quraysh", "Al-Ma'un", "Al-Kautsar", "Al-Kafirun", "An-Nasr",
    "Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas", "Al-Baqarah",
    "Ali 'Imran", "An-Nisa", "Al-Maidah", "Yasin", "Ar-Rahman",
    "Al-Waqi'ah", "Al-Mulk", "Lainnya (ketik manual)",
]

def render(scope_kelas: str = None):
    st.title("📥 Input Setoran Harian")
    st.caption("Pilih jenis setoran: Jiyadah (Hafalan Baru) atau Murojaah (Pengulangan).")

    santri_df = db.get_all_santri()
    if scope_kelas:
        santri_df = santri_df[santri_df["kelas"] == scope_kelas]
        st.caption(f"Menampilkan data untuk kelas: **{scope_kelas}**")

    if santri_df.empty:
        st.warning("Tambahkan data santri terlebih dahulu di menu **Profil Santri**.")
        return

    tab1, tab2 = st.tabs(["➕ Input Setoran Baru", "📜 Riwayat Setoran"])

    # ------------------------------------------------------------
    # TAB 1: INPUT SETORAN BARU
    # ------------------------------------------------------------
    with tab1:
        with st.form("form_hafalan", clear_on_submit=True):
            santri_id = st.selectbox(
                "Pilih Santri", santri_df["id"],
                format_func=lambda x: santri_df[santri_df["id"] == x]["nama_santri"].values[0],
            )

            c_jenis, c_tgl = st.columns(2)
            jenis_setoran = c_jenis.selectbox("Jenis Setoran", ["Jiyadah", "Murojaah"])
            tanggal_setor = c_tgl.date_input("Tanggal Setor", value=date.today())

            c1, c2 = st.columns(2)
            surah = c1.selectbox("Surah", DAFTAR_SURAH)
            if surah == "Lainnya (ketik manual)":
                surah = c1.text_input("Nama Surah Manual")
            
            jumlah_ayat = c2.number_input("Jumlah Ayat Disetor", min_value=1, value=5)

            st.markdown("##### Penilaian (skala 0 - 100)")
            nilai_setoran = st.slider("Nilai Setoran", 0, 100, 80)
            catatan = st.text_area("Catatan Ustadz/Ustadzah (opsional)")

            submitted = st.form_submit_button("💾 Simpan Setoran", use_container_width=True)
            if submitted:
                ok = db.insert_hafalan(
                    santri_id=santri_id, 
                    jenis_setoran=jenis_setoran, 
                    surah=surah, 
                    jumlah_ayat=jumlah_ayat,
                    tanggal_setor=tanggal_setor, 
                    nilai_setoran=nilai_setoran, 
                    catatan=catatan
                )
                if ok:
                    st.success("Setoran hafalan berhasil disimpan ✅")
                    st.rerun()

    # ------------------------------------------------------------
    # TAB 2: RIWAYAT SETORAN
    # ------------------------------------------------------------
    with tab2:
        df = db.get_all_hafalan()
        if scope_kelas and not df.empty:
            df = df[df["kelas"] == scope_kelas]
        if df.empty:
            st.info("Belum ada riwayat setoran.")
            return

        nama_filter = st.multiselect("Filter Santri", df["nama_santri"].unique())
        tampil = df if not nama_filter else df[df["nama_santri"].isin(nama_filter)]

        st.dataframe(
            tampil[["id", "nama_santri", "kelas", "jenis_setoran", "surah", "jumlah_ayat",
                    "tanggal_setor", "nilai_setoran", "catatan"]],
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("🗑️ Hapus Data Setoran"):
            hapus_id = st.number_input("Masukkan ID Setoran yang ingin dihapus", min_value=0, step=1)
            if st.button("Hapus Setoran"):
                if hapus_id > 0:
                    db.delete_hafalan(hapus_id)
                    st.success(f"Setoran dengan ID {hapus_id} berhasil dihapus.")
                    st.rerun()
