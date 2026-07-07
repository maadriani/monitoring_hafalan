"""
modules/users.py
==================
FITUR: Kelola Pengguna (CRUD akun login) — KHUSUS ROLE ADMIN.

Mengatur 3 jenis akun:
- admin        : akses penuh
- wali_kelas   : akses dibatasi ke 1 kelas (kolom `kelas`)
- wali_santri  : akses dibatasi ke 1 santri/anak (kolom `santri_id`)
"""

import streamlit as st
import pandas as pd
import auth
import database as db


def render():
    st.title("🔐 Kelola Pengguna")
    st.caption("Mengatur akun login untuk Admin, Wali Kelas, dan Wali Santri.")

    df_users = db.get_all_users()
    santri_df = db.get_all_santri()

    tab1, tab2, tab3 = st.tabs(["📋 Daftar Pengguna", "➕ Tambah Pengguna", "✏️ Edit / Reset / Hapus"])

    # ------------------------------------------------------------
    # TAB 1: DAFTAR PENGGUNA (Dengan Filter & Search)
    # ------------------------------------------------------------
    with tab1:
        if df_users.empty:
            st.info("Belum ada pengguna.")
        else:
            c1, c2 = st.columns(2)
            filter_role = c1.radio("Filter Role", ["Semua", "Admin", "Wali Kelas", "Wali Santri"], horizontal=True)
            cari_nama = c2.text_input("🔍 Cari Username / Nama Lengkap")

            tampil = df_users.copy()

            if filter_role == "Admin":
                tampil = tampil[tampil["role"] == "admin"]
            elif filter_role == "Wali Kelas":
                tampil = tampil[tampil["role"] == "wali_kelas"]
            elif filter_role == "Wali Santri":
                tampil = tampil[tampil["role"] == "wali_santri"]

            if cari_nama:
                tampil = tampil[
                    tampil["username"].str.contains(cari_nama, case=False, na=False) |
                    tampil["nama_lengkap"].str.contains(cari_nama, case=False, na=False)
                ]

            label_role = {"admin": "🛡️ Admin", "wali_kelas": "👨‍🏫 Wali Kelas", "wali_santri": "👪 Wali Santri"}
            tampil["role_label"] = tampil["role"].map(label_role)
            tampil["kelas"] = tampil["kelas"].fillna("-")
            tampil["nama_anak"] = tampil["nama_anak"].fillna("-")
            
            st.markdown(f"**Total Data:** {len(tampil)} Pengguna")
            st.dataframe(
                tampil[["id", "username", "role_label", "nama_lengkap", "kelas", "nama_anak", "created_at"]],
                use_container_width=True,
                hide_index=True,
            )

    # ------------------------------------------------------------
    # TAB 2: TAMBAH PENGGUNA
    # ------------------------------------------------------------
    with tab2:
        role_baru = st.selectbox(
            "Role Pengguna Baru",
            ["admin", "wali_kelas", "wali_santri"],
            format_func=lambda x: {"admin": "🛡️ Admin", "wali_kelas": "👨‍🏫 Wali Kelas", "wali_santri": "👪 Wali Santri"}[x],
            key="role_tambah",
        )

        with st.form("form_tambah_user", clear_on_submit=True):
            c1, c2 = st.columns(2)
            username = c1.text_input("Username *")
            nama_lengkap = c2.text_input("Nama Lengkap *")
            password = c1.text_input("Password *", type="password")
            password2 = c2.text_input("Ulangi Password *", type="password")

            kelas = None
            santri_id = None

            if role_baru == "wali_kelas":
                if santri_df.empty:
                    st.warning("Belum ada data santri untuk mengambil daftar kelas.")
                else:
                    daftar_kelas = sorted(santri_df["kelas"].astype(str).dropna().unique().tolist())
                    kelas = st.selectbox("Pilih Kelas yang Diampu", daftar_kelas)
            elif role_baru == "wali_santri":
                if santri_df.empty:
                    st.warning("Belum ada data santri. Tambahkan santri dahulu di menu Data Santri.")
                else:
                    santri_id = st.selectbox(
                        "Anak / Santri yang Terhubung",
                        santri_df["id"],
                        format_func=lambda x: f"{santri_df[santri_df['id']==x]['nama_santri'].values[0]} "
                                               f"({santri_df[santri_df['id']==x]['kelas'].values[0]})",
                    )

            submitted = st.form_submit_button("💾 Simpan Pengguna", use_container_width=True)
            if submitted:
                if not username or not nama_lengkap or not password:
                    st.warning("Semua field bertanda * wajib diisi.")
                elif password != password2:
                    st.error("Password dan ulangi password tidak sama.")
                elif not db.get_user_by_username(username).empty:
                    st.error("Username sudah digunakan, pilih username lain.")
                else:
                    hashed = auth.hash_password(password)
                    ok = db.insert_user(username, hashed, role_baru, nama_lengkap, kelas, santri_id)
                    if ok:
                        st.success(f"Pengguna **{username}** berhasil ditambahkan.")
                        st.rerun()

    # ------------------------------------------------------------
    # TAB 3: EDIT / RESET PASSWORD / HAPUS (Dengan Filter)
    # ------------------------------------------------------------
    with tab3:
        if df_users.empty:
            st.info("Belum ada pengguna.")
            return

        st.markdown("Cari pengguna yang ingin diubah datanya:")
        c3, c4 = st.columns(2)
        edit_role_filter = c3.selectbox("Saring berdasarkan Role", ["Semua", "Admin", "Wali Kelas", "Wali Santri"])
        edit_search = c4.text_input("🔍 Cari Nama/Username (Opsional)")
        
        df_edit = df_users.copy()
        
        if edit_role_filter == "Admin":
            df_edit = df_edit[df_edit["role"] == "admin"]
        elif edit_role_filter == "Wali Kelas":
            df_edit = df_edit[df_edit["role"] == "wali_kelas"]
        elif edit_role_filter == "Wali Santri":
            df_edit = df_edit[df_edit["role"] == "wali_santri"]

        if edit_search:
            df_edit = df_edit[
                df_edit["username"].str.contains(edit_search, case=False, na=False) |
                df_edit["nama_lengkap"].str.contains(edit_search, case=False, na=False)
            ]

        if df_edit.empty:
            st.warning("Pengguna tidak ditemukan.")
            return

        pilihan = st.selectbox(
            "Pilih Pengguna untuk Diedit/Dihapus", df_edit["id"],
            format_func=lambda x: f"[{df_edit[df_edit['id']==x]['role'].values[0]}] "
                                   f"{df_edit[df_edit['id']==x]['username'].values[0]} "
                                   f"- {df_edit[df_edit['id']==x]['nama_lengkap'].values[0]}"
        )
        
        data = df_edit[df_edit["id"] == pilihan].iloc[0]

        st.divider()

        st.markdown(f"##### ✏️ Edit Data: **{data['username']}**")
        with st.form("form_edit_user"):
            nama_lengkap = st.text_input("Nama Lengkap", value=data["nama_lengkap"])
            role_opsi = ["admin", "wali_kelas", "wali_santri"]
            role_baru = st.selectbox("Role", role_opsi, index=role_opsi.index(data["role"]))

            kelas = data["kelas"]
            santri_id = data["santri_id"]
            
            if role_baru == "wali_kelas":
                santri_id = None
                if not santri_df.empty:
                    daftar_kelas = sorted(santri_df["kelas"].astype(str).dropna().unique().tolist())
                    default_idx = daftar_kelas.index(str(data["kelas"])) if str(data["kelas"]) in daftar_kelas else 0
                    kelas = st.selectbox("Pilih Kelas yang Diampu", daftar_kelas, index=default_idx)
                else:
                    kelas = st.text_input("Kelas yang Diampu", value=data["kelas"] or "")
            elif role_baru == "wali_santri":
                kelas = None
                if not santri_df.empty:
                    default_idx = 0
                    ids_list = santri_df["id"].tolist()
                    if data["santri_id"] in ids_list:
                        default_idx = ids_list.index(data["santri_id"])
                    santri_id = st.selectbox(
                        "Anak / Santri yang Terhubung", santri_df["id"], index=default_idx,
                        format_func=lambda x: santri_df[santri_df["id"] == x]["nama_santri"].values[0],
                    )
            else:
                kelas, santri_id = None, None

            if st.form_submit_button("💾 Update Pengguna", use_container_width=True):
                ok = db.update_user(pilihan, nama_lengkap, role_baru, kelas, santri_id)
                if ok:
                    st.success("Data pengguna berhasil diperbarui.")
                    st.rerun()

        st.markdown("##### 🔑 Reset Password")
        with st.form("form_reset_pw"):
            pw_baru = st.text_input("Password Baru", type="password")
            if st.form_submit_button("🔑 Reset Password"):
                if len(pw_baru) < 6:
                    st.warning("Password minimal 6 karakter.")
                else:
                    db.update_user_password(pilihan, auth.hash_password(pw_baru))
                    st.success("Password berhasil direset.")

        st.markdown("##### 🗑️ Hapus Pengguna")
        if data["username"] == st.session_state.get("username"):
            st.info("Anda tidak dapat menghapus akun yang sedang Anda gunakan.")
        else:
            if st.button("🗑️ Hapus Pengguna Ini", type="primary"):
                db.delete_user(pilihan)
                st.success("Pengguna berhasil dihapus.")
                st.rerun()
