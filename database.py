# database.py
import mysql.connector
from datetime import datetime
import config

def simpan_ke_database(suhu, kelembapan_udara, co2):
    try:
        db = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        cursor = db.cursor()

        sql = """INSERT INTO tb_sensor 
                 (suhu, kelembapan_udara, kadar_co2) 
                 VALUES (%s, %s, %s)"""
        val = (suhu, kelembapan_udara, co2)
        
        cursor.execute(sql, val)
        db.commit()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [DB] Data Sensor tersimpan.")
        
    except mysql.connector.Error as err:
        print(f"[ERROR DB] Gagal menyimpan: {err}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()

def simpan_aktuator_ke_database(kipas_pwm, mist_maker, lampu_pemanas):
    try:
        db = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        cursor = db.cursor()

        sql = """INSERT INTO tb_aktuator 
                 (kipas_exhaust, mist_maker, lampu_pemanas) 
                 VALUES (%s, %s, %s)"""
                 
        # Konversi kipas_pwm ke string (jika diperlukan) agar konsisten
        # berdasarkan gambar db, sepertinya kolom berjenis varchar/string
        val = (str(kipas_pwm), mist_maker, lampu_pemanas)
        
        cursor.execute(sql, val)
        db.commit()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [DB] Data Aktuator tersimpan.")
        
    except mysql.connector.Error as err:
        print(f"[ERROR DB] Gagal menyimpan Aktuator: {err}")
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()

def ambil_data_statistik():
    try:
        db = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        cursor = db.cursor()

        # ====== QUERY 1: Data Trend (7 data terakhir saja) ======
        # Hanya mengambil 7 baris, BUKAN seluruh tabel.
        # Subquery diperlukan agar urutan data tetap ASC (kiri ke kanan di grafik).
        cursor.execute("""
            SELECT waktu, suhu, kelembapan_udara, kadar_co2 
            FROM (
                SELECT id, waktu, suhu, kelembapan_udara, kadar_co2 FROM tb_sensor ORDER BY id DESC LIMIT 7
            ) AS terbaru ORDER BY id ASC
        """)
        rows_trend = cursor.fetchall()

        if not rows_trend:
            return None

        # Ekstraksi untuk Trend (Grafik) — Maksimal 7 baris saja di RAM
        label_waktu = [row[0].strftime("%H:%M") for row in rows_trend]
        suhu_trend = [float(row[1]) for row in rows_trend]
        kel_udara_trend = [float(row[2]) for row in rows_trend]
        co2_trend = [int(row[3]) for row in rows_trend]

        # ====== QUERY 2: Agregasi (Dikerjakan oleh MySQL, bukan Python) ======
        # MySQL menghitung AVG, MAX, MIN di sisi server database.
        # Python hanya menerima 1 baris hasil, bukan ratusan ribu baris.
        cursor.execute("""
            SELECT 
                ROUND(AVG(suhu), 1),              MAX(suhu),              MIN(suhu),
                ROUND(AVG(kelembapan_udara), 1),   MAX(kelembapan_udara),  MIN(kelembapan_udara),
                ROUND(AVG(kadar_co2)),             MAX(kadar_co2),         MIN(kadar_co2)
            FROM tb_sensor
        """)
        agg = cursor.fetchone()

        return {
            "label_waktu": label_waktu,
            "suhu": {
                "trend": suhu_trend,
                "rata_rata": float(agg[0]) if agg[0] else 0,
                "tertinggi": float(agg[1]) if agg[1] else 0,
                "terendah": float(agg[2]) if agg[2] else 0
            },
            "kelembapan_udara": {
                "trend": kel_udara_trend,
                "rata_rata": float(agg[3]) if agg[3] else 0,
                "tertinggi": float(agg[4]) if agg[4] else 0,
                "terendah": float(agg[5]) if agg[5] else 0
            },
            "kadar_co2": {
                "trend": co2_trend,
                "rata_rata": int(agg[6]) if agg[6] else 0,
                "tertinggi": int(agg[7]) if agg[7] else 0,
                "terendah": int(agg[8]) if agg[8] else 0
            }
        }
        
    except mysql.connector.Error as err:
        print(f"[ERROR DB STATISTIK] Gagal mengambil data: {err}")
        return None
    finally:
        if 'db' in locals() and db.is_connected():
            if 'cursor' in locals():
                cursor.close()
            db.close()