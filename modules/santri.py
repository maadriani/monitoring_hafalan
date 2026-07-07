"""
modules/santri.py
===================
FITUR: CRUD (Tambah, Lihat, Edit, Hapus) Data Santri
       + Input/Update kategori hafalan manual (label untuk Random Forest).
"""

import streamlit as st
import database as db


def render(role: str = "admin", scope_kelas: str = None):
    st.title("👥 Data Santri")
    if scope_kelas:
        st.caption(f"Anda Wali Kelas **{scope_kelas}** — hanya bisa mengelola santri kelas ini.")

    tab1, tab2, tab3 = st.tabs(["📋 Daftar Santri", "➕ Tambah Santri", "✏️ Edit / Hapus / Beri Label"])

    # ------------------------------------------------------------
    # TAB 1: DAFTAR SANTRI
    # ------------------------------------------------------------
    with tab1:
        df = db.get_all_santri()
        if scope_kelas:
            df = df[df["kelas"] == scope_kelas]
        if df.empty:
            st.info("Belum ada data santri.")
        else:
            if scope_kelas:
                tampil = df
            else:
                filter_kelas = st.selectbox(
                    "Filter Kelas", ["Semua"] + sorted(df["kelas"].dropna().unique().tolist())
                )
                tampil = df if filter_kelas == "Semua" else df[df["kelas"] == filter_kelas]
            st.dataframe(
                tampil[["id", "nis", "nama", "jenis_kelamin", "kelas",
                        "tanggal_lahir", "tanggal_masuk", "kategori_hafalan"]],
                use_container_width=True,
                hide_index=True,
            )

    # ------------------------------------------------------------
    # TAB 2: TAMBAH SANTRI
    # ------------------------------------------------------------
    with tab2:
        with st.form("form_tambah_santri", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nis = c1.text_input("NIS")
            nama = c2.text_input("Nama Lengkap *")
            jk = c1.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            if scope_kelas:
                kelas = c2.text_input("Kelas", value=scope_kelas, disabled=True)
            else:
                kelas = c2.text_input("Kelas (contoh: 7A)")
            tgl_lahir = c1.date_input("Tanggal Lahir")
            tgl_masuk = c2.date_input("Tanggal Masuk")

            submitted = st.form_submit_button("💾 Simpan Santri", use_container_width=True)
            if submitted:
                if not nama:
                    st.warning("Nama wajib diisi.")
                else:
                    ok = db.insert_santri(nis, nama, jk, kelas, tgl_lahir, tgl_masuk)
                    if ok:
                        st.success(f"Santri **{nama}** berhasil ditambahkan.")
                        st.rerun()

    # ------------------------------------------------------------
    # TAB 3: EDIT / HAPUS / LABEL KATEGORI
    # ------------------------------------------------------------
    with tab3:
        df = db.get_all_santri()
        if scope_kelas:
            df = df[df["kelas"] == scope_kelas]
        if df.empty:
            st.info("Belum ada data santri.")
            return

        pilihan = st.selectbox(
            "Pilih Santri", df["id"], format_func=lambda x: df[df["id"] == x]["nama"].values[0]
        )
        data = df[df["id"] == pilihan].iloc[0]

        st.markdown("##### ✏️ Edit Data")
        with st.form("form_edit_santri"):
            c1, c2 = st.columns(2)
            nis = c1.text_input("NIS", value=data["nis"] or "")
            nama = c2.text_input("Nama Lengkap", value=data["nama"])
            jk = c1.selectbox(
                "Jenis Kelamin", ["Laki-laki", "Perempuan"],
                index=0 if data["jenis_kelamin"] == "Laki-laki" else 1,
            )
            kelas = c2.text_input("Kelas", value=data["kelas"] or "")
            tgl_lahir = c1.date_input("Tanggal Lahir", value=data["tanggal_lahir"])
            tgl_masuk = c2.date_input("Tanggal Masuk", value=data["tanggal_masuk"])

            if st.form_submit_button("💾 Update Data"):
                ok = db.update_santri(pilihan, nis, nama, jk, kelas, tgl_lahir, tgl_masuk)
                if ok:
                    st.success("Data santri berhasil diperbarui.")
                    st.rerun()

        st.markdown("##### 🏷️ Beri Label Kategori Hafalan (manual oleh Ustadz/Ustadzah)")
        st.caption(
            "Label ini digunakan sebagai **target/label** untuk melatih model "
            "Random Forest pada menu Prediksi."
        )
        kategori_sekarang = data["kategori_hafalan"] or "Belum Dinilai"
        opsi = ["Belum Dinilai", "Lancar", "Cukup", "Perlu Bimbingan"]
        kategori_baru = st.selectbox(
            "Kategori Hafalan", opsi, index=opsi.index(kategori_sekarang)
        )
        if st.button("💾 Simpan Label Kategori"):
            nilai_simpan = None if kategori_baru == "Belum Dinilai" else kategori_baru
            db.update_kategori_hafalan(pilihan, nilai_simpan)
            st.success("Label kategori berhasil disimpan.")
            st.rerun()

        st.markdown("##### 🗑️ Hapus Santri")
        if role != "admin":
            st.info("Hanya Admin yang dapat menghapus data santri.")
        else:
            st.warning("Menghapus santri akan ikut menghapus seluruh riwayat hafalannya.")
            if st.button("🗑️ Hapus Santri Ini", type="primary"):
                db.delete_santri(pilihan)
                st.success("Santri berhasil dihapus.")
                st.rerun()
