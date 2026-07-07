"""
modules/monitoring.py
=======================
FITUR: Monitoring Progress Hafalan per Santri
        (grafik perkembangan nilai & progres jumlah ayat/juz).
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import database as db

TOTAL_AYAT_QURAN = 6236


def render(scope_kelas: str = None, locked_santri_id: int = None):
    st.title("📈 Monitoring Progress Hafalan")

    santri_df = db.get_all_santri()
    if scope_kelas:
        santri_df = santri_df[santri_df["kelas"] == scope_kelas]

    if santri_df.empty:
        st.warning("Belum ada data santri.")
        return

    if locked_santri_id is not None:
        # Wali Santri: tidak ada pilihan, otomatis terkunci ke anaknya sendiri
        if locked_santri_id not in santri_df["id"].values:
            st.error("Data santri yang terhubung dengan akun Anda tidak ditemukan.")
            return
        santri_id = locked_santri_id
    else:
        santri_id = st.selectbox(
            "Pilih Santri", santri_df["id"],
            format_func=lambda x: santri_df[santri_df["id"] == x]["nama"].values[0],
        )
    info = santri_df[santri_df["id"] == santri_id].iloc[0]

    riwayat = db.get_hafalan_by_santri(santri_id)

    st.subheader(f"👤 {info['nama']}  ·  Kelas {info['kelas']}")
    badge = info["kategori_hafalan"] or "Belum Dinilai"
    warna = {"Lancar": "🟢", "Cukup": "🟡", "Perlu Bimbingan": "🔴", "Belum Dinilai": "⚪"}
    st.caption(f"{warna.get(badge,'⚪')} Kategori: **{badge}**")

    if riwayat.empty:
        st.info("Santri ini belum memiliki riwayat setoran hafalan.")
        return

    riwayat["tanggal_setor"] = pd.to_datetime(riwayat["tanggal_setor"])
    riwayat = riwayat.sort_values("tanggal_setor")

    # ---------------- METRICS ----------------
    total_ayat = int(riwayat["jumlah_ayat"].sum())
    total_setoran = len(riwayat)
    rata_nilai = round(
        riwayat[["nilai_kelancaran", "nilai_tajwid", "nilai_makhraj"]].mean().mean(), 1
    )
    progres_persen = round((total_ayat / TOTAL_AYAT_QURAN) * 100, 2)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Setoran", total_setoran)
    c2.metric("Total Ayat Dihafal", total_ayat)
    c3.metric("Rata-rata Nilai", rata_nilai)
    c4.metric("Progres Al-Qur'an", f"{progres_persen}%")

    st.progress(min(progres_persen / 100, 1.0))

    st.divider()

    # ---------------- GRAFIK PERKEMBANGAN NILAI ----------------
    st.subheader("Grafik Perkembangan Nilai")
    fig = px.line(
        riwayat,
        x="tanggal_setor",
        y=["nilai_kelancaran", "nilai_tajwid", "nilai_makhraj"],
        markers=True,
        labels={"value": "Nilai", "tanggal_setor": "Tanggal", "variable": "Aspek"},
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- GRAFIK DURASI & KESALAHAN ----------------
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Durasi Setor per Sesi (menit)")
        st.bar_chart(riwayat.set_index("tanggal_setor")["durasi_menit"])
    with col_b:
        st.subheader("Jumlah Kesalahan per Sesi")
        st.bar_chart(riwayat.set_index("tanggal_setor")["jumlah_kesalahan"])

    st.divider()
    st.subheader("📜 Riwayat Setoran Lengkap")
    st.dataframe(
        riwayat[["tanggal_setor", "surah", "juz", "ayat_mulai", "ayat_selesai",
                 "nilai_kelancaran", "nilai_tajwid", "nilai_makhraj",
                 "durasi_menit", "jumlah_kesalahan", "status_setoran", "catatan"]],
        use_container_width=True,
        hide_index=True,
    )
