import pandas as pd
import math
from datetime import datetime, timedelta
import random
import sys

# Mengambil koneksi dan fungsi database dari modul aplikasi yang sudah ada
import database as db

def main():
    print("Mulai proses migrasi dan translasi data dari Excel ke SQL...")
    
    # 1. Load data
    try:
        # skiprows=1 karena judul tabel ada di baris 0, header asli ada di baris 1
        df = pd.read_excel('data hafalan santri.xlsx', skiprows=1)
    except Exception as e:
        print(f"❌ Gagal membaca file Excel: {e}")
        sys.exit(1)
        
    print(f"✅ File Excel berhasil dibaca. Ditemukan {len(df)} baris data.")
    success_count = 0
    
    for index, row in df.iterrows():
        nama = row.get('Nama Santri')
        # Skip jika baris kosong / tidak ada nama santri
        if pd.isna(nama):
            continue
            
        kelas = row.get('Kelas\n(MTs)', 'Tidak Diketahui')
        estimasi_hari = row.get('Estimasi Hari\nSelesai\n(Label/Output)')
        
        # 2. Translasi Kategori Hafalan (Berdasarkan Estimasi Hari)
        kategori = None
        if not pd.isna(estimasi_hari):
            try:
                hari = float(estimasi_hari)
                if hari < 100:
                    kategori = 'Lancar'
                elif hari <= 300:
                    kategori = 'Cukup'
                else:
                    kategori = 'Perlu Bimbingan'
            except ValueError:
                pass
                
        # 3. Generate Data Santri
        nis = f"MIG-{index+1000}"  # NIS dummy untuk data migrasi
        tgl_masuk = "2023-07-01"
        tgl_lahir = "2010-01-01"
        
        # Insert Santri
        db.insert_santri(nis, nama, 'Laki-laki', str(kelas), tgl_lahir, tgl_masuk)
        
        # Ambil ID Santri yang baru saja di-insert
        santri_df = db.fetch_df("SELECT id FROM santri WHERE nis=%s", (nis,))
        if santri_df.empty:
            print(f"❌ Gagal insert santri: {nama}")
            continue
            
        santri_id = santri_df.iloc[0]['id']
        
        # Update kategori hafalan
        if kategori:
            db.update_kategori_hafalan(santri_id, kategori)
            
        # 4. Translasi Data Hafalan
        frekuensi_minggu = row.get('Frekuensi\nSetoran/\nMinggu', 1)
        if pd.isna(frekuensi_minggu) or frekuensi_minggu <= 0:
            frekuensi_minggu = 1
            
        total_ayat = row.get('Total Hafalan\nSaat Ini\n(Ayat)', 10)
        if pd.isna(total_ayat) or total_ayat <= 0:
            total_ayat = 10
            
        rata_nilai = row.get('Rata-rata\nNilai Setoran', 80)
        if pd.isna(rata_nilai):
            rata_nilai = 80
            
        # Asumsi mensimulasikan data selama 1 bulan (4 minggu)
        n_setoran = int(frekuensi_minggu * 4)
        if n_setoran == 0:
            n_setoran = 1
            
        ayat_per_setoran = max(1, int(total_ayat / n_setoran))
        
        base_date = datetime.now() - timedelta(days=30)
        
        # Loop untuk insert riwayat setoran hafalan buatan (translasi)
        for i in range(n_setoran):
            # Sebarkan tanggal setoran dalam 30 hari terakhir
            days_add = int(30/n_setoran) * i
            tgl_setor = (base_date + timedelta(days=days_add)).strftime('%Y-%m-%d')
            
            # Nilai disamakan semua sesuai dengan 'rata_nilai' dari Excel
            db.insert_hafalan(
                santri_id=int(santri_id),
                surah='Surah Migrasi',
                juz=30,
                ayat_mulai=1,
                ayat_selesai=int(ayat_per_setoran),
                tanggal_setor=tgl_setor,
                nilai_kelancaran=int(rata_nilai),
                nilai_tajwid=int(rata_nilai),
                nilai_makhraj=int(rata_nilai),
                durasi_menit=10,  # Nilai default rata-rata
                jumlah_kesalahan=2, # Nilai default rata-rata
                status_setoran='Lulus',
                catatan='Data translasi dari Excel'
            )
            
        success_count += 1
        print(f"✅ Berhasil migrasi {nama} ({n_setoran} riwayat setoran). Kategori: {kategori}")
        
    print(f"\n🎉 Migrasi Selesai! Total santri berhasil: {success_count}")

if __name__ == '__main__':
    main()
