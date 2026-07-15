"""
modules/prediksi.py
FITUR: Evaluasi Model AI Random Forest (dari Google Colab) dan Prediksi Estimasi Hari Selesai Hafalan.
Menggunakan model .pkl yang sudah dilatih di Colab. Tidak melatih ulang.
Modul evaluasi model Random Forest Hafalan Al-Qur'an.
"""
import math
import os
import joblib
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import database as db

MODEL_FILE = "model_random_forest_hafalan.pkl"

# Kolom fitur PERSIS sesuai saat model dilatih di Google Colab
# Kolom fitur sesuai dataset histori hafalan santri
FITUR_INPUT = [
    "Kelas (MTs)",
    "Rata-rata Jiyadah/Hari (Ayat)",
    "Frekuensi Setoran/ Minggu",
    "Total Hafalan Saat Ini (Ayat)",
    "Sisa Hafalan (Ayat)",
    "Rata-rata Nilai Setoran",
]


def _hitung_estimasi_formula(row) -> int:
    target  = float(row.get("target_hafalan_ayat") or 1203)
    current = float(row.get("total_hafalan") or 0)
    jiyadah = float(row.get("rata_jiyadah") or 5)
    frek    = float(row.get("frekuensi_minggu") or 5)
    nilai   = float(row.get("rata_nilai") or 80)
    sisa    = max(1.0, target - current)
    kec     = max(0.5, (jiyadah * frek * (nilai / 100)) / 7.0)
    return max(1, math.ceil(sisa / kec))


def _prepare_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    kelas_num = pd.to_numeric(df_raw["kelas"], errors="coerce").fillna(1).astype(int)
    jiyadah   = pd.to_numeric(df_raw["rata_jiyadah"], errors="coerce").fillna(0)
    frekuensi = pd.to_numeric(df_raw["frekuensi_minggu"], errors="coerce").fillna(0)
    total     = pd.to_numeric(df_raw["total_hafalan"], errors="coerce").fillna(0)
    target    = pd.to_numeric(df_raw["target_hafalan_ayat"], errors="coerce").fillna(1203)
    sisa      = (target - total).clip(lower=1)
    nilai     = pd.to_numeric(df_raw["rata_nilai"], errors="coerce").fillna(0)
    df_feat = pd.DataFrame({
        "Kelas (MTs)":                   kelas_num,
        "Rata-rata Jiyadah/Hari (Ayat)": jiyadah,
        "Frekuensi Setoran/ Minggu":      frekuensi,
        "Total Hafalan Saat Ini (Ayat)":  total,
        "Sisa Hafalan (Ayat)":            sisa,
        "Rata-rata Nilai Setoran":         nilai,
    })
    return df_feat[FITUR_INPUT]


