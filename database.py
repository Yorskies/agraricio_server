# database.py
import mysql.connector
from datetime import datetime
import config

def simpan_ke_database(suhu, kelembapan_udara, kelembapan_media, co2, ph):
    try:
        db = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        cursor = db.cursor()

        sql = """INSERT INTO tb_sensor 
                 (suhu, kelembapan_udara, kelembapan_media, kadar_co2, kadar_ph) 
                 VALUES (%s, %s, %s, %s, %s)"""
        val = (suhu, kelembapan_udara, kelembapan_media, co2, ph)
        
        cursor.execute(sql, val)
        db.commit()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [DB] Data Sensor tersimpan.")
        
    except mysql.connector.Error as err:
        print(f"[ERROR DB] Gagal menyimpan: {err}")
    finally:
        if 'db' in locals() and db.is_connected():
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

        # Menyedot seluruh 5 parameter dari database
        cursor.execute("""
            SELECT id, waktu, suhu, kelembapan_udara, 
                   kelembapan_media, kadar_co2, kadar_ph 
            FROM tb_sensor ORDER BY id ASC
        """)
        rows = cursor.fetchall()

        if not rows:
            return None 

        # Ambil maksimal 7 data TERAKHIR untuk grafik trend
        data_terakhir = rows[-7:] if len(rows) >= 7 else rows
        
        # Ekstraksi untuk Trend (Grafik)
        label_waktu = [row[1].strftime("%H:%M") for row in data_terakhir]
        suhu_trend = [float(row[2]) for row in data_terakhir]
        kel_udara_trend = [float(row[3]) for row in data_terakhir]
        kel_media_trend = [float(row[4]) for row in data_terakhir]
        co2_trend = [int(row[5]) for row in data_terakhir]
        ph_trend = [float(row[6]) for row in data_terakhir]

        # Ekstraksi untuk Agregasi (Keseluruhan Data)
        semua_suhu = [float(row[2]) for row in rows]
        semua_kel_udara = [float(row[3]) for row in rows]
        semua_kel_media = [float(row[4]) for row in rows]
        semua_co2 = [int(row[5]) for row in rows]
        semua_ph = [float(row[6]) for row in rows]

        return {
            "label_waktu": label_waktu,
            "suhu": {
                "trend": suhu_trend,
                "rata_rata": round(sum(semua_suhu) / len(semua_suhu), 1),
                "tertinggi": round(max(semua_suhu), 1),
                "terendah": round(min(semua_suhu), 1)
            },
            "kelembapan_udara": {
                "trend": kel_udara_trend,
                "rata_rata": round(sum(semua_kel_udara) / len(semua_kel_udara), 1),
                "tertinggi": round(max(semua_kel_udara), 1),
                "terendah": round(min(semua_kel_udara), 1)
            },
            "kelembapan_media": {
                "trend": kel_media_trend,
                "rata_rata": round(sum(semua_kel_media) / len(semua_kel_media), 1),
                "tertinggi": round(max(semua_kel_media), 1),
                "terendah": round(min(semua_kel_media), 1)
            },
            "kadar_co2": {
                "trend": co2_trend,
                "rata_rata": int(sum(semua_co2) / len(semua_co2)),
                "tertinggi": int(max(semua_co2)),
                "terendah": int(min(semua_co2))
            },
            "kadar_ph": {
                "trend": ph_trend,
                "rata_rata": round(sum(semua_ph) / len(semua_ph), 1),
                "tertinggi": round(max(semua_ph), 1),
                "terendah": round(min(semua_ph), 1)
            }
        }
        
    except mysql.connector.Error as err:
        print(f"[ERROR DB STATISTIK] Gagal mengambil data: {err}")
        return None
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()