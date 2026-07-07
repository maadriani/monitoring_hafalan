"""
modules/prediksi.py
=====================
FITUR: Prediksi Kategori Hafalan Santri menggunakan Random Forest.

Cara kerja:
1. Fitur diambil dari agregasi riwayat hafalan tiap santri:
   jumlah_setoran, avg_kelancaran, avg_tajwid, avg_makhraj,
   avg_durasi, avg_kesalahan, total_ayat.
2. Label (target) = kolom santri.kategori_hafalan yang diisi MANUAL
   oleh ustadz/ustadzah (lihat menu Data Santri -> tab "Beri Label").
3. Model dilatih dari santri yang SUDAH berlabel, lalu dipakai untuk
   memprediksi kategori santri yang BELUM berlabel.
4. Tersedia juga simulasi prediksi manual (input nilai bebas).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

import database as db

FITUR_KOLOM = [
    "jumlah_setoran", "avg_kelancaran", "avg_tajwid",
    "avg_makhraj", "avg_durasi", "avg_kesalahan", "total_ayat",
]

MIN_SAMPLE_TRAINING = 4  # minimal jumlah santri berlabel agar model layak dilatih


def render():
    st.title("🌲 Prediksi Kategori Hafalan (Random Forest)")
    st.caption(
        "Model Random Forest memprediksi kategori hafalan santri "
        "(*Lancar / Cukup / Perlu Bimbingan*) berdasarkan riwayat penilaian setoran."
    )

    data = db.get_fitur_agregat_santri()
    if data.empty:
        st.warning("Belum ada data santri.")
        return

    berlabel = data[data["kategori_hafalan"].notna()].copy()
    belum_label = data[data["kategori_hafalan"].isna()].copy()

    st.info(
        f"📌 Data santri **berlabel** (untuk training): **{len(berlabel)}**  |  "
        f"Data santri **belum berlabel** (akan diprediksi): **{len(belum_label)}**"
    )

    if len(berlabel) < MIN_SAMPLE_TRAINING:
        st.error(
            f"Minimal {MIN_SAMPLE_TRAINING} santri perlu diberi label kategori hafalan "
            f"secara manual dahulu (menu **Data Santri** > tab **Edit/Hapus/Beri Label**) "
            f"sebelum model Random Forest bisa dilatih. Saat ini baru {len(berlabel)} santri berlabel."
        )
        return

    if berlabel["kategori_hafalan"].nunique() < 2:
        st.error("Minimal harus ada 2 kategori berbeda pada data berlabel agar model dapat dilatih.")
        return

    # ------------------------------------------------------------
    # TRAINING MODEL
    # ------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(
        ["🧠 Training & Evaluasi Model", "🔮 Prediksi Santri Belum Berlabel", "✍️ Simulasi Prediksi Manual"]
    )

    X = berlabel[FITUR_KOLOM]
    y_raw = berlabel["kategori_hafalan"]

    encoder = LabelEncoder()
    y = encoder.fit_transform(y_raw)

    test_size = 0.2 if len(berlabel) >= 15 else max(1 / len(berlabel), 0.15)

    with tab1:
        c1, c2 = st.columns(2)
        n_estimators = c1.slider("Jumlah Trees (n_estimators)", 50, 300, 100, step=50)
        max_depth = c2.slider("Kedalaman Maksimal (max_depth)", 2, 20, 6)

        if st.button("🚀 Latih Model Random Forest", type="primary"):
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42,
                stratify=y if min(pd.Series(y).value_counts()) > 1 else None,
            )

            model = RandomForestClassifier(
                n_estimators=n_estimators, max_depth=max_depth, random_state=42
            )
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            akurasi = accuracy_score(y_test, y_pred)

            st.session_state["rf_model"] = model
            st.session_state["rf_encoder"] = encoder

            st.success(f"✅ Model berhasil dilatih. Akurasi pada data uji: **{akurasi*100:.1f}%**")

            colx, coly = st.columns(2)
            with colx:
                st.markdown("##### Laporan Klasifikasi")
                report = classification_report(
                    y_test, y_pred, target_names=encoder.classes_,
                    output_dict=True, zero_division=0,
                )
                st.dataframe(pd.DataFrame(report).transpose().round(2), use_container_width=True)

            with coly:
                st.markdown("##### Confusion Matrix")
                cm = confusion_matrix(y_test, y_pred)
                fig_cm = px.imshow(
                    cm, text_auto=True, x=encoder.classes_, y=encoder.classes_,
                    labels=dict(x="Prediksi", y="Aktual"), color_continuous_scale="Blues",
                )
                st.plotly_chart(fig_cm, use_container_width=True)

            st.markdown("##### 📊 Feature Importance")
            importance = pd.DataFrame({
                "Fitur": FITUR_KOLOM,
                "Importance": model.feature_importances_,
            }).sort_values("Importance", ascending=False)
            fig_imp = px.bar(importance, x="Importance", y="Fitur", orientation="h")
            st.plotly_chart(fig_imp, use_container_width=True)

        elif "rf_model" in st.session_state:
            st.info("Model dari sesi sebelumnya masih aktif. Klik tombol di atas untuk melatih ulang.")

    # ------------------------------------------------------------
    # PREDIKSI SANTRI BELUM BERLABEL
    # ------------------------------------------------------------
    with tab2:
        if "rf_model" not in st.session_state:
            st.warning("Latih model terlebih dahulu di tab **Training & Evaluasi Model**.")
        elif belum_label.empty:
            st.success("🎉 Semua santri sudah memiliki label kategori hafalan.")
        else:
            model = st.session_state["rf_model"]
            encoder = st.session_state["rf_encoder"]

            X_baru = belum_label[FITUR_KOLOM]
            pred = model.predict(X_baru)
            proba = model.predict_proba(X_baru)

            hasil = belum_label[["santri_id", "nama", "kelas"]].copy()
            hasil["Prediksi Kategori"] = encoder.inverse_transform(pred)
            hasil["Probabilitas"] = proba.max(axis=1).round(3)

            st.dataframe(hasil, use_container_width=True, hide_index=True)

            if st.button("💾 Simpan Semua Hasil Prediksi ke Log"):
                for _, row in hasil.iterrows():
                    db.insert_prediksi_log(
                        row["santri_id"], row["Prediksi Kategori"], row["Probabilitas"]
                    )
                st.success("Hasil prediksi berhasil disimpan ke tabel prediksi_log.")

    # ------------------------------------------------------------
    # SIMULASI PREDIKSI MANUAL
    # ------------------------------------------------------------
    with tab3:
        if "rf_model" not in st.session_state:
            st.warning("Latih model terlebih dahulu di tab **Training & Evaluasi Model**.")
        else:
            st.caption("Masukkan nilai hipotetis untuk melihat prediksi kategori hafalan.")
            c1, c2 = st.columns(2)
            jumlah_setoran = c1.number_input("Jumlah Setoran", 0, 500, 20)
            avg_kelancaran = c2.slider("Rata-rata Kelancaran", 0, 100, 80)
            avg_tajwid = c1.slider("Rata-rata Tajwid", 0, 100, 80)
            avg_makhraj = c2.slider("Rata-rata Makhraj", 0, 100, 80)
            avg_durasi = c1.number_input("Rata-rata Durasi (menit)", 1, 120, 10)
            avg_kesalahan = c2.number_input("Rata-rata Jumlah Kesalahan", 0, 50, 2)
            total_ayat = c1.number_input("Total Ayat Dihafal", 0, 6236, 100)

            if st.button("🔮 Prediksi Sekarang", type="primary"):
                model = st.session_state["rf_model"]
                encoder = st.session_state["rf_encoder"]
                input_df = pd.DataFrame([{
                    "jumlah_setoran": jumlah_setoran,
                    "avg_kelancaran": avg_kelancaran,
                    "avg_tajwid": avg_tajwid,
                    "avg_makhraj": avg_makhraj,
                    "avg_durasi": avg_durasi,
                    "avg_kesalahan": avg_kesalahan,
                    "total_ayat": total_ayat,
                }])
                pred = model.predict(input_df)[0]
                proba = model.predict_proba(input_df)[0]
                kategori = encoder.inverse_transform([pred])[0]

                warna = {"Lancar": "success", "Cukup": "warning", "Perlu Bimbingan": "error"}
                getattr(st, warna.get(kategori, "info"))(
                    f"Hasil Prediksi: **{kategori}** (probabilitas: {proba.max()*100:.1f}%)"
                )

                proba_df = pd.DataFrame({"Kategori": encoder.classes_, "Probabilitas": proba})
                st.bar_chart(proba_df.set_index("Kategori"))

    # ------------------------------------------------------------
    # RIWAYAT LOG PREDIKSI
    # ------------------------------------------------------------
    st.divider()
    with st.expander("🗂️ Riwayat Log Prediksi Tersimpan"):
        log_df = db.get_prediksi_log()
        if log_df.empty:
            st.info("Belum ada log prediksi yang tersimpan.")
        else:
            st.dataframe(log_df, use_container_width=True, hide_index=True)
