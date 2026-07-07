"""
modules/dashboard.py
=====================
FITUR: Dashboard ringkasan / KPI utama monitoring hafalan.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

import database as db


def render(scope_kelas: str = None):
    st.title("📊 Dashboard Monitoring Hafalan Al-Qur'an")
    if scope_kelas:
        st.caption(f"Menampilkan data untuk kelas: **{scope_kelas}**")

    santri_df = db.get_all_santri()
    hafalan_df = db.get_all_hafalan()

    if scope_kelas:
        santri_df = santri_df[santri_df["kelas"] == scope_kelas]
        if not hafalan_df.empty:
            hafalan_df = hafalan_df[hafalan_df["kelas"] == scope_kelas]

    if santri_df.empty:
        st.info("Belum ada data santri. Tambahkan data di menu **Data Santri**.")
        return

    # ---------------- KPI CARDS ----------------
    total_santri = len(santri_df)
    bulan_ini = pd.Timestamp(date.today()).to_period("M")
    setoran_bulan_ini = 0
    rata_nilai = 0

    if not hafalan_df.empty:
        hafalan_df["tanggal_setor"] = pd.to_datetime(hafalan_df["tanggal_setor"])
        setoran_bulan_ini = (hafalan_df["tanggal_setor"].dt.to_period("M") == bulan_ini).sum()
        rata_nilai = round(
            hafalan_df[["nilai_kelancaran", "nilai_tajwid", "nilai_makhraj"]]
            .mean()
            .mean(),
            1,
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Santri", total_santri)
    col2.metric("📥 Setoran Bulan Ini", int(setoran_bulan_ini))
    col3.metric("⭐ Rata-rata Nilai", f"{rata_nilai}")
    col4.metric("📚 Total Setoran", len(hafalan_df))

    st.divider()

    col_a, col_b = st.columns(2)

    # ---------------- DISTRIBUSI KATEGORI ----------------
    with col_a:
        st.subheader("Distribusi Kategori Hafalan")
        kategori_count = santri_df["kategori_hafalan"].fillna("Belum Dinilai").value_counts()
        fig = px.pie(
            names=kategori_count.index,
            values=kategori_count.values,
            hole=0.4,
            color=kategori_count.index,
            color_discrete_map={
                "Lancar": "#2ecc71",
                "Cukup": "#f1c40f",
                "Perlu Bimbingan": "#e74c3c",
                "Belum Dinilai": "#95a5a6",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- TOP 5 SANTRI ----------------
    with col_b:
        st.subheader("🏆 Top 5 Nilai Rata-rata Tertinggi")
        if not hafalan_df.empty:
            agg = (
                hafalan_df.groupby("nama_santri")[
                    ["nilai_kelancaran", "nilai_tajwid", "nilai_makhraj"]
                ]
                .mean()
                .mean(axis=1)
                .sort_values(ascending=False)
                .head(5)
                .reset_index()
            )
            agg.columns = ["Nama Santri", "Rata-rata Nilai"]
            agg["Rata-rata Nilai"] = agg["Rata-rata Nilai"].round(1)
            st.dataframe(agg, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data setoran hafalan.")

    st.divider()
    st.subheader("📈 Tren Jumlah Setoran per Tanggal")
    if not hafalan_df.empty:
        tren = hafalan_df.groupby(hafalan_df["tanggal_setor"].dt.date).size().reset_index()
        tren.columns = ["Tanggal", "Jumlah Setoran"]
        fig2 = px.line(tren, x="Tanggal", y="Jumlah Setoran", markers=True)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Belum ada data setoran untuk ditampilkan.")
