"""
modules/monitoring.py
=======================
FITUR: Monitoring Progress Hafalan per Santri (Grafik Tren Harian)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import database as db

def render(scope_kelas: str = None, locked_santri_id: int = None):
    st.title("📈 Monitoring Progres Hafalan")
    
    santri_df = db.get_all_santri()
    if scope_kelas:
        santri_df = santri_df[santri_df["kelas"] == scope_kelas]

    if santri_df.empty:
        st.warning("Belum ada data santri.")
        return

    # Filter santri
    if locked_santri_id is not None:
        pilihan_id = locked_santri_id
        nama_santri = santri_df[santri_df["id"] == pilihan_id]["nama_santri"].values[0]
        st.subheader(f"Statistik Hafalan: {nama_santri}")
    else:
        pilihan_id = st.selectbox(
            "Pilih Santri", santri_df["id"],
            format_func=lambda x: santri_df[santri_df["id"] == x]["nama_santri"].values[0]
        )

    # Ambil riwayat hafalan santri terpilih
    riwayat = db.get_hafalan_by_santri(pilihan_id)

    if riwayat.empty:
        st.info("Santri ini belum memiliki riwayat setoran (Jiyadah/Murojaah) harian.")
        return

    # Pastikan tipe tanggal
    riwayat["tanggal_setor"] = pd.to_datetime(riwayat["tanggal_setor"])
    riwayat = riwayat.sort_values(by="tanggal_setor")

    col1, col2 = st.columns(2)

    # GRAFIK 1: Tren Nilai Setoran Harian
    with col1:
        st.markdown("##### 📈 Tren Nilai Setoran")
        fig1 = px.line(
            riwayat, x="tanggal_setor", y="nilai_setoran", color="jenis_setoran",
            markers=True, title="Perkembangan Nilai per Setoran",
            labels={"tanggal_setor": "Tanggal Setor", "nilai_setoran": "Nilai Diberikan", "jenis_setoran": "Jenis"}
        )
        fig1.update_traces(
            hovertemplate="<b>Tanggal: %{x}</b><br>Nilai: %{y} poin<extra></extra>"
        )
        st.plotly_chart(fig1, use_container_width=True)

    # GRAFIK 2: Jumlah Ayat (Jiyadah vs Murojaah)
    with col2:
        st.markdown("##### 📊 Jumlah Ayat Disetor")
        fig2 = px.bar(
            riwayat, x="tanggal_setor", y="jumlah_ayat", color="jenis_setoran",
            title="Volume Hafalan per Hari", barmode="group",
            labels={"tanggal_setor": "Tanggal Setor", "jumlah_ayat": "Jumlah Ayat Disetor", "jenis_setoran": "Jenis"},
            text_auto=True
        )
        fig2.update_traces(
            hovertemplate="<b>Tanggal: %{x}</b><br>Disetor: %{y} Ayat<extra></extra>"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("📜 Riwayat Setoran Lengkap")
    tampil = riwayat[["tanggal_setor", "jenis_setoran", "surah", "jumlah_ayat", "nilai_setoran", "catatan"]]
    st.dataframe(tampil, use_container_width=True, hide_index=True)
