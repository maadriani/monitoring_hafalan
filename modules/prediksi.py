"""
modules/prediksi.py
=====================
FITUR: Prediksi Estimasi Hari Selesai Hafalan Santri menggunakan Random Forest Regressor.
"""

import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import plotly.express as px
import numpy as np

import database as db

def render():
    st.title("🌲 Model AI (Random Forest Regressor)")
    st.caption("Latih model dan prediksi estimasi hari selesai hafalan santri secara otomatis.")

    # Ambil data dari tabel santri
    df_raw = db.get_fitur_agregat_santri()

    if df_raw.empty or len(df_raw) < 10:
        st.warning("Data santri belum cukup untuk melatih model AI. Minimal butuh 10 data.")
        return

    st.markdown("### 1. Data Dataset (Preview)")
    st.dataframe(df_raw.head(5), use_container_width=True)

    # ---------------------------------------------------------
    # PREPROCESSING DATA
    # ---------------------------------------------------------
    df = df_raw.copy()
    
    # Fitur X dan Target Y
    X_cols = [
        "rata_jiyadah", 
        "frekuensi_minggu", 
        "total_hafalan", 
        "target_hafalan_ayat",
        "target_hafalan_juz",
        "rata_nilai"
    ]
    
    # Kita buat dummy untuk categorical jika diperlukan, tapi fitur numerik utama sudah cukup
    # Encode kelas (opsional)
    df["kelas_encoded"] = df["kelas"].astype("category").cat.codes
    X_cols.append("kelas_encoded")
    
    # Cek nilai kosong
    for col in X_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Pisahkan data yang sudah punya label dan yang belum
    df_labeled = df.dropna(subset=["estimasi_hari_selesai"]).copy()
    df_unlabeled = df[df["estimasi_hari_selesai"].isna()].copy()

    if len(df_labeled) < 5:
        st.error("Data berlabel (Estimasi Hari Selesai) kurang dari 5. Tidak bisa melatih model.")
        return

    st.markdown(f"**Total Data Training:** {len(df_labeled)} baris | **Data Menunggu Prediksi:** {len(df_unlabeled)} baris")

    # ---------------------------------------------------------
    # TRAINING MODEL
    # ---------------------------------------------------------
    X = df_labeled[X_cols]
    y = df_labeled["estimasi_hari_selesai"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    y_pred = rf_model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    st.markdown("### 2. Evaluasi Model AI")
    col1, col2, col3 = st.columns(3)
    col1.metric("📉 Mean Absolute Error (MAE)", f"{mae:.2f} Hari")
    col2.metric("📉 Root Mean Squared Error (RMSE)", f"{rmse:.2f} Hari")
    col3.metric("📊 R² Score (Akurasi Regresi)", f"{r2:.2f}")

    with st.expander("Lihat Detail & Grafik Evaluasi"):
        eval_df = pd.DataFrame({"Data Aktual (Hari)": y_test, "Prediksi (Hari)": y_pred})
        fig = px.scatter(
            eval_df, x="Data Aktual (Hari)", y="Prediksi (Hari)", 
            title="Akurasi Tebakan AI (Aktual vs Prediksi)",
            labels={"Data Aktual (Hari)": "Hari Seharusnya (Kenyataan)", "Prediksi (Hari)": "Tebakan AI (Prediksi)"},
            color_discrete_sequence=["#2B5748"],
        )
        fig.update_traces(
            hovertemplate="<b>Kenyataan: %{x} Hari</b><br>AI Menebak: %{y} Hari<extra></extra>",
            marker=dict(size=10, opacity=0.7)
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#273338")
        )
        st.plotly_chart(fig, use_container_width=True)

        feature_imp = pd.Series(rf_model.feature_importances_, index=X_cols).sort_values(ascending=True)
        # Ubah nama kolom agar lebih enak dibaca awam
        nama_ramah = {
            "rata_jiyadah": "Kecepatan Hafal (Jiyadah)",
            "frekuensi_minggu": "Rajin Setoran (Frekuensi)",
            "total_hafalan": "Total Ayat Dihafal",
            "target_hafalan_ayat": "Target Ayat",
            "target_hafalan_juz": "Target Juz",
            "rata_nilai": "Kualitas Hafalan (Nilai)"
        }
        feature_imp.index = [nama_ramah.get(i, i) for i in feature_imp.index]

        fig_imp = px.bar(
            feature_imp, x=feature_imp.values, y=feature_imp.index, orientation='h',
            title="Faktor Apa Saja yang Paling Mempengaruhi Cepat/Lambatnya Anak Khatam?",
            labels={"x": "Persentase Pengaruh (0 - 1)", "y": "Faktor / Fitur"},
            color_discrete_sequence=["#618764"],
        )
        fig_imp.update_traces(
            hovertemplate="<b>Faktor: %{y}</b><br>Tingkat Pengaruh: %{x:.2f}<extra></extra>"
        )
        fig_imp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#273338")
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    # ---------------------------------------------------------
    # PREDIKSI MASSAL (AUTO-FILL)
    # ---------------------------------------------------------
    st.markdown("### 3. Prediksi Estimasi untuk Data Baru")
    if not df_unlabeled.empty:
        st.info(f"Ada {len(df_unlabeled)} santri yang kolom 'Estimasi Hari Selesai'-nya masih kosong.")
        if st.button("🚀 Prediksi Sekarang & Simpan", type="primary"):
            X_new = df_unlabeled[X_cols]
            pred_new = rf_model.predict(X_new)
            
            # Simpan ke DB
            with st.spinner("Menyimpan hasil prediksi ke database..."):
                for idx, row in df_unlabeled.iterrows():
                    santri_id = row["id"]
                    pred_val = int(pred_new[df_unlabeled.index.get_loc(idx)])
                    db.update_estimasi_selesai(santri_id, pred_val)
                    db.insert_prediksi_log(santri_id, pred_val)
                    
            st.success("Semua data berhasil diprediksi dan disimpan!")
            st.rerun()
    else:
        st.success("✨ Semua data santri saat ini sudah memiliki nilai Prediksi Estimasi Khatam.")

    st.divider()
    st.markdown("### 📜 Log / Riwayat Prediksi Terbaru")
    log_df = db.get_prediksi_log()
    if not log_df.empty:
        st.dataframe(log_df.head(20)[["tanggal_prediksi", "nama_santri", "kelas", "estimasi_hari_prediksi"]],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("Belum ada riwayat prediksi.")
