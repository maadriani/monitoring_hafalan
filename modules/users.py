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

import auth
import database as db


def render():
    st.title("🔐 Kelola Pengguna")
    st.caption("Mengatur akun login untuk Admin, Wali Kelas, dan Wali Santri.")

    tab1, tab2, tab3 = st.tabs(["📋 Daftar Pengguna", "➕ Tambah Pengguna", "✏️ Edit / Reset Password / Hapus"])

    santri_df = db.get_all_santri()

    # ------------------------------------------------------------
    # TAB 1: DAFTAR PENGGUNA
    # ------------------------------------------------------------
    with tab1:
        df = db.get_all_users()
        if df.empty:
            st.info("Belum ada pengguna.")
        else:
            label_role = {"admin": "🛡️ Admin", "wali_kelas": "👨‍🏫 Wali Kelas", "wali_santri": "👪 Wali Santri"}
            tampil = df.copy()
            tampil["role"] = tampil["role"].map(label_role)
            tampil["kelas"] = tampil["kelas"].fillna("-")
            tampil["nama_anak"] = tampil["nama_anak"].fillna("-")
            st.dataframe(
                tampil[["id", "username", "role", "nama_lengkap", "kelas", "nama_anak", "created_at"]],
                use_container_width=True,
                hide_index=True,
            )

    # ------------------------------------------------------------
    # TAB 2: TAMBAH PENGGUNA
    # ------------------------------------------------------------
    with tab2:
        role_baru = st.selectbox(
            "Role Pengguna",
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
                kelas = st.text_input(
                    "Kelas yang Diampu (harus sama dengan kolom kelas di Data Santri, contoh: 7A)"
                )
            elif role_baru == "wali_santri":
                if santri_df.empty:
                    st.warning("Belum ada data santri. Tambahkan santri dahulu di menu Data Santri.")
                else:
                    santri_id = st.selectbox(
                        "Anak / Santri yang Terhubung",
                        santri_df["id"],
                        format_func=lambda x: f"{santri_df[santri_df['id']==x]['nama'].values[0]} "
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
    # TAB 3: EDIT / RESET PASSWORD / HAPUS
    # ------------------------------------------------------------
    with tab3:
        df = db.get_all_users()
        if df.empty:
            st.info("Belum ada pengguna.")
            return

        pilihan = st.selectbox(
            "Pilih Pengguna", df["id"],
            format_func=lambda x: f"{df[df['id']==x]['username'].values[0]} "
                                   f"({df[df['id']==x]['nama_lengkap'].values[0]})",
        )
        data = df[df["id"] == pilihan].iloc[0]

        st.markdown("##### ✏️ Edit Data Pengguna")
        with st.form("form_edit_user"):
            nama_lengkap = st.text_input("Nama Lengkap", value=data["nama_lengkap"])
            role_opsi = ["admin", "wali_kelas", "wali_santri"]
            role = st.selectbox("Role", role_opsi, index=role_opsi.index(data["role"]))

            kelas = data["kelas"]
            santri_id = data["santri_id"]
            if role == "wali_kelas":
                kelas = st.text_input("Kelas yang Diampu", value=data["kelas"] or "")
                santri_id = None
            elif role == "wali_santri":
                kelas = None
                if not santri_df.empty:
                    default_idx = 0
                    ids_list = santri_df["id"].tolist()
                    if data["santri_id"] in ids_list:
                        default_idx = ids_list.index(data["santri_id"])
                    santri_id = st.selectbox(
                        "Anak / Santri yang Terhubung", santri_df["id"], index=default_idx,
                        format_func=lambda x: santri_df[santri_df["id"] == x]["nama"].values[0],
                    )
            else:
                kelas, santri_id = None, None

            if st.form_submit_button("💾 Update Pengguna"):
                ok = db.update_user(pilihan, nama_lengkap, role, kelas, santri_id)
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
