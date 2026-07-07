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
    """Menampilkan form login dengan desain UI/UX yang lebih modern."""
    bg_base64 = get_base64_image("OIP.webp")
    
    # CSS Styling - Modern Glassmorphism & Islamic Green Theme
    css_style = f"""
    <style>
    /* Background Image setup */
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/webp;base64,{bg_base64}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    /* Glassmorphism Form Container */
    div[data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 40px 30px !important;
        border-radius: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(43, 87, 72, 0.25) !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
    }}
    
    /* Submit Button Styling */
    [data-testid="stFormSubmitButton"] button {{
        background: linear-gradient(135deg, #2B5748 0%, #3e7c67 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }}
    [data-testid="stFormSubmitButton"] button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(43, 87, 72, 0.4) !important;
        background: linear-gradient(135deg, #1e3d32 0%, #2B5748 100%) !important;
    }}
    
    /* Expander Styling */
    div[data-testid="stExpander"] {{
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(43, 87, 72, 0.2) !important;
        border-radius: 16px !important;
        margin-top: 15px !important;
    }}
    </style>
    """
    
    if bg_base64:
        st.markdown(css_style, unsafe_allow_html=True)

    # Header Text
    st.markdown(
        "<h1 style='text-align:center; color:#2B5748; text-shadow: 0 2px 10px rgba(255,255,255,0.9); font-size: 2.5rem; margin-bottom: 0;'>📖 Monitoring Hafalan</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align:center; color:#1B3B2B; font-weight:600; margin-top: 0; text-shadow: 0 1px 5px rgba(255,255,255,0.8);'>Al-Qur'an</h3>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Centering the Form
    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        with st.form("form_login"):
            st.markdown("<h4 style='text-align:center; color:#2B5748; margin-bottom: 15px;'>Masuk ke Akun Anda</h4>", unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="Masukkan username di sini...")
            password = st.text_input("Password", type="password", placeholder="Masukkan password di sini...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔐 Login")

            if submitted:
                if not username or not password:
                    st.warning("⚠️ Username dan password wajib diisi.")
                else:
                    user_df = db.get_user_by_username(username)
                    if user_df.empty:
                        st.error("❌ Username tidak ditemukan.")
                    else:
                        user = user_df.iloc[0]
                        if verify_password(password, user["password"]):
                            _set_session(user)
                            st.rerun()
                        else:
                            st.error("❌ Password salah.")

        with st.expander("ℹ️ Akun Contoh (Bawaan Demo)"):
            st.info(
                "**Admin** \n\n Username: `admin` | Password: `admin123`\n\n"
                "---\n"
                "**Wali Kelas** \n\n Username: `guru_1` | Password: `guru123`\n\n"
                "---\n"
                "**Wali Santri** \n\n Username: `afiaalghoustunnur` | Password: `ortu123`"
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
