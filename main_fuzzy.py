import paho.mqtt.client as mqtt
import mysql.connector
import json
from datetime import datetime

# ================= KONFIGURASI =================
# Konfigurasi MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_SENSOR = "kumbung/sensor"

# Konfigurasi Database XAMPP (Default)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_NAME = "db_jamur_kancing"
# ===============================================

# Fungsi untuk menyimpan data ke MySQL
def simpan_ke_database(suhu, kelembapan_udara, kelembapan_media, co2, ph):
    try:
        # Membuka koneksi ke MySQL
        db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = db.cursor()

        # Query SQL untuk memasukkan data ke tb_sensor
        sql = """INSERT INTO tb_sensor 
                 (suhu, kelembapan_udara, kelembapan_media, kadar_co2, kadar_ph) 
                 VALUES (%s, %s, %s, %s, %s)"""
        
        # Nilai yang akan dimasukkan
        val = (suhu, kelembapan_udara, kelembapan_media, co2, ph)
        
        # Eksekusi dan Simpan (Commit)
        cursor.execute(sql, val)
        db.commit() 
        
        waktu_sekarang = datetime.now().strftime('%H:%M:%S')
        print(f"[{waktu_sekarang}] [SUCCESS] Data berhasil direkam ke MySQL!")
        
    except mysql.connector.Error as err:
        print(f"[ERROR DB] Gagal menyimpan data: {err}")
    finally:
        # Menutup koneksi database agar tidak bocor (memory leak)
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

# Callback saat terhubung ke MQTT
def on_connect(client, userdata, flags, rc):
    print(f"[STATUS] Terhubung ke Broker (Kode: {rc})")
    client.subscribe(TOPIC_SENSOR)
    print(f"[STATUS] Standby mendengarkan topik: {TOPIC_SENSOR} ...\n")

# Callback saat ada pesan MQTT masuk
def on_message(client, userdata, msg):
    try:
        # 1. Ekstrak JSON
        payload = json.loads(msg.payload.decode("utf-8"))
        suhu = payload.get('suhu')
        kel_udara = payload.get('kelembapan_udara')
        kel_media = payload.get('kelembapan_media')
        co2 = payload.get('kadar_co2')
        ph = payload.get('kadar_ph')
        
        print("-" * 40)
        print(f"Data Masuk -> Suhu: {suhu}°C | Kelembapan: {kel_udara}% | pH: {ph}")
        
        # 2. Simpan ke Database
        simpan_ke_database(suhu, kel_udara, kel_media, co2, ph)
        
        # 3. TODO NEXT: Hitung Fuzzy Logic & Kirim Perintah ke Aktuator
        
    except Exception as e:
        print(f"[ERROR MQTT] Format pesan salah atau rusak: {e}")

# ================= EKSEKUSI UTAMA =================
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Memulai Server Utama Jamur Kancing...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()