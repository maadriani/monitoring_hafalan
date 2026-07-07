-- =====================================================================
-- SKEMA DATABASE: MONITORING HAFALAN AL-QUR'AN
-- =====================================================================
CREATE DATABASE IF NOT EXISTS db_hafalan_quran
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE db_hafalan_quran;

-- ---------------------------------------------------------------------
-- Tabel SANTRI
-- kategori_hafalan diisi MANUAL oleh ustadz/ustadzah secara berkala.
-- Kolom inilah yang menjadi LABEL/TARGET untuk training Random Forest.
-- Jika NULL, berarti santri belum dinilai/dikategorikan -> akan
-- diprediksi oleh model Random Forest pada fitur Prediksi.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS santri (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nis             VARCHAR(20)  UNIQUE,
    nama            VARCHAR(100) NOT NULL,
    jenis_kelamin   ENUM('Laki-laki','Perempuan') NOT NULL,
    kelas           VARCHAR(20),
    tanggal_lahir   DATE,
    tanggal_masuk   DATE,
    kategori_hafalan ENUM('Lancar','Cukup','Perlu Bimbingan') DEFAULT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabel HAFALAN (riwayat setoran hafalan)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hafalan (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    santri_id         INT NOT NULL,
    surah             VARCHAR(50) NOT NULL,
    juz               INT,
    ayat_mulai        INT,
    ayat_selesai      INT,
    jumlah_ayat       INT,
    tanggal_setor     DATE NOT NULL,
    nilai_kelancaran  INT CHECK (nilai_kelancaran BETWEEN 0 AND 100),
    nilai_tajwid      INT CHECK (nilai_tajwid BETWEEN 0 AND 100),
    nilai_makhraj     INT CHECK (nilai_makhraj BETWEEN 0 AND 100),
    durasi_menit      INT,
    jumlah_kesalahan  INT DEFAULT 0,
    status_setoran    ENUM('Lulus','Mengulang','Belum Lancar') DEFAULT 'Lulus',
    catatan           TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (santri_id) REFERENCES santri(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabel PREDIKSI_LOG (riwayat hasil prediksi Random Forest)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prediksi_log (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    santri_id         INT NOT NULL,
    tanggal_prediksi  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kategori_prediksi VARCHAR(50),
    probabilitas      FLOAT,
    FOREIGN KEY (santri_id) REFERENCES santri(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabel USERS (akun login: admin, wali_kelas, wali_santri)
--
-- role        : 'admin' | 'wali_kelas' | 'wali_santri'
-- kelas       : diisi HANYA untuk role wali_kelas -> kelas yang diampu
--               (harus sama persis dengan isi kolom santri.kelas, mis. "7A")
-- santri_id   : diisi HANYA untuk role wali_santri -> terhubung ke 1 anak
-- password    : disimpan dalam bentuk HASH (bcrypt), JANGAN plain text
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password      VARCHAR(255) NOT NULL,
    role          ENUM('admin','wali_kelas','wali_santri') NOT NULL,
    nama_lengkap  VARCHAR(100) NOT NULL,
    kelas         VARCHAR(20)  DEFAULT NULL,
    santri_id     INT          DEFAULT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (santri_id) REFERENCES santri(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Contoh data (opsional, boleh dihapus)
-- ---------------------------------------------------------------------
INSERT INTO santri (nis, nama, jenis_kelamin, kelas, tanggal_lahir, tanggal_masuk, kategori_hafalan) VALUES
('S001','Ahmad Fauzi','Laki-laki','7A','2012-03-10','2023-07-01','Lancar'),
('S002','Siti Aisyah','Perempuan','7A','2012-05-22','2023-07-01','Cukup'),
('S003','Muhammad Rizki','Laki-laki','7B','2012-01-15','2023-07-01','Perlu Bimbingan'),
('S004','Khadijah Putri','Perempuan','7B','2012-08-09','2023-07-01','Lancar'),
('S005','Umar Abdullah','Laki-laki','8A','2011-11-30','2022-07-01',NULL);

-- ---------------------------------------------------------------------
-- Contoh akun login (password di bawah sudah di-hash dengan bcrypt)
--   - admin       / admin123
--   - bu_guru7a   / walikelas123   (wali kelas 7A)
--   - ortu_ahmad  / walisantri123  (wali santri, anak = Ahmad Fauzi / id 1)
-- ⚠️ SEGERA GANTI PASSWORD INI SETELAH LOGIN PERTAMA KALI!
-- ---------------------------------------------------------------------
INSERT INTO users (username, password, role, nama_lengkap, kelas, santri_id) VALUES
('admin', '$2b$12$Fzo4zwS9T1ePvKtL417Dle9TBJm879KPqNcLKsSf9439oxrb.Tbyu', 'admin', 'Administrator', NULL, NULL),
('bu_guru7a', '$2b$12$ybJGlBroGuWGReGtfxsy3.3qIbCCEsWGLz6Wvg7xR1/wK6m2BNxve', 'wali_kelas', 'Ustadzah Fatimah', '7A', NULL),
('ortu_ahmad', '$2b$12$C4UIXOPi7sST6lO8vjhhzOvNVaPu6Mo9zI3d5nG29PoDbdMc0EEVq', 'wali_santri', 'Bapak Slamet', NULL, 1);
