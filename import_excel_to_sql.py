import pandas as pd
import sys
import database as db

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("Mulai proses migrasi data dari Excel ke SQL (Format Dataset Murni)...")
    
    try:
        df = pd.read_excel('data hafalan santri.xlsx', skiprows=1)
    except Exception as e:
        print(f"❌ Gagal membaca file Excel: {e}")
        sys.exit(1)
        
    print(f"✅ File Excel berhasil dibaca. Ditemukan {len(df)} baris data.")
    
    success_count = 0
    
    for index, row in df.iterrows():
        nama = row.get('Nama Santri')
        if pd.isna(nama): continue
            
        kelas = str(row.get('Kelas\n(MTs)', ''))
        
        jiyadah_val = row.get('Rata-rata\nJiyadah/Hari\n(Ayat)')
        jiyadah = int(jiyadah_val) if not pd.isna(jiyadah_val) else 5
        
        frek_val = row.get('Frekuensi\nSetoran/\nMinggu')
        frekuensi = int(frek_val) if not pd.isna(frek_val) else 5
        
        tot_val = row.get('Total Hafalan\nSaat Ini\n(Ayat)')
        total_ayat = int(tot_val) if not pd.isna(tot_val) else 0
        
        target_ayat_val = row.get('Target Hafalan (Ayat) ')
        target_ayat = int(target_ayat_val) if not pd.isna(target_ayat_val) else 0
        
        target_surah_val = row.get('Hafalan\n(Surat)')
        target_surah = str(target_surah_val) if not pd.isna(target_surah_val) else ''
        
        target_juz_val = row.get('Target\nHafalan\n(Juz)')
        target_juz = int(target_juz_val) if not pd.isna(target_juz_val) else 30
        
        nilai_val = row.get('Rata-rata\nNilai Setoran')
        nilai = int(nilai_val) if not pd.isna(nilai_val) else 80
        
        estimasi_hari = row.get('Estimasi Hari\nSelesai\n(Label/Output)')
        
        nis = f"MIG-{index+1000}"
        
        db.insert_santri(
            nis=nis, 
            nama=nama, 
            kelas=kelas, 
            rata_jiyadah=jiyadah, 
            frekuensi=frekuensi, 
            total_hafalan=total_ayat, 
            target_ayat=target_ayat, 
            hafalan_surat=target_surah, 
            target_juz=target_juz,
            rata_nilai=nilai,
            estimasi_hari=int(estimasi_hari) if not pd.isna(estimasi_hari) else None
        )
        
        success_count += 1
        
    print(f"\n🎉 Migrasi Selesai! Total baris dataset berhasil dimasukkan ke sistem baru: {success_count}")

if __name__ == '__main__':
    main()
