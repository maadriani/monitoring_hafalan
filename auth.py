"""
auth.py
========
FITUR: Login, Logout, dan pengecekan session untuk 3 role pengguna:
       admin, wali_kelas, wali_santri.

Password disimpan di database dalam bentuk HASH (bcrypt), tidak pernah
dalam bentuk plain text.
"""

import streamlit as st
import bcrypt

import database as db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _set_session(user):
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = int(user["id"])
    st.session_state["username"] = user["username"]
    st.session_state["role"] = user["role"]
    st.session_state["nama_lengkap"] = user["nama_lengkap"]
    st.session_state["kelas_ampu"] = user["kelas"]
    santri_id = user["santri_id"]
    st.session_state["santri_id_anak"] = None if pd_isna(santri_id) else int(santri_id)


def pd_isna(value) -> bool:
    """Helper kecil agar tidak perlu import pandas di file ini."""
    try:
        return value is None or value != value  # NaN != NaN -> True
    except Exception:
        return value is None


def render_login():
    """Menampilkan form login. Dipanggil dari app.py jika belum login."""
    st.markdown(
        "<h1 style='text-align:center;'>📖 Monitoring Hafalan Al-Qur'an</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("<p style='text-align:center;'>Silakan login untuk melanjutkan</p>",
                unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("form_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Masuk", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.warning("Username dan password wajib diisi.")
                else:
                    user_df = db.get_user_by_username(username)
                    if user_df.empty:
                        st.error("Username tidak ditemukan.")
                    else:
                        user = user_df.iloc[0]
                        if verify_password(password, user["password"]):
                            _set_session(user)
                            st.rerun()
                        else:
                            st.error("Password salah.")

        with st.expander("ℹ️ Akun contoh (bawaan demo)"):
            st.code(
                "Admin       -> username: admin       | password: admin123\n"
                "Wali Kelas  -> username: bu_guru7a   | password: walikelas123\n"
                "Wali Santri -> username: ortu_ahmad  | password: walisantri123",
                language="text",
            )
            st.caption("Segera ganti password ini lewat menu Kelola Pengguna (admin) setelah login.")


def logout():
    for key in [
        "logged_in", "user_id", "username", "role",
        "nama_lengkap", "kelas_ampu", "santri_id_anak",
        "rf_model", "rf_encoder",
    ]:
        st.session_state.pop(key, None)
    st.rerun()


def require_login():
    """Panggil di awal app.py. Akan menghentikan eksekusi jika belum login."""
    if not st.session_state.get("logged_in"):
        render_login()
        st.stop()


def current_role() -> str:
    return st.session_state.get("role", "")


def current_kelas_ampu():
    return st.session_state.get("kelas_ampu")


def current_santri_id_anak():
    return st.session_state.get("santri_id_anak")
