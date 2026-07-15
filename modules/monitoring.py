"""
modules/monitoring.py
=======================
FITUR: Monitoring Progress Hafalan per Santri (Grafik Tren Harian + Live AI Prediction)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
import numpy as np

import database as db

def render(scope_kelas: str = None, locked_santri_id: int = None):
    st.title("📈 Monitoring Progres & Estimasi AI")
    st.caption("Pantau perkembangan hafalan harian santri sekaligus melihat kalkulasi estimasi kelulusan dari AI Colab secara live.")

    # Ambil data agregat fitur santri agar kita punya variabel untuk input AI
    santri_df = db.get_fitur_agregat_santri()
    if scope_kelas:
        santri_df = santri_df[santri_df["kelas"] == scope_kelas]

    if santri_df.empty:
        st.warning("Belum ada data santri.")
        return

    # Filter santri berdasarkan ID
    if locked_santri_id is not None:
        pilihan_id = locked_santri_id
        row_santri = santri_df[santri_df["id"] == pilihan_id]
        if not row_santri.empty:
            nama_santri = row_santri["nama_santri"].values[0]
            st.subheader(f"Statistik Hafalan: {nama_santri}")
        else:
            st.error("Data santri tidak ditemukan.")
            return
    else:
        pilihan_id = st.selectbox(
            "Pilih Santri", santri_df["id"],
            format_func=lambda x: santri_df[santri_df["id"] == x]["nama_santri"].values[0]
        )
        row_santri = santri_df[santri_df["id"] == pilihan_id]

    # =========================================================================
    # 🔥 INTEGRASI LIVE AI PREDICTION (ON-THE-FLY TANPA SIMPAN DATABASE)
    # =========================================================================
    MODEL_FILE = "model_random_forest_hafalan.pkl"
    
    if os.path.exists(MODEL_FILE) and not row_santri.empty:
        try:
            # Muat model terbaik hasil tuning Colab
            model = joblib.load(MODEL_FILE)
            santri_data = row_santri.iloc[0]
            
            # Ekstraksi dan pembersihan data fitur numerik santri terpilih
            # Kelas: ambil nilai integer (di DB tersimpan "1", "2", "3")
            kelas_val = pd.to_numeric(santri_data.get("kelas", 1), errors="coerce")
            if pd.isna(kelas_val):
                kelas_val = 1
            kelas_val = int(kelas_val)
                
            target_ayat = float(santri_data.get("target_hafalan_ayat", 1203) or 1203)
            total_ayat  = float(santri_data.get("total_hafalan", 0) or 0)
            jiyadah     = float(santri_data.get("rata_jiyadah", 0) or 0)
            frekuensi   = float(santri_data.get("frekuensi_minggu", 0) or 0)
            nilai       = float(santri_data.get("rata_nilai", 0) or 0)
            
            # Hitung Sisa Hafalan = fitur turunan (Sisa = Target - Total)
            sisa_hafalan = max(target_ayat - total_ayat, 1)

            # Susun dataframe input dengan nama kolom PERSIS sama seperti saat model dilatih di Colab
            # Sesuai: fitur_input = ["Kelas (MTs)", "Rata-rata Jiyadah/Hari (Ayat)",
            #         "Frekuensi Setoran/ Minggu", "Total Hafalan Saat Ini (Ayat)",
            #         "Sisa Hafalan (Ayat)", "Rata-rata Nilai Setoran"]
            data_input = pd.DataFrame([{
                "Kelas (MTs)":                   kelas_val,
                "Rata-rata Jiyadah/Hari (Ayat)": jiyadah,
                "Frekuensi Setoran/ Minggu":      frekuensi,
                "Total Hafalan Saat Ini (Ayat)":  total_ayat,
                "Sisa Hafalan (Ayat)":            sisa_hafalan,
                "Rata-rata Nilai Setoran":         nilai,
            }])

            # Prediksi instan di tempat menggunakan model .pkl
            hasil_prediksi = model.predict(data_input)[0]
            estimasi_bulat = int(np.round(hasil_prediksi))

            # Tampilkan Hasil Analisis Singkat AI di atas Grafik Utama
            st.markdown("### 🧠 Live AI Prediction Insights")
            col_ai1, col_ai2, col_ai3 = st.columns(3)
            col_ai1.metric("🎯 Sisa Target", f"{int(sisa_hafalan)} Ayat")
            col_ai2.metric("⚡ Kecepatan (Jiyadah)", f"{jiyadah:.1f} Ayat/Hari")
            col_ai3.metric("🔮 Estimasi Selesai (AI)", f"± {estimasi_bulat} Hari", delta="Prediksi Terhubung", delta_color="normal")
            
            st.info(f"💡 **Analisis AI:** Berdasarkan performa saat ini (Rata-rata Nilai Setoran: **{nilai:.1f}** dan Frekuensi Aktif: **{int(frekuensi)}x/minggu**), "
                    f"santri ini diprediksi oleh Random Forest dapat menyelesaikan target hafalannya dalam **{estimasi_bulat} hari** lagi.")
            st.markdown("---")
            
        except Exception as e:
            st.caption(f"ℹ️ Informasi: Gagal memuat prediksi live AI pada santri ini ({e})")
    else:
        st.info("💡 Hubungkan file `model_random_forest_hafalan.pkl` di folder utama proyek untuk mengaktifkan fitur Live AI Prediksi pada halaman monitoring ini.")

    # =========================================================================
    # LOGIK GRAFIK MONITORING PROGRESS (KODE LAMA ANDA YANG UTUH & RAPI)
    # =========================================================================
    # Ambil riwayat hafalan santri terpilih
    riwayat = db.get_hafalan_by_santri(pilihan_id)

    # Jika riwayat kosong, tampilkan statistik dasar dari tabel santri
    empty_riwayat = False
    if riwayat.empty:
        empty_riwayat = True
        # Tampilkan statistik awal dari tabel santri (profil hafalan)
        if not row_santri.empty:
            sd = row_santri.iloc[0]
            total_h = float(sd.get("total_hafalan", 0) or 0)
            target_h = float(sd.get("target_hafalan_ayat", 1203) or 1203)
            sisa_h = max(0, target_h - total_h)
            r_nilai = float(sd.get("rata_nilai", 0) or 0)
            pct = min(100, round((total_h / target_h * 100) if target_h > 0 else 0, 1))

            st.markdown("#### 📋 Statistik Profil Hafalan Santri")
            cs1, cs2, cs3, cs4 = st.columns(4)
            cs1.metric("📖 Total Hafalan", f"{int(total_h)} Ayat")
            cs2.metric("🎯 Target Hafalan", f"{int(target_h)} Ayat")
            cs3.metric("📉 Sisa Target", f"{int(sisa_h)} Ayat")
            cs4.metric("⭐ Rata-rata Nilai", f"{r_nilai:.1f}")
            st.progress(pct / 100, text=f"Progres Hafalan: **{pct}%**")

        st.info(
            "📭 Santri ini belum memiliki riwayat setoran harian (Jiyadah/Murojaah). "
            "Silakan tambahkan data melalui menu **Input Hafalan Harian**."
        )
        riwayat = pd.DataFrame(columns=["tanggal_setor", "jenis_setoran", "surah", "jumlah_ayat", "nilai_setoran", "catatan"])

    # Pastikan tipe tanggal
    riwayat["tanggal_setor"] = pd.to_datetime(riwayat["tanggal_setor"])
    riwayat = riwayat.sort_values(by="tanggal_setor")

    col1, col2 = st.columns(2)

    # GRAFIK 1: Tren Nilai Setoran Harian
    with col1:
        st.markdown("##### 📈 Tren Nilai Setoran")
        if not empty_riwayat:
            fig1 = px.line(
                riwayat, x="tanggal_setor", y="nilai_setoran", color="jenis_setoran",
                markers=True, title="Perkembangan Nilai per Setoran",
                labels={"tanggal_setor": "Tanggal Setor", "nilai_setoran": "Nilai Diberikan", "jenis_setoran": "Jenis"},
                color_discrete_sequence=["#2B5748", "#618764", "#9CB080", "#273338"],
            )
            fig1.update_traces(
                hovertemplate="<b>Tanggal: %{x}</b><br>Nilai: %{y} poin<extra></extra>"
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#273338")
            )
        else:
            placeholder_text = "Belum ada riwayat untuk santri ini.\nTambahkan data di menu Input Hafalan Harian."
            fig1 = go.Figure()
            fig1.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                annotations=[dict(text=placeholder_text, x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#273338"))],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
        st.plotly_chart(fig1, use_container_width=True)

    # GRAFIK 2: Jumlah Ayat (Jiyadah vs Murojaah)
    with col2:
        st.markdown("##### 📊 Jumlah Ayat Disetor")
        if not empty_riwayat:
            fig2 = px.bar(
                riwayat, x="tanggal_setor", y="jumlah_ayat", color="jenis_setoran",
                title="Volume Hafalan per Hari", barmode="group",
                labels={"tanggal_setor": "Tanggal Setor", "jumlah_ayat": "Jumlah Ayat Disetor", "jenis_setoran": "Jenis"},
                text_auto=True,
                color_discrete_sequence=["#618764", "#2B5748", "#9CB080", "#273338"],
            )
            fig2.update_traces(
                hovertemplate="<b>Tanggal: %{x}</b><br>Disetor: %{y} Ayat<extra></extra>"
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#273338")
            )
        else:
            fig2 = go.Figure()
            fig2.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                annotations=[dict(text="Tidak ada data jumlah ayat", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#273338"))],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("📜 Riwayat Setoran Lengkap")
    tampil = riwayat[["tanggal_setor", "jenis_setoran", "surah", "jumlah_ayat", "nilai_setoran", "catatan"]]
    st.dataframe(tampil, use_container_width=True, hide_index=True)