"""
modules/laporan.py
====================
FITUR: Laporan & Ekspor Data (Pure Dataset + Prediksi).
"""

import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

import database as db

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan Santri")
    return output.getvalue()

def to_pdf_bytes(df: pd.DataFrame) -> bytes:
    pdf = FPDF(orientation="L", format="A4")
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Laporan Data Hafalan Santri", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 10)
    cols = ["NIS", "Nama Santri", "Kelas", "Target (Ayat)", "Tercapai", "Nilai", "Estimasi (Hari)"]
    col_widths = [25, 75, 20, 30, 30, 25, 45]
    
    # Print Headers
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 10, col, border=1, align="C")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 10)
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, str(row.get("nis", "")), border=1)
        
        # Potong nama jika terlalu panjang
        nama = str(row.get("nama_santri", ""))
        if len(nama) > 35:
            nama = nama[:32] + "..."
            
        pdf.cell(col_widths[1], 10, nama, border=1)
        pdf.cell(col_widths[2], 10, str(row.get("kelas", "")), border=1, align="C")
        pdf.cell(col_widths[3], 10, str(row.get("target_hafalan_ayat", "")), border=1, align="C")
        pdf.cell(col_widths[4], 10, str(row.get("total_hafalan", "")), border=1, align="C")
        pdf.cell(col_widths[5], 10, str(round(float(row.get("rata_nilai", 0)), 1)), border=1, align="C")
        
        estimasi = row.get("estimasi_hari_selesai", "")
        pdf.cell(col_widths[6], 10, f"{estimasi} Hari" if pd.notna(estimasi) else "-", border=1, align="C")
        pdf.ln(10)
        
    return bytes(pdf.output())

def render(scope_kelas: str = None, locked_santri_id: int = None):
    st.title("🧾 Laporan Data & Prediksi Santri")

    df = db.get_all_santri()
    if df.empty:
        st.info("Belum ada data.")
        return

    if scope_kelas:
        df = df[df["kelas"] == scope_kelas]
    if locked_santri_id is not None:
        df = df[df["id"] == locked_santri_id]
        if df.empty:
            st.info("Data anak Anda belum terdaftar.")
            return

    if locked_santri_id is not None:
        kelas_filter = "Semua"
    else:
        kelas_opsi = ["Semua"] + sorted(df["kelas"].dropna().unique().tolist())
        kelas_filter = st.selectbox("Filter Kelas", kelas_opsi)

    hasil = df.copy()
    if kelas_filter != "Semua":
        hasil = hasil[hasil["kelas"] == kelas_filter]

    st.subheader(f"Hasil: {len(hasil)} santri")

    if hasil.empty:
        st.warning("Tidak ada data pada filter ini.")
        return

    kolom_tampil = [
        "nis", "nama_santri", "kelas", "rata_jiyadah", "frekuensi_minggu",
        "total_hafalan", "target_hafalan_ayat", "hafalan_surat", "target_hafalan_juz",
        "rata_nilai", "estimasi_hari_selesai"
    ]
    st.dataframe(hasil[kolom_tampil], use_container_width=True, hide_index=True)

    st.markdown("##### 📌 Ringkasan Statistik")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Santri", len(hasil))
    col2.metric("Rata-rata Nilai Global", round(hasil["rata_nilai"].mean(), 1))
    col3.metric("Total Ayat Dihafal (Kolektif)", int(hasil["total_hafalan"].sum()))

    st.divider()
    st.markdown("##### ⬇️ Unduh Laporan")
    colx, coly, colz = st.columns(3)
    with colx:
        csv = hasil[kolom_tampil].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV", data=csv,
            file_name=f"laporan_dataset_santri.csv",
            mime="text/csv", use_container_width=True,
        )
    with coly:
        excel_bytes = to_excel_bytes(hasil[kolom_tampil])
        st.download_button(
            "⬇️ Download Excel", data=excel_bytes,
            file_name=f"laporan_dataset_santri.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with colz:
        try:
            pdf_bytes = to_pdf_bytes(hasil)
            st.download_button(
                "⬇️ Download PDF", data=pdf_bytes,
                file_name=f"laporan_dataset_santri.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Gagal generate PDF: {e}")