def render():
    st.title("Model AI - Random Forest Regressor")
    st.caption(
        "Evaluasi model Random Forest yang telah dilatih di Google Colab "
        "dan prediksi estimasi hari selesai hafalan santri."
    )

    # Cek file model
    if not os.path.exists(MODEL_FILE):
        st.error(f"File model `{MODEL_FILE}` tidak ditemukan di folder proyek.")
        st.info(
            "Letakkan file `model_random_forest_hafalan.pkl` hasil training Colab "
            "di folder yang sama dengan `app.py`, kemudian refresh halaman ini."
        )
        return

    # Load model
    try:
        model = joblib.load(MODEL_FILE)
    except Exception as e:
        st.error(f"Gagal memuat model: {e}")
        return

    # Load data profil dasar dari DB (Modal awal yang identik dengan dataset Colab)
    df_raw = db.get_all_santri()
    if df_raw.empty:
        st.warning("Belum ada data santri di database.")
        return

    # Guard kolom
    required_cols = [
        "rata_jiyadah", "frekuensi_minggu", "total_hafalan",
        "target_hafalan_ayat", "rata_nilai", "kelas", "estimasi_hari_selesai"
    ]
    for col in required_cols:
        if col not in df_raw.columns:
            df_raw[col] = None

    # 1. Preview Dataset
    st.markdown("### 1. Preview Dataset Santri")
    tampil_cols = [
        "nama_santri", "kelas", "rata_jiyadah", "frekuensi_minggu",
        "total_hafalan", "target_hafalan_ayat", "rata_nilai", "estimasi_hari_selesai"
    ]
    rename_map = {
        "nama_santri": "Nama Santri", "kelas": "Kelas (MTs)",
        "rata_jiyadah": "Rata-rata Jiyadah/Hari", "frekuensi_minggu": "Frekuensi Setoran/Minggu",
        "total_hafalan": "Total Hafalan (Ayat)", "target_hafalan_ayat": "Target (Ayat)",
        "rata_nilai": "Rata-rata Nilai Setoran", "estimasi_hari_selesai": "Estimasi Hari Selesai (DB)"
    }
    st.dataframe(
        df_raw[tampil_cols].rename(columns=rename_map).head(10),
        use_container_width=True, hide_index=True
    )
    st.caption(f"Total data: **{len(df_raw)} santri** dalam database.")

    # 2. Persiapan Data (Tidak ditampilkan di UI agar rapi saat demo)

    X = _prepare_features(df_raw)

    # Label Y (Aktual) dihitung dari formula secara dinamis untuk evaluasi yang akurat
    # (mengabaikan data lama di database yang mungkin usang atau salah)
    y_label = df_raw.apply(_hitung_estimasi_formula, axis=1)
    y = y_label.astype(float)


    # Prediksi dengan model pkl
    y_pred = model.predict(X)

    # 2. Evaluasi Model (Sebelumnya 3)
    st.markdown("### 2. Evaluasi Model Random Forest")
    mae  = mean_absolute_error(y, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
    r2   = r2_score(y, y_pred)

    c1, c2, c3 = st.columns(3)
    c1.metric("MAE (Mean Absolute Error)", f"{mae:.2f} Hari",
              help="Rata-rata selisih absolut antara prediksi dan nilai aktual")
    c2.metric("RMSE (Root Mean Squared Error)", f"{rmse:.2f} Hari",
              help="Akar kuadrat rata-rata error kuadrat")
    c3.metric("R2 (Koefisien Determinasi)", f"{r2:.4f}",
              help="Mendekati 1.0 = model sangat baik")

    # Parameter model terbaik
    st.markdown("#### Parameter Model Terbaik (GridSearchCV)")
    st.dataframe(pd.DataFrame({
        "No": [1, 2, 3, 4],
        "Parameter": [
            "n_estimators (jumlah pohon)",
            "max_depth (kedalaman pohon)",
            "min_samples_split",
            "min_samples_leaf"
        ],
        "Nilai Terbaik": [200, 10, 2, 1],
    }), use_container_width=True, hide_index=True)

    # Perbandingan baseline vs tuned
    st.markdown("#### Perbandingan Baseline vs Tuned")
    st.dataframe(pd.DataFrame({
        "No": [1, 2],
        "Model": [
            "Random Forest (Baseline)",
            "Random Forest (Tuned - GridSearchCV)"
        ],
        "MAE (hari)": [3.45, 3.29],
        "RMSE (hari)": [5.48, 5.12],
        "R2": [0.9969, 0.9973],
    }), use_container_width=True, hide_index=True)

    # 3. Visualisasi (Sebelumnya 4)
    st.divider()
    st.markdown("### 3. Visualisasi Hasil Prediksi")

    with st.expander("Grafik Aktual vs Prediksi", expanded=True):
        eval_df = pd.DataFrame({
            "Nama Santri":            df_raw["nama_santri"].values,
            "Nilai Aktual (Hari)":    y.values.round(0).astype(int),
            "Nilai Prediksi (Hari)":  np.round(y_pred).astype(int),
            "Selisih Error (Hari)":   np.round(np.abs(y.values - y_pred)).astype(int),
        })
        min_val = int(eval_df["Nilai Aktual (Hari)"].min())
        max_val = int(eval_df["Nilai Aktual (Hari)"].max())
        fig_scatter = px.scatter(
            eval_df,
            x="Nilai Aktual (Hari)", y="Nilai Prediksi (Hari)",
            hover_name="Nama Santri",
            title="Aktual vs Prediksi - Estimasi Hari Selesai",
            color_discrete_sequence=["#2B5748"],
        )
        fig_scatter.add_shape(
            type="line", x0=min_val, y0=min_val, x1=max_val, y1=max_val,
            line=dict(color="#618764", dash="dash", width=2),
        )
        fig_scatter.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>Aktual: %{x} Hari<br>Prediksi: %{y} Hari<extra></extra>",
            marker=dict(size=10, opacity=0.75),
        )
        fig_scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#273338"),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown("**Tabel Perbandingan Aktual vs Prediksi (10 Data Pertama)**")
        st.dataframe(eval_df.head(10), use_container_width=True, hide_index=True)

    with st.expander("Feature Importance - Tingkat Kepentingan Fitur"):
        fi     = pd.Series(model.feature_importances_, index=FITUR_INPUT).sort_values(ascending=True)
        fi_pct = (fi * 100).round(2)
        fig_fi = px.bar(
            fi_pct, x=fi_pct.values, y=fi_pct.index, orientation="h",
            title="Feature Importance - Random Forest",
            labels={"x": "Tingkat Kepentingan Fitur (%)", "y": "Fitur"},
            color_discrete_sequence=["#618764"],
            text_auto=".2f",
        )
        fig_fi.update_traces(
            hovertemplate="<b>%{y}</b><br>Kepentingan: %{x:.2f}%<extra></extra>",
            textposition="outside",
        )
        fig_fi.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#273338"),
        )
        st.plotly_chart(fig_fi, use_container_width=True)
        fi_sorted = fi.sort_values(ascending=False)
        st.dataframe(pd.DataFrame({
            "No": range(1, len(FITUR_INPUT) + 1),
            "Fitur": fi_sorted.index.tolist(),
            "Tingkat Kepentingan": [f"{v:.2f}%" for v in fi_sorted.values * 100],
        }), use_container_width=True, hide_index=True)

    with st.expander("Distribusi Residual (Error) Model"):
        residual = y.values - y_pred
        fig_res = px.histogram(
            x=residual, nbins=25,
            title="Distribusi Residual (Error) Model",
            labels={"x": "Residual (Aktual - Prediksi)", "y": "Count"},
            color_discrete_sequence=["#9CB080"],
        )
        fig_res.add_vline(x=0, line_color="#273338", line_dash="dash",
                          annotation_text="Residual = 0", annotation_position="top right")
        fig_res.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#273338"),
        )
        st.plotly_chart(fig_res, use_container_width=True)

    # 5. Semua Santri
    st.divider()
    st.markdown("### 5. Hasil Prediksi AI - Semua Santri")
    target_num = pd.to_numeric(df_raw["target_hafalan_ayat"], errors="coerce").fillna(1203)
    total_num  = pd.to_numeric(df_raw["total_hafalan"], errors="coerce").fillna(0)
    hasil_df = pd.DataFrame({
        "Nama Santri":          df_raw["nama_santri"].values,
        "Kelas":                df_raw["kelas"].values,
        "Total Hafalan (Ayat)": total_num.astype(int).values,
        "Target (Ayat)":        target_num.astype(int).values,
        "Sisa Hafalan (Ayat)":  (target_num - total_num).clip(lower=0).astype(int).values,
        "Rata-rata Nilai":      pd.to_numeric(df_raw["rata_nilai"], errors="coerce").fillna(0).round(1).values,
        "Estimasi AI (Hari)":   np.round(y_pred).astype(int),
    })
    fig_bar = px.bar(
        hasil_df.sort_values("Estimasi AI (Hari)"),
        x="Nama Santri", y="Estimasi AI (Hari)", color="Kelas",
        title="Estimasi Hari Selesai Hafalan per Santri (Prediksi AI)",
        labels={"Nama Santri": "Santri", "Estimasi AI (Hari)": "Estimasi (Hari)"},
        color_discrete_sequence=["#2B5748", "#618764", "#9CB080", "#273338"],
        text_auto=True,
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#273338"), xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.dataframe(hasil_df, use_container_width=True, hide_index=True)

    # 6. Simpan ke DB
    st.divider()
    if st.button("Simpan Hasil Prediksi AI ke Database", type="primary", use_container_width=True):
        with st.spinner("Menyimpan hasil prediksi ke database..."):
            for i, (_, row) in enumerate(df_raw.iterrows()):
                pred_val = max(1, int(round(float(y_pred[i]))))
                db.update_estimasi_selesai(int(row["id"]), pred_val)
                db.insert_prediksi_log(int(row["id"]), pred_val)
        st.success(f"**{len(df_raw)} santri** berhasil diprediksi dan disimpan ke database!")
        st.rerun()

    # 7. Log Prediksi
    st.divider()
    st.markdown("### Log Riwayat Prediksi Terbaru")
    log_df = db.get_prediksi_log()
    if not log_df.empty:
        st.dataframe(
            log_df.head(20)[["tanggal_prediksi", "nama_santri", "kelas", "estimasi_hari_prediksi"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.caption("Belum ada riwayat prediksi.")