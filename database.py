"""
database.py
============
FITUR: Koneksi & Query Database MySQL.

Semua modul mengambil data lewat fungsi ini.
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
import streamlit as st
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"❌ Gagal koneksi ke database MySQL: {e}")
        return None

def fetch_df(query: str, params: tuple = None) -> pd.DataFrame:
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
    conn = get_connection()
    if conn:
        conn.close()
        return True
    return False

# =====================================================================
# QUERY: SANTRI
# =====================================================================
def get_all_santri() -> pd.DataFrame:
    return fetch_df("SELECT * FROM santri ORDER BY nama_santri ASC")

def get_santri_by_id(santri_id: int) -> pd.DataFrame:
    return fetch_df("SELECT * FROM santri WHERE id = %s", (santri_id,))

def insert_santri(nis, nama, kelas, rata_jiyadah, frekuensi, total_hafalan, 
                  target_ayat, hafalan_surat, target_juz, rata_nilai, estimasi_hari=None):
    query = """
        INSERT INTO santri (nis, nama_santri, kelas, rata_jiyadah, frekuensi_minggu, 
                            total_hafalan, target_hafalan_ayat, hafalan_surat, 
                            target_hafalan_juz, rata_nilai, estimasi_hari_selesai)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_query(query, (nis, nama, kelas, rata_jiyadah, frekuensi, total_hafalan, 
                                 target_ayat, hafalan_surat, target_juz, rata_nilai, estimasi_hari))

def update_santri(santri_id, nis, nama, kelas, rata_jiyadah, frekuensi, total_hafalan, 
                  target_ayat, hafalan_surat, target_juz, rata_nilai, estimasi_hari=None):
    query = """
        UPDATE santri
        SET nis=%s, nama_santri=%s, kelas=%s,
            rata_jiyadah=%s, frekuensi_minggu=%s, total_hafalan=%s,
            target_hafalan_ayat=%s, hafalan_surat=%s, target_hafalan_juz=%s,
            rata_nilai=%s, estimasi_hari_selesai=%s
        WHERE id=%s
    """
    return execute_query(query, (nis, nama, kelas, rata_jiyadah, frekuensi, total_hafalan, 
                                 target_ayat, hafalan_surat, target_juz, rata_nilai, estimasi_hari, santri_id))

def update_estimasi_selesai(santri_id, estimasi_hari):
    query = "UPDATE santri SET estimasi_hari_selesai=%s WHERE id=%s"
    return execute_query(query, (int(estimasi_hari) if estimasi_hari else None, santri_id))

def delete_santri(santri_id):
    return execute_query("DELETE FROM santri WHERE id=%s", (santri_id,))

# =====================================================================
# QUERY: HAFALAN (OPERASIONAL HARIAN)
# =====================================================================
def insert_hafalan(santri_id, jenis_setoran, surah, jumlah_ayat, tanggal_setor, nilai_setoran, catatan):
    query = """
        INSERT INTO hafalan
        (santri_id, jenis_setoran, surah, jumlah_ayat, tanggal_setor, nilai_setoran, catatan)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """
    params = (santri_id, jenis_setoran, surah, jumlah_ayat, tanggal_setor, nilai_setoran, catatan)
    return execute_query(query, params)

def get_all_hafalan() -> pd.DataFrame:
    query = """
        SELECT h.*, s.nama_santri, s.kelas
        FROM hafalan h
        JOIN santri s ON h.santri_id = s.id
        ORDER BY h.tanggal_setor DESC, h.created_at DESC
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
# QUERY: AGREGASI UNTUK MACHINE LEARNING (RANDOM FOREST REGRESSOR)
# =====================================================================
def get_fitur_agregat_santri() -> pd.DataFrame:
    """
    Menggabungkan Modal Awal (tabel santri) dengan Riwayat Harian (tabel hafalan).
    - Jika santri melakukan Jiyadah -> total_hafalan bertambah.
    - Frekuensi dan Rata_jiyadah akan diupdate berdasarkan riwayat jika ada.
    - Rata_nilai dikombinasikan.
    """
    query = """
        SELECT 
            s.id,
            s.nis,
            s.nama_santri,
            s.kelas,
            
            -- Frekuensi: (Jika ada riwayat, pakai jumlah riwayat / 4 minggu, misal 1 bulan. Jika 0, pakai base Excel)
            COALESCE(
                IF(COUNT(h.id) > 0, CEIL(COUNT(h.id) / 4.0), s.frekuensi_minggu),
                s.frekuensi_minggu
            ) AS frekuensi_minggu,
            
            -- Rata Jiyadah: (Rata-rata jumlah_ayat khusus Jiyadah. Jika null, pakai base Excel)
            COALESCE(
                IF(SUM(CASE WHEN h.jenis_setoran = 'Jiyadah' THEN 1 ELSE 0 END) > 0,
                   AVG(CASE WHEN h.jenis_setoran = 'Jiyadah' THEN h.jumlah_ayat ELSE NULL END),
                   s.rata_jiyadah),
                s.rata_jiyadah
            ) AS rata_jiyadah,
            
            -- Total Hafalan: Base Excel + Total Jiyadah dari riwayat
            s.total_hafalan + COALESCE(SUM(CASE WHEN h.jenis_setoran = 'Jiyadah' THEN h.jumlah_ayat ELSE 0 END), 0) AS total_hafalan,
            
            -- Nilai: Rata-rata dari nilai riwayat, jika tidak ada pakai base Excel
            COALESCE(
                IF(COUNT(h.id) > 0, AVG(h.nilai_setoran), s.rata_nilai),
                s.rata_nilai
            ) AS rata_nilai,
            
            s.target_hafalan_ayat,
            s.target_hafalan_juz,
            s.estimasi_hari_selesai
        FROM santri s
        LEFT JOIN hafalan h ON s.id = h.santri_id
        GROUP BY s.id
    """
    return fetch_df(query)

# =====================================================================
# QUERY: PREDIKSI LOG
# =====================================================================
def insert_prediksi_log(santri_id, estimasi_hari):
    query = "INSERT INTO prediksi_log (santri_id, estimasi_hari_prediksi) VALUES (%s, %s)"
    return execute_query(query, (santri_id, int(estimasi_hari)))

def get_prediksi_log() -> pd.DataFrame:
    query = """
        SELECT p.*, s.nama_santri, s.kelas
        FROM prediksi_log p
        JOIN santri s ON p.santri_id = s.id
        ORDER BY p.tanggal_prediksi DESC
    """
    return fetch_df(query)

# =====================================================================
# QUERY: USERS
# =====================================================================
def get_user_by_username(username: str) -> pd.DataFrame:
    return fetch_df("SELECT * FROM users WHERE username = %s", (username,))

def get_all_users() -> pd.DataFrame:
    query = """
        SELECT u.id, u.username, u.role, u.nama_lengkap, u.kelas,
               u.santri_id, s.nama_santri AS nama_anak, u.created_at
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
