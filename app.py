"""
app.py
=======
APLIKASI: Monitoring Hafalan Al-Qur'an (Hybrid Architecture)
"""

import streamlit as st
import database as db
import auth
from modules import dashboard, santri, hafalan, monitoring, prediksi, laporan, users, notifikasi

st.set_page_config(
    page_title="Monitoring Hafalan (Hybrid)",
    page_icon="📖",
    layout="wide",
)

# -----------------------------------------------------------------------------
# CUSTOM STYLING (THEME REDESIGN WITH COLOR PALETTE)
# Palette: #9CB080 (Light Sage), #618764 (Medium Sage), #2B5748 (Forest Green), #273338 (Charcoal Slate)
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* Global Typography & Headers */
    h1, h2, h3 {
        color: #273338 !important;
        font-family: 'Inter', sans-serif;
    }
    h4, h5, h6 {
        color: #2B5748 !important;
    }
    
    /* Buttons Customization */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #2B5748 !important;
        color: #FFFFFF !important;
        border: 1px solid #618764 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease-in-out !important;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #618764 !important;
        border-color: #9CB080 !important;
        box-shadow: 0 4px 8px rgba(43, 87, 72, 0.2) !important;
        transform: translateY(-1px);
    }
    
    /* Metric Cards Customization */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(156, 176, 128, 0.18) 0%, rgba(97, 135, 100, 0.08) 100%) !important;
        border-left: 5px solid #2B5748 !important;
        border-top: 1px solid rgba(156, 176, 128, 0.3) !important;
        border-right: 1px solid rgba(156, 176, 128, 0.3) !important;
        border-bottom: 1px solid rgba(156, 176, 128, 0.3) !important;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 6px rgba(39, 51, 56, 0.05) !important;
    }
    div[data-testid="metric-container"] label {
        color: #273338 !important;
        font-weight: 600 !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #2B5748 !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar Styling Accents */
    section[data-testid="stSidebar"] {
        border-right: 2px solid #9CB080 !important;
    }
    section[data-testid="stSidebar"] .stRadio label span {
        color: #273338 !important;
        font-weight: 500 !important;
    }
    
    /* Dividers and Expanders */
    hr {
        border-color: #9CB080 !important;
        opacity: 0.6;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #618764 !important;
        border-radius: 8px !important;
        background-color: rgba(156, 176, 128, 0.05) !important;
    }
    
    /* Dataframe / Table Header accent */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(156, 176, 128, 0.4) !important;
        border-radius: 8px !important;
    }
    
    /* Info/Success/Warning Callouts */
    div.stAlert {
        border-radius: 8px !important;
        border-left-width: 5px !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

auth.require_login()

role = auth.current_role()
kelas_ampu = auth.current_kelas_ampu()
santri_id_anak = auth.current_santri_id_anak()

ROLE_LABEL = {"admin": "🛡️ Admin", "wali_kelas": "👨‍🏫 Wali Kelas", "wali_santri": "👪 Wali Santri"}

MENU_PER_ROLE = {
    "admin": [
        "📊 Dashboard",
        "👥 Profil Santri",
        "📥 Input Hafalan Harian",
        "📈 Monitoring Progres",
        "🌲 Model AI (Latih & Test)",
        "🧾 Laporan",
        "🔐 Kelola Pengguna",
    ],
    "wali_kelas": [
        "📊 Dashboard",
        "👥 Profil Santri",
        "📥 Input Hafalan Harian",
        "📈 Monitoring Progres",
        "🧾 Laporan",
    ],
    "wali_santri": [
        "🔔 Kotak Masuk (Notifikasi)",
        "📈 Monitoring Progres",
        "🧾 Laporan",
    ],
}

with st.sidebar:
    st.title("📖 Monitoring Hafalan")
    st.caption("Aplikasi Hybrid: Operasional + Prediksi AI")

    st.markdown(f"**{ROLE_LABEL.get(role, role)}**")
    st.caption(f"👤 {st.session_state.get('nama_lengkap', '')}")
    if role == "wali_kelas" and kelas_ampu:
        st.caption(f"🏷️ Kelas diampu: **{kelas_ampu}**")

    if st.button("🚪 Logout", use_container_width=True):
        auth.logout()

    st.divider()
    menu = st.radio("Pilih Fitur", MENU_PER_ROLE.get(role, []))
    st.divider()
    if db.test_connection():
        st.success("✅ Terhubung ke MySQL")
    else:
        st.error("❌ Tidak dapat terhubung ke MySQL.")

if menu == "📊 Dashboard":
    dashboard.render(scope_kelas=kelas_ampu if role == "wali_kelas" else None)

elif menu == "👥 Profil Santri":
    santri.render(role=role, scope_kelas=kelas_ampu if role == "wali_kelas" else None)

elif menu == "📥 Input Hafalan Harian":
    hafalan.render(scope_kelas=kelas_ampu if role == "wali_kelas" else None)

elif menu == "📈 Monitoring Progres":
    monitoring.render(
        scope_kelas=kelas_ampu if role == "wali_kelas" else None,
        locked_santri_id=santri_id_anak if role == "wali_santri" else None,
    )

elif menu == "🔔 Kotak Masuk (Notifikasi)":
    notifikasi.render(locked_santri_id=santri_id_anak)

elif menu == "🌲 Model AI (Latih & Test)":
    prediksi.render()

elif menu == "🧾 Laporan":
    laporan.render(
        scope_kelas=kelas_ampu if role == "wali_kelas" else None,
        locked_santri_id=santri_id_anak if role == "wali_santri" else None,
    )

elif menu == "🔐 Kelola Pengguna":
    users.render()
