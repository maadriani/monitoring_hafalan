-- =====================================================================
-- SKEMA DATABASE: MONITORING HAFALAN AL-QUR'AN (HYBRID ARCHITECTURE)
-- =====================================================================
CREATE DATABASE IF NOT EXISTS db_hafalan_quran
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE db_hafalan_quran;

-- ---------------------------------------------------------------------
-- Tabel SANTRI (Sebagai Modal Awal / Profil Dataset)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS santri (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nis             VARCHAR(20) UNIQUE,
    nama_santri     VARCHAR(100) NOT NULL,
    kelas           VARCHAR(20),
    rata_jiyadah    INT DEFAULT 5,
    frekuensi_minggu INT DEFAULT 5,
    total_hafalan   INT DEFAULT 0,
    target_hafalan_ayat INT DEFAULT 0,
    hafalan_surat   VARCHAR(100) DEFAULT '',
    target_hafalan_juz INT DEFAULT 30,
    rata_nilai      INT DEFAULT 0,
    estimasi_hari_selesai INT DEFAULT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabel HAFALAN (Riwayat Operasional Harian)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hafalan (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    santri_id         INT NOT NULL,
    jenis_setoran     ENUM('Jiyadah', 'Murojaah') NOT NULL DEFAULT 'Jiyadah',
    surah             VARCHAR(50) NOT NULL,
    jumlah_ayat       INT NOT NULL,
    tanggal_setor     DATE NOT NULL,
    nilai_setoran     INT CHECK (nilai_setoran BETWEEN 0 AND 100),
    catatan           TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (santri_id) REFERENCES santri(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabel PREDIKSI_LOG (riwayat hasil prediksi Random Forest Regressor)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prediksi_log (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    santri_id         INT NOT NULL,
    tanggal_prediksi  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimasi_hari_prediksi INT,
    FOREIGN KEY (santri_id) REFERENCES santri(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabel USERS (akun login: admin, wali_kelas, wali_santri)
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
-- Contoh akun login
-- ---------------------------------------------------------------------
INSERT INTO users (username, password, role, nama_lengkap, kelas, santri_id) VALUES
('admin', '$2b$12$Fzo4zwS9T1ePvKtL417Dle9TBJm879KPqNcLKsSf9439oxrb.Tbyu', 'admin', 'Administrator', NULL, NULL),
('bu_guru', '$2b$12$ybJGlBroGuWGReGtfxsy3.3qIbCCEsWGLz6Wvg7xR1/wK6m2BNxve', 'wali_kelas', 'Ustadzah Fatimah', '1', NULL);
