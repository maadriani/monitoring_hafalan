"""
modules/hafalan.py
====================
FITUR: Input Setoran Hafalan & Riwayat Setoran.
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
    st.title("📥 Input Setoran Hafalan")

    santri_df = db.get_all_santri()
    if scope_kelas:
        santri_df = santri_df[santri_df["kelas"] == scope_kelas]
        st.caption(f"Menampilkan data untuk kelas: **{scope_kelas}**")

    if santri_df.empty:
        st.warning("Tambahkan data santri terlebih dahulu di menu **Data Santri**.")
        return

    tab1, tab2 = st.tabs(["➕ Input Setoran Baru", "📜 Riwayat Setoran"])

    # ------------------------------------------------------------
    # TAB 1: INPUT SETORAN BARU
    # ------------------------------------------------------------
    with tab1:
        with st.form("form_hafalan", clear_on_submit=True):
            santri_id = st.selectbox(
                "Pilih Santri", santri_df["id"],
                format_func=lambda x: santri_df[santri_df["id"] == x]["nama"].values[0],
            )

            c1, c2, c3 = st.columns(3)
            surah = c1.selectbox("Surah", DAFTAR_SURAH)
            if surah == "Lainnya (ketik manual)":
                surah = c1.text_input("Nama Surah Manual")
            juz = c2.number_input("Juz", min_value=1, max_value=30, value=1)
            tanggal_setor = c3.date_input("Tanggal Setor", value=date.today())

            c4, c5 = st.columns(2)
            ayat_mulai = c4.number_input("Ayat Mulai", min_value=1, value=1)
            ayat_selesai = c5.number_input("Ayat Selesai", min_value=1, value=5)

            st.markdown("##### Penilaian (skala 0 - 100)")
            c6, c7, c8 = st.columns(3)
            nilai_kelancaran = c6.slider("Kelancaran", 0, 100, 80)
            nilai_tajwid = c7.slider("Tajwid", 0, 100, 80)
            nilai_makhraj = c8.slider("Makhrajul Huruf", 0, 100, 80)

            c9, c10 = st.columns(2)
            durasi_menit = c9.number_input("Durasi Setor (menit)", min_value=1, value=10)
            jumlah_kesalahan = c10.number_input("Jumlah Kesalahan", min_value=0, value=0)

            status_setoran = st.selectbox("Status Setoran", ["Lulus", "Mengulang", "Belum Lancar"])
            catatan = st.text_area("Catatan Ustadz/Ustadzah (opsional)")

            submitted = st.form_submit_button("💾 Simpan Setoran", use_container_width=True)
            if submitted:
                if ayat_selesai < ayat_mulai:
                    st.error("Ayat selesai tidak boleh kurang dari ayat mulai.")
                else:
                    ok = db.insert_hafalan(
                        santri_id, surah, juz, ayat_mulai, ayat_selesai,
                        tanggal_setor, nilai_kelancaran, nilai_tajwid,
                        nilai_makhraj, durasi_menit, jumlah_kesalahan,
                        status_setoran, catatan,
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
            tampil[["id", "nama_santri", "kelas", "surah", "juz", "ayat_mulai",
                    "ayat_selesai", "tanggal_setor", "nilai_kelancaran",
                    "nilai_tajwid", "nilai_makhraj", "status_setoran"]],
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
