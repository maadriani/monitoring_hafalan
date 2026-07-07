# 📖 Aplikasi Monitoring Hafalan Al-Qur'an

Aplikasi web untuk memantau perkembangan hafalan Al-Qur'an santri, dibangun dengan
**Streamlit (Python)**, **MySQL**, dan fitur **Random Forest** (scikit-learn) untuk
memprediksi kategori hafalan santri.

---

## 🗂️ Struktur Project

```
hafalan-quran-app/
├── app.py                  # Entry point Streamlit (routing antar fitur)
├── database.py             # Koneksi & semua query ke MySQL
├── schema.sql               # Skema database MySQL (jalankan ini dulu)
├── requirements.txt
├── README.md
└── modules/
    ├── dashboard.py         # FITUR: Dashboard/KPI
    ├── santri.py            # FITUR: CRUD Data Santri + label kategori
    ├── hafalan.py            # FITUR: Input & riwayat setoran hafalan
    ├── monitoring.py         # FITUR: Monitoring progres per santri
    ├── prediksi.py            # FITUR: Prediksi Random Forest
    └── laporan.py             # FITUR: Laporan & ekspor CSV/Excel
```

Setiap fitur sengaja dipisah menjadi 1 file Python tersendiri di folder `modules/`
agar mudah dibaca, dikembangkan, atau diganti satu per satu.

---

## ⚙️ 1. Instalasi

```bash
# 1) Buat virtual environment (opsional tapi disarankan)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2) Install dependencies
pip install -r requirements.txt
```

## 🗄️ 2. Setup Database MySQL

1. Pastikan MySQL Server sudah berjalan di komputer/server Anda.
2. Import skema database:

```bash
mysql -u root -p < schema.sql
```

Ini akan membuat database `db_hafalan_quran` beserta tabel:
- `santri` — data santri + kolom `kategori_hafalan` (label manual)
- `hafalan` — riwayat setoran hafalan
- `prediksi_log` — riwayat hasil prediksi Random Forest

3. Sesuaikan kredensial koneksi di `database.py`:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "PASSWORD_ANDA",
    "database": "db_hafalan_quran",
}
```

> 💡 Untuk produksi, sebaiknya simpan kredensial di `st.secrets` (`.streamlit/secrets.toml`)
> daripada hardcode di file Python.

## ▶️ 3. Menjalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan terbuka otomatis di browser pada `http://localhost:8501`.

---

## 🔐 Sistem Login & 3 Role Pengguna

Aplikasi ini punya 3 jenis akun dengan hak akses berbeda:

| Role | Bisa Akses | Tidak Bisa |
|---|---|---|
| **🛡️ Admin** | Semua fitur, semua kelas, kelola pengguna, training Random Forest | - |
| **👨‍🏫 Wali Kelas** | Dashboard/Data Santri/Input Hafalan/Monitoring/Laporan — **hanya untuk kelas yang diampu** | Hapus santri, akses kelas lain, training Random Forest, kelola pengguna |
| **👪 Wali Santri** | Monitoring Progress & Laporan — **hanya untuk anaknya sendiri** (read-only) | Semua fitur input/edit, lihat data santri lain |

### Akun contoh (bawaan demo di `schema.sql`)

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |
| `bu_guru7a` | `walikelas123` | Wali Kelas (kelas 7A) |
| `ortu_ahmad` | `walisantri123` | Wali Santri (anak: Ahmad Fauzi) |

> ⚠️ **Segera ganti password akun-akun ini** setelah login pertama kali, lewat menu
> **🔐 Kelola Pengguna** (hanya admin yang bisa akses menu ini).

### Cara menambah pengguna baru

1. Login sebagai **admin**
2. Buka menu **🔐 Kelola Pengguna** → tab **➕ Tambah Pengguna**
3. Pilih role:
   - **Wali Kelas** → isi kolom **Kelas yang Diampu** (harus sama persis dengan isi kolom
     `kelas` di tabel santri, contoh: `7A`, `8B`, dst — perhatikan huruf besar/kecil)
   - **Wali Santri** → pilih nama anak dari dropdown (data diambil dari tabel `santri`)
4. Klik **Simpan Pengguna**

### Catatan teknis keamanan

- Password disimpan dalam bentuk **hash bcrypt**, tidak pernah plain text (lihat `auth.py`).
- Filter data per role dilakukan di level aplikasi (`app.py` meneruskan `scope_kelas` /
  `locked_santri_id` ke setiap modul) — pastikan kolom `kelas` di tabel `santri` konsisten
  penulisannya dengan kolom `kelas` di tabel `users` agar Wali Kelas melihat data yang benar.

---



| Fitur | File | Deskripsi |
|---|---|---|
| **Login & Role** | `auth.py`, `modules/users.py` | Login 3 role, dan **Kelola Pengguna** (khusus admin): tambah/edit/reset password/hapus akun |
| **Dashboard** | `modules/dashboard.py` | KPI total santri, setoran bulan ini, rata-rata nilai, distribusi kategori, top 5 santri, tren setoran |
| **Data Santri** | `modules/santri.py` | Tambah/Edit/Hapus data santri, serta **input label kategori hafalan manual** (Lancar/Cukup/Perlu Bimbingan) |
| **Input Hafalan** | `modules/hafalan.py` | Form input setoran (surah, juz, ayat, nilai kelancaran/tajwid/makhraj, durasi, kesalahan), serta riwayat setoran |
| **Monitoring Progress** | `modules/monitoring.py` | Grafik perkembangan nilai per santri, progres jumlah ayat dihafal terhadap total Al-Qur'an (6.236 ayat) |
| **Prediksi (Random Forest)** | `modules/prediksi.py` | Training model Random Forest dari data santri yang sudah berlabel, evaluasi (akurasi, confusion matrix, feature importance), prediksi santri belum berlabel, dan simulasi input manual |
| **Laporan** | `modules/laporan.py` | Filter laporan berdasarkan tanggal & kelas, ekspor ke CSV/Excel |

---

## 🌲 Cara Kerja Fitur Random Forest

1. **Label/target** kategori hafalan (`Lancar` / `Cukup` / `Perlu Bimbingan`) diisi
   **manual** oleh ustadz/ustadzah lewat menu **Data Santri → tab "Edit/Hapus/Beri Label"**.
   Ini wajib dilakukan untuk minimal **6 santri** dengan minimal **2 kategori berbeda**
   sebelum model bisa dilatih.
2. **Fitur input model** dihitung otomatis dari agregasi riwayat hafalan tiap santri:
   - `jumlah_setoran`
   - `avg_kelancaran`, `avg_tajwid`, `avg_makhraj`
   - `avg_durasi`, `avg_kesalahan`
   - `total_ayat`
3. Pada menu **Prediksi**:
   - Tab **Training & Evaluasi**: melatih `RandomForestClassifier`, menampilkan akurasi,
     classification report, confusion matrix, dan feature importance.
   - Tab **Prediksi Santri Belum Berlabel**: memprediksi kategori santri yang belum
     diberi label manual, hasil bisa disimpan ke tabel `prediksi_log`.
   - Tab **Simulasi Prediksi Manual**: mencoba input nilai bebas untuk melihat hasil
     prediksi model secara langsung.

---

## 📌 Catatan

- Skala nilai (kelancaran, tajwid, makhraj) menggunakan rentang **0–100**.
- Total ayat Al-Qur'an yang digunakan untuk hitung progres: **6.236 ayat**.
- Library wajib: `streamlit`, `mysql-connector-python`, `pandas`, `numpy`,
  `scikit-learn`, `plotly`, `openpyxl` (lihat `requirements.txt`).
