"""
app.py
=======
APLIKASI: Monitoring Hafalan Al-Qur'an
TECH STACK: Streamlit + Python + MySQL + scikit-learn (Random Forest)

3 ROLE PENGGUNA:
- admin       : akses penuh ke semua fitur & semua kelas
- wali_kelas  : akses dibatasi ke 1 kelas yang diampu
- wali_santri : akses hanya ke monitoring & laporan anaknya sendiri (read-only)

Jalankan dengan:
    streamlit run app.py
"""

import streamlit as st

import database as db
import auth
from modules import dashboard, santri, hafalan, monitoring, prediksi, laporan, users

st.set_page_config(
    page_title="Monitoring Hafalan Al-Qur'an",
    page_icon="📖",
    layout="wide",
)

# =====================================================================
# WAJIB LOGIN SEBELUM MENGAKSES APLIKASI
# =====================================================================
auth.require_login()

role = auth.current_role()
kelas_ampu = auth.current_kelas_ampu()
santri_id_anak = auth.current_santri_id_anak()

ROLE_LABEL = {"admin": "🛡️ Admin", "wali_kelas": "👨‍🏫 Wali Kelas", "wali_santri": "👪 Wali Santri"}

# =====================================================================
# DAFTAR MENU PER ROLE
# =====================================================================
MENU_PER_ROLE = {
    "admin": [
        "📊 Dashboard",
        "👥 Data Santri",
        "📥 Input Hafalan",
        "📈 Monitoring Progress",
        "🌲 Prediksi (Random Forest)",
        "🧾 Laporan",
        "🔐 Kelola Pengguna",
    ],
    "wali_kelas": [
        "📊 Dashboard",
        "👥 Data Santri",
        "📥 Input Hafalan",
        "📈 Monitoring Progress",
        "🧾 Laporan",
    ],
    "wali_santri": [
        "📈 Monitoring Progress",
        "🧾 Laporan",
    ],
}

# =====================================================================
# SIDEBAR: INFO USER, NAVIGASI, STATUS KONEKSI DATABASE
# =====================================================================
with st.sidebar:
    st.title("📖 Monitoring Hafalan")
    st.caption("Aplikasi berbasis Streamlit + MySQL + Random Forest")

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
        st.success("✅ Terhubung ke database MySQL")
    else:
        st.error("❌ Tidak dapat terhubung ke MySQL.\nCek konfigurasi di database.py")

    st.caption("© 2026 - Aplikasi Monitoring Hafalan Al-Qur'an")

# =====================================================================
# ROUTING ANTAR FITUR (data otomatis di-scope sesuai role)
# =====================================================================
if menu == "📊 Dashboard":
    dashboard.render(scope_kelas=kelas_ampu if role == "wali_kelas" else None)

elif menu == "👥 Data Santri":
    santri.render(role=role, scope_kelas=kelas_ampu if role == "wali_kelas" else None)

elif menu == "📥 Input Hafalan":
    hafalan.render(scope_kelas=kelas_ampu if role == "wali_kelas" else None)

elif menu == "📈 Monitoring Progress":
    monitoring.render(
        scope_kelas=kelas_ampu if role == "wali_kelas" else None,
        locked_santri_id=santri_id_anak if role == "wali_santri" else None,
    )

elif menu == "🌲 Prediksi (Random Forest)":
    prediksi.render()  # khusus admin

elif menu == "🧾 Laporan":
    laporan.render(
        scope_kelas=kelas_ampu if role == "wali_kelas" else None,
        locked_santri_id=santri_id_anak if role == "wali_santri" else None,
    )

elif menu == "🔐 Kelola Pengguna":
    users.render()  # khusus admin
