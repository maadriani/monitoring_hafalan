"""
database.py
============
FITUR: Koneksi & Query Database MySQL.

Semua modul lain (santri, hafalan, monitoring, prediksi, laporan)
mengambil/menyimpan data lewat fungsi-fungsi pada file ini, supaya
konfigurasi koneksi database hanya ada di SATU tempat.
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
import streamlit as st

# =====================================================================
# KONFIGURASI KONEKSI MYSQL
# Ubah sesuai environment Anda (atau set lewat st.secrets / .env)
# =====================================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "db_hafalan_quran",
}


def get_connection():
    """Membuka koneksi baru ke MySQL. Return None jika gagal."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"❌ Gagal koneksi ke database MySQL: {e}")
        return None


def fetch_df(query: str, params: tuple = None) -> pd.DataFrame:
    """Menjalankan SELECT dan mengembalikan hasil sebagai DataFrame."""
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"❌ Query gagal: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def execute_query(query: str, params: tuple = None) -> bool:
    """Menjalankan INSERT/UPDATE/DELETE. Return True jika sukses."""
    conn = get_connection()
    if conn is None:
        return False
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        conn.commit()
        return True
    except Error as e:
        st.error(f"❌ Query gagal: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def test_connection() -> bool:
    """Cek apakah koneksi database berhasil (dipakai di sidebar)."""
    conn = get_connection()
    if conn:
        conn.close()
        return True
    return False


# =====================================================================
# QUERY: SANTRI
# =====================================================================
def get_all_santri() -> pd.DataFrame:
    return fetch_df("SELECT * FROM santri ORDER BY nama ASC")


def get_santri_by_id(santri_id: int) -> pd.DataFrame:
    return fetch_df("SELECT * FROM santri WHERE id = %s", (santri_id,))


def insert_santri(nis, nama, jk, kelas, tgl_lahir, tgl_masuk):
    query = """
        INSERT INTO santri (nis, nama, jenis_kelamin, kelas, tanggal_lahir, tanggal_masuk)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_query(query, (nis, nama, jk, kelas, tgl_lahir, tgl_masuk))


def update_santri(santri_id, nis, nama, jk, kelas, tgl_lahir, tgl_masuk):
    query = """
        UPDATE santri
        SET nis=%s, nama=%s, jenis_kelamin=%s, kelas=%s,
            tanggal_lahir=%s, tanggal_masuk=%s
        WHERE id=%s
    """
    return execute_query(query, (nis, nama, jk, kelas, tgl_lahir, tgl_masuk, santri_id))


def update_kategori_hafalan(santri_id, kategori):
    query = "UPDATE santri SET kategori_hafalan=%s WHERE id=%s"
    return execute_query(query, (kategori, santri_id))


def delete_santri(santri_id):
    return execute_query("DELETE FROM santri WHERE id=%s", (santri_id,))


# =====================================================================
# QUERY: HAFALAN
# =====================================================================
def insert_hafalan(santri_id, surah, juz, ayat_mulai, ayat_selesai,
                    tanggal_setor, nilai_kelancaran, nilai_tajwid,
                    nilai_makhraj, durasi_menit, jumlah_kesalahan,
                    status_setoran, catatan):
    jumlah_ayat = max(int(ayat_selesai) - int(ayat_mulai) + 1, 0)
    query = """
        INSERT INTO hafalan
        (santri_id, surah, juz, ayat_mulai, ayat_selesai, jumlah_ayat,
         tanggal_setor, nilai_kelancaran, nilai_tajwid, nilai_makhraj,
         durasi_menit, jumlah_kesalahan, status_setoran, catatan)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    params = (santri_id, surah, juz, ayat_mulai, ayat_selesai, jumlah_ayat,
              tanggal_setor, nilai_kelancaran, nilai_tajwid, nilai_makhraj,
              durasi_menit, jumlah_kesalahan, status_setoran, catatan)
    return execute_query(query, params)


def get_all_hafalan() -> pd.DataFrame:
    query = """
        SELECT h.*, s.nama AS nama_santri, s.kelas
        FROM hafalan h
        JOIN santri s ON h.santri_id = s.id
        ORDER BY h.tanggal_setor DESC
    """
    return fetch_df(query)


def get_hafalan_by_santri(santri_id: int) -> pd.DataFrame:
    query = """
        SELECT * FROM hafalan
        WHERE santri_id = %s
        ORDER BY tanggal_setor ASC
    """
    return fetch_df(query, (santri_id,))


def delete_hafalan(hafalan_id):
    return execute_query("DELETE FROM hafalan WHERE id=%s", (hafalan_id,))


# =====================================================================
# QUERY: AGREGASI UNTUK MACHINE LEARNING (RANDOM FOREST)
# =====================================================================
def get_fitur_agregat_santri() -> pd.DataFrame:
    """
    Menghitung fitur agregat per santri dari riwayat hafalan:
    rata-rata nilai, jumlah setoran, rata-rata durasi & kesalahan, dll.
    Digabung dengan label kategori_hafalan (jika sudah diisi manual).
    """
    query = """
        SELECT
            s.id AS santri_id,
            s.nama,
            s.kelas,
            s.kategori_hafalan,
            COUNT(h.id) AS jumlah_setoran,
            COALESCE(AVG(h.nilai_kelancaran), 0) AS avg_kelancaran,
            COALESCE(AVG(h.nilai_tajwid), 0) AS avg_tajwid,
            COALESCE(AVG(h.nilai_makhraj), 0) AS avg_makhraj,
            COALESCE(AVG(h.durasi_menit), 0) AS avg_durasi,
            COALESCE(AVG(h.jumlah_kesalahan), 0) AS avg_kesalahan,
            COALESCE(SUM(h.jumlah_ayat), 0) AS total_ayat
        FROM santri s
        LEFT JOIN hafalan h ON s.id = h.santri_id
        GROUP BY s.id, s.nama, s.kelas, s.kategori_hafalan
    """
    return fetch_df(query)


# =====================================================================
# QUERY: PREDIKSI LOG
# =====================================================================
def insert_prediksi_log(santri_id, kategori_prediksi, probabilitas):
    query = """
        INSERT INTO prediksi_log (santri_id, kategori_prediksi, probabilitas)
        VALUES (%s, %s, %s)
    """
    return execute_query(query, (santri_id, kategori_prediksi, float(probabilitas)))


def get_prediksi_log() -> pd.DataFrame:
    query = """
        SELECT p.*, s.nama, s.kelas
        FROM prediksi_log p
        JOIN santri s ON p.santri_id = s.id
        ORDER BY p.tanggal_prediksi DESC
    """
    return fetch_df(query)


# =====================================================================
# QUERY: USERS (LOGIN & MANAJEMEN AKUN PER ROLE)
# =====================================================================
def get_user_by_username(username: str) -> pd.DataFrame:
    return fetch_df("SELECT * FROM users WHERE username = %s", (username,))


def get_all_users() -> pd.DataFrame:
    query = """
        SELECT u.id, u.username, u.role, u.nama_lengkap, u.kelas,
               u.santri_id, s.nama AS nama_anak, u.created_at
        FROM users u
        LEFT JOIN santri s ON u.santri_id = s.id
        ORDER BY u.role, u.nama_lengkap
    """
    return fetch_df(query)


def insert_user(username, password_hash, role, nama_lengkap, kelas=None, santri_id=None):
    query = """
        INSERT INTO users (username, password, role, nama_lengkap, kelas, santri_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_query(query, (username, password_hash, role, nama_lengkap, kelas, santri_id))


def update_user(user_id, nama_lengkap, role, kelas=None, santri_id=None):
    query = """
        UPDATE users
        SET nama_lengkap=%s, role=%s, kelas=%s, santri_id=%s
        WHERE id=%s
    """
    return execute_query(query, (nama_lengkap, role, kelas, santri_id, user_id))


def update_user_password(user_id, password_hash):
    return execute_query("UPDATE users SET password=%s WHERE id=%s", (password_hash, user_id))


def delete_user(user_id):
    return execute_query("DELETE FROM users WHERE id=%s", (user_id,))
