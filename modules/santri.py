"""
modules/santri.py
===================
FITUR: Kelola Data Santri (Dataset)
"""

import streamlit as st
import pandas as pd
import database as db

def render(role: str, scope_kelas: str = None):
    st.title("👥 Data & Prediksi Santri")
    st.caption("Manajemen dataset murni. Ubah data di sini untuk update input AI.")

    df = db.get_all_santri()

    if scope_kelas:
        df = df[df["kelas"] == scope_kelas]
        st.caption(f"Menampilkan data untuk kelas: **{scope_kelas}**")

    # ------------------------------------------------------------
    # TAB 1: DAFTAR SANTRI
    # ------------------------------------------------------------
    tab1, tab2 = st.tabs(["📋 Data Santri (Dataset)", "➕ Tambah / Edit Data"])

    with tab1:
        if df.empty:
            st.info("Belum ada data santri. Silakan tambah data di tab sebelah.")
        else:
            cari = st.text_input("🔍 Cari Nama Santri")
            if cari:
                df = df[df["nama_santri"].str.contains(cari, case=False, na=False)]

            kolom_tampil = [
                "id", "nis", "nama_santri", "kelas", "rata_jiyadah", 
                "frekuensi_minggu", "total_hafalan", "target_hafalan_ayat",
                "hafalan_surat", "target_hafalan_juz", "rata_nilai", "estimasi_hari_selesai"
            ]
            st.dataframe(df[kolom_tampil], use_container_width=True, hide_index=True)

            if role == "admin":
                with st.expander("🗑️ Hapus Data Santri"):
                    hapus_id = st.number_input("Masukkan ID Santri yang ingin dihapus", min_value=0, step=1)
                    if st.button("Hapus Santri", type="primary"):
                        if hapus_id > 0:
                            db.delete_santri(hapus_id)
                            st.success(f"Santri dengan ID {hapus_id} berhasil dihapus.")
                            st.rerun()

    # ------------------------------------------------------------
    # TAB 2: TAMBAH / EDIT
    # ------------------------------------------------------------
    with tab2:
        if role not in ["admin", "wali_kelas"]:
            st.warning("Anda tidak memiliki hak akses untuk menambah/mengubah data santri.")
            return

        mode = st.radio("Mode", ["Tambah Santri Baru", "Edit Data Santri"], horizontal=True)

        if mode == "Tambah Santri Baru":
            st.subheader("➕ Tambah Data Baru")
            with st.form("form_tambah_santri", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nis = c1.text_input("NIS (Opsional / Generated)")
                nama = c2.text_input("Nama Santri*")
                
                c3, c4 = st.columns(2)
                kelas = c3.text_input("Kelas* (Mts)", value=scope_kelas if scope_kelas else "")
                hafalan_surat = c4.text_input("Hafalan (Surat)", value="")
                
                c5, c6, c7 = st.columns(3)
                rata_jiyadah = c5.number_input("Rata-rata Jiyadah/Hari (Ayat)", min_value=1, value=5)
                frekuensi = c6.number_input("Frekuensi Setoran/Minggu", min_value=1, value=5)
                total_hafalan = c7.number_input("Total Hafalan Saat Ini (Ayat)", min_value=0, value=0)
                
                c8, c9, c10 = st.columns(3)
                target_ayat = c8.number_input("Target Hafalan (Ayat)", min_value=0, value=100)
                target_juz = c9.number_input("Target Hafalan (Juz)", min_value=1, max_value=30, value=30)
                rata_nilai = c10.number_input("Rata-rata Nilai Setoran", min_value=0, max_value=100, value=80)

                submitted = st.form_submit_button("💾 Simpan Data", use_container_width=True)
                if submitted:
                    if not nama or not kelas:
                        st.error("Nama dan Kelas wajib diisi!")
                    else:
                        if not nis:
                            nis = f"NEW-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
                        ok = db.insert_santri(
                            nis, nama, kelas, rata_jiyadah, frekuensi, total_hafalan,
                            target_ayat, hafalan_surat, target_juz, rata_nilai, None
                        )
                        if ok:
                            st.success("Data berhasil ditambahkan!")
                            st.rerun()

        else:
            st.subheader("📝 Edit Data Santri")
            if df.empty:
                st.info("Tidak ada data untuk diedit.")
                return

            pilih_id = st.selectbox(
                "Pilih Santri yang ingin diedit", 
                df["id"], 
                format_func=lambda x: df[df["id"] == x]["nama_santri"].values[0]
            )
            
            row = df[df["id"] == pilih_id].iloc[0]
            
            with st.form("form_edit_santri"):
                c1, c2 = st.columns(2)
                e_nis = c1.text_input("NIS", value=row["nis"])
                e_nama = c2.text_input("Nama Santri*", value=row["nama_santri"])
                
                c3, c4 = st.columns(2)
                e_kelas = c3.text_input("Kelas*", value=row["kelas"])
                e_hafalan_surat = c4.text_input("Hafalan (Surat)", value=row["hafalan_surat"] if pd.notna(row["hafalan_surat"]) else "")
                
                c5, c6, c7 = st.columns(3)
                e_rata_jiyadah = c5.number_input("Rata-rata Jiyadah/Hari (Ayat)", min_value=1, value=int(row["rata_jiyadah"]))
                e_frekuensi = c6.number_input("Frekuensi Setoran/Minggu", min_value=1, value=int(row["frekuensi_minggu"]))
                e_total = c7.number_input("Total Hafalan Saat Ini (Ayat)", min_value=0, value=int(row["total_hafalan"]))
                
                c8, c9, c10 = st.columns(3)
                e_target_ayat = c8.number_input("Target Hafalan (Ayat)", min_value=0, value=int(row["target_hafalan_ayat"]))
                e_target_juz = c9.number_input("Target Hafalan (Juz)", min_value=1, max_value=30, value=int(row["target_hafalan_juz"]))
                e_rata_nilai = c10.number_input("Rata-rata Nilai Setoran", min_value=0, max_value=100, value=int(row["rata_nilai"]))

                e_estimasi = row["estimasi_hari_selesai"]

                submitted = st.form_submit_button("💾 Update Data", use_container_width=True)
                if submitted:
                    if not e_nama or not e_kelas:
                        st.error("Nama dan Kelas wajib diisi!")
                    else:
                        ok = db.update_santri(
                            pilih_id, e_nis, e_nama, e_kelas, e_rata_jiyadah, e_frekuensi,
                            e_total, e_target_ayat, e_hafalan_surat, e_target_juz, e_rata_nilai, e_estimasi
                        )
                        if ok:
                            st.success("Data santri berhasil diupdate!")
                            st.rerun()
