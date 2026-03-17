import paho.mqtt.client as mqtt
import json
import config

# Pastikan import ini sesuai dengan file Anda
from database import simpan_ke_database
from fuzzy_engine import hitung_fuzzy

# ================= 1. CALLBACK KONEKSI (API V2) =================
# Di V2, parameter 'rc' berubah menjadi 'reason_code', dan ada tambahan 'properties'
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[STATUS] Terhubung ke Broker MQTT (Kode: {reason_code})")
        client.subscribe(config.TOPIC_SENSOR)
        print(f"[STATUS] Mendengarkan data di stasiun: {config.TOPIC_SENSOR} ...\n")
    else:
        print(f"[ERROR] Gagal terhubung ke broker! Kode: {reason_code}")

# ================= 2. CALLBACK TERIMA PESAN =================
def on_message(client, userdata, msg):
    try:
        # Parsing Data Mentah dari Simulator/ESP32
        payload = json.loads(msg.payload.decode("utf-8"))
        
        # Mengambil data menggunakan key yang sama persis dengan simulator
        suhu = payload.get('suhu', 0.0)
        kel_udara = payload.get('kelembapan_udara', 0.0)
        kel_media = payload.get('kelembapan_media', 0.0)
        co2 = payload.get('kadar_co2', 0)
        ph = payload.get('kadar_ph', 0.0)
        
        print("-" * 50)
        print(f"📥 [SENSOR MASUK] Suhu: {suhu}°C | Kelembapan: {kel_udara}%")
        
        # Simpan ke Database
        # simpan_ke_database(suhu, kel_udara, kel_media, co2, ph)
        print("[DB] Data berhasil disimpan (Simulasi)")
        
        # Hitung Menggunakan Fuzzy Logic Mamdani
        kipas_pwm, mist_intensitas = hitung_fuzzy(suhu, kel_udara)
        
        # Konversi intensitas mist maker menjadi status ON/OFF (Threshold 50%)
        status_mist = "ON" if mist_intensitas > 50 else "OFF"
        
        print(f"🧠 [FUZZY OUTPUT] Kipas PWM: {kipas_pwm} | Mist Maker: {status_mist}")
        
        # Kirim Perintah Kembali ke ESP32 (Aktuator)
        perintah_aktuator = {
            "kipas_pwm": kipas_pwm,
            "mist_maker": status_mist
        }
        client.publish(config.TOPIC_AKTUATOR, json.dumps(perintah_aktuator))
        print(f"📤 [MQTT KIRIM] Perintah aktuator diterbitkan!")
        print("-" * 50)

    except Exception as e:
        print(f"[ERROR MAIN] Terjadi kesalahan saat memproses data: {e}")

# ================= 3. INISIALISASI & EKSEKUSI =================
if __name__ == "__main__":
    print("=== SERVER KUMBUNG JAMUR KANCING (MODULAR) ===")
    
    # 1. Pastikan IP yang ditarik dari config benar
    print(f"[*] Target Broker: {config.MQTT_BROKER} (Port {config.MQTT_PORT})")
    print("[*] Sedang mencoba menghubungi TCP...")
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # 2. Proses mengetuk pintu
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        
        # 3. Jika baris ini tercetak, berarti IP dan Port benar!
        print("[*] Pintu terbuka! Menunggu balasan jabat tangan MQTT (on_connect)...")
        
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n[STATUS] Server dimatikan.")
        client.disconnect()
    except Exception as e:
        print(f"[FATAL ERROR] Gagal menjalankan server: {e}")