"""
modules/dashboard.py
=====================
FITUR: Dashboard ringkasan / KPI utama monitoring hafalan (Dataset-based).
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

    if scope_kelas:
        santri_df = santri_df[santri_df["kelas"] == scope_kelas]

    if santri_df.empty:
        st.info("Belum ada data santri. Tambahkan data di menu **Data & Prediksi**.")
        return

    # ---------------- KPI CARDS ----------------
    total_santri = len(santri_df)
    rata_nilai = round(santri_df["rata_nilai"].mean(), 1) if not santri_df["rata_nilai"].isna().all() else 0
    total_ayat_kolektif = int(santri_df["total_hafalan"].sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total Santri", total_santri)
    col2.metric("⭐ Rata-rata Nilai Setoran", f"{rata_nilai}")
    col3.metric("📚 Total Ayat Terhafal (Kolektif)", f"{total_ayat_kolektif} Ayat")

    st.divider()

    col_a, col_b = st.columns(2)

    # ---------------- DISTRIBUSI ESTIMASI HARI ----------------
    with col_a:
        st.subheader("Distribusi Estimasi Khatam (AI)")
        bins = [0, 30, 90, 365, 9999]
        labels = ["< 1 Bulan", "1 - 3 Bulan", "3 - 12 Bulan", "> 1 Tahun"]
        
        santri_df["estimasi_hari_selesai"] = pd.to_numeric(santri_df["estimasi_hari_selesai"], errors="coerce")
        
        estimasi_cat = pd.cut(santri_df["estimasi_hari_selesai"], bins=bins, labels=labels)
        kategori_count = estimasi_cat.astype(str).replace("nan", "Belum Estimasi (Proses AI)").value_counts()
        
        fig = px.pie(
            names=kategori_count.index,
            values=kategori_count.values,
            hole=0.4,
            color=kategori_count.index,
            color_discrete_sequence=["#2B5748", "#618764", "#9CB080", "#273338"],
        )
        
        # Kustomisasi teks yang muncul saat mouse diarahkan (Tooltip Hover)
        fig.update_traces(
            hovertemplate="<b>Estimasi: %{label}</b><br>Jumlah: %{value} Santri<br>Persentase: %{percent}<extra></extra>",
            textinfo="percent+label",
            textfont_size=14
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#273338")
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- TOP 5 SANTRI ----------------
    with col_b:
        st.subheader("🏆 Top 5 Santri (Berdasarkan Ayat Terbanyak)")
        if not santri_df.empty:
            agg = santri_df.sort_values(by="total_hafalan", ascending=False).head(5)
            tampil_top = agg[["nama_santri", "kelas", "total_hafalan", "rata_nilai"]]
            st.dataframe(tampil_top, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data.")

    st.divider()
    st.subheader("Rata-rata Nilai per Kelas")
    if not santri_df.empty:
        tren = santri_df.groupby("kelas")["rata_nilai"].mean().reset_index()
        fig2 = px.bar(
            tren, x="kelas", y="rata_nilai", 
            title="Perbandingan Nilai Rata-rata Antar Kelas",
            labels={"kelas": "Nama Kelas", "rata_nilai": "Nilai Rata-rata"},
            color="kelas",
            color_discrete_sequence=["#2B5748", "#618764", "#9CB080", "#273338"],
            text_auto='.1f' # Menampilkan angka di atas batang
        )
        fig2.update_traces(
            hovertemplate="<b>Kelas: %{x}</b><br>Nilai Rata-rata: %{y:.1f}<extra></extra>"
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#273338")
        )
        st.plotly_chart(fig2, use_container_width=True)
