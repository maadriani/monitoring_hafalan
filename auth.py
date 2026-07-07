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


def get_base64_image(image_path: str) -> str:
    import base64
    import os
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return ""


def render_login():
    """Menampilkan form login. Dipanggil dari app.py jika belum login."""
    bg_base64 = get_base64_image("OIP.webp")
    if bg_base64:
        st.markdown(
            f"""
            <style>
            /* Background OIP.webp untuk Halaman Login */
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/webp;base64,{bg_base64}") !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
            }}
            [data-testid="stHeader"] {{
                background: transparent !important;
            }}
            div[data-testid="stForm"] {{
                background: rgba(255, 255, 255, 0.96) !important;
                padding: 35px !important;
                border-radius: 16px !important;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
                border: 2px solid #2B5748 !important;
            }}
            div[data-testid="stExpander"] {{
                background: rgba(255, 255, 255, 0.92) !important;
                border: 1px solid #2B5748 !important;
                border-radius: 10px !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "<h1 style='text-align:center; color:#2B5748; text-shadow: 0 2px 4px rgba(255,255,255,0.8);'>📖 Monitoring Hafalan Al-Qur'an</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("<p style='text-align:center; color:#1B3B2B; font-weight:600; text-shadow: 0 1px 2px rgba(255,255,255,0.8);'>Silakan login untuk melanjutkan</p>",
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
                "Admin       -> username: admin          | password: admin123\n"
                "Wali Kelas  -> username: guru_1         | password: guru123\n"
                "Wali Santri -> username: ortu_MIG-1000  | password: ortu123",
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
