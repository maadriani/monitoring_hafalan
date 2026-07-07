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
