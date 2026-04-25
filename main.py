# main.py
# Pusat Kontrol Server IoT Kumbung Jamur Merang
# Menjalankan MQTT Listener (Thread) + Flask REST API (Main)

import threading
import paho.mqtt.client as mqtt
import json
import config

from database import simpan_ke_database, simpan_aktuator_ke_database
from fuzzy_engine import hitung_fuzzy
from api_server import SYSTEM_STATE

# ================= 1. CALLBACK KONEKSI MQTT (API V2) =================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[MQTT] Terhubung ke Broker MQTT (Kode: {reason_code})")
        client.subscribe(config.TOPIC_SENSOR)
        print(f"[MQTT] Mendengarkan data di stasiun: {config.TOPIC_SENSOR} ...\n")
    else:
        print(f"[MQTT ERROR] Gagal terhubung ke broker! Kode: {reason_code}")

# ================= 2. CALLBACK TERIMA PESAN MQTT =================
def on_message(client, userdata, msg):
    try:
        mode = SYSTEM_STATE["mode"]

        print("-" * 50)
        print(f"⚙️  [MODE AKTIF] {mode}")

        # ==============================================================
        # CABANG A: MODE AUTO — Gunakan sensor fisik ESP32 + Fuzzy
        # ==============================================================
        if mode == "AUTO":
            payload = json.loads(msg.payload.decode("utf-8"))

            suhu      = payload.get('suhu', 0.0)
            kel_udara = payload.get('kelembapan_udara', 0.0)
            co2       = payload.get('kadar_co2', 0)

            print(f"📥 [SENSOR FISIK] Suhu: {suhu}°C | Kel: {kel_udara}% | CO2: {co2} ppm")

            # Simpan Data Sensor ke Database
            simpan_ke_database(suhu, kel_udara, co2)

            # Hitung Fuzzy Logic Mamdani
            kipas_pwm, mist_intensitas, lampu_intensitas = hitung_fuzzy(suhu, kel_udara, co2)

            status_mist  = "ON" if mist_intensitas > 50 else "OFF"
            status_lampu = "ON" if lampu_intensitas > 50 else "OFF"

            print(f"🧠 [FUZZY] Kipas: {kipas_pwm} | Mist: {status_mist} | Heater: {status_lampu}")

        # ==============================================================
        # CABANG B: MODE SIMULASI — Abaikan sensor, pakai nilai dari App
        # ==============================================================
        elif mode == "SIMULASI_SENSOR":
            print("🔬 [SIMULASI] Mengabaikan sensor fisik ESP32!")

            suhu      = SYSTEM_STATE["sim_suhu"]
            kel_udara = SYSTEM_STATE["sim_kel"]
            co2       = SYSTEM_STATE["sim_co2"]

            print(f"📡 [SIMULASI INPUT] Suhu: {suhu}°C | Kel: {kel_udara}% | CO2: {co2} ppm")

            # Simpan Data Simulasi ke Database (agar grafik tetap jalan)
            simpan_ke_database(suhu, kel_udara, co2)

            # Hitung Fuzzy Logic Mamdani (dengan input simulasi)
            kipas_pwm, mist_intensitas, lampu_intensitas = hitung_fuzzy(suhu, kel_udara, co2)

            status_mist  = "ON" if mist_intensitas > 50 else "OFF"
            status_lampu = "ON" if lampu_intensitas > 50 else "OFF"

            print(f"🧠 [FUZZY] Kipas: {kipas_pwm} | Mist: {status_mist} | Heater: {status_lampu}")

        # ==============================================================
        # CABANG C: MODE MANUAL — Abaikan sensor DAN fuzzy, kontrol langsung
        # ==============================================================
        elif mode == "MANUAL_AKTUATOR":
            print("🕹️  [MANUAL] Mengabaikan sensor fisik DAN fuzzy logic!")

            kipas_pwm    = SYSTEM_STATE["manual_kipas"]
            status_mist  = SYSTEM_STATE["manual_mist"]
            status_lampu = SYSTEM_STATE["manual_heater"]

            print(f"🎛️  [MANUAL OUTPUT] Kipas: {kipas_pwm} | Mist: {status_mist} | Heater: {status_lampu}")

        # --- Aksi Bersama: Publish ke MQTT & Simpan ke DB ---
        perintah_aktuator = {
            "kipas_pwm": kipas_pwm,
            "mist_maker": status_mist,
            "lampu_pemanas": status_lampu
        }
        client.publish(config.TOPIC_AKTUATOR, json.dumps(perintah_aktuator))
        print(f"📤 [MQTT KIRIM] Perintah aktuator diterbitkan ke ESP32!")

        simpan_aktuator_ke_database(kipas_pwm, status_mist, status_lampu)

        print("-" * 50)

    except Exception as e:
        print(f"[ERROR MAIN] Terjadi kesalahan saat memproses data: {e}")

# ================= 3. FUNGSI THREAD MQTT =================
def jalankan_mqtt():
    """Menjalankan MQTT Client di thread terpisah (background)."""
    print("[THREAD] Memulai MQTT Client di background thread...")
    print(f"[THREAD] Target Broker: {config.MQTT_BROKER} (Port {config.MQTT_PORT})")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        print("[THREAD] Koneksi TCP ke broker berhasil! Menunggu jabat tangan MQTT...")
        client.loop_forever()
    except Exception as e:
        print(f"[THREAD FATAL] Gagal menjalankan MQTT Client: {e}")

# ================= 4. ENTRY POINT UTAMA =================
if __name__ == "__main__":
    print("=" * 55)
    print("  SERVER KUMBUNG JAMUR MERANG - AGRARIC.IO")
    print("  MQTT Listener + Flask REST API (Threaded)")
    print("=" * 55)

    # 1. Jalankan MQTT di background thread (daemon)
    #    daemon=True artinya thread akan otomatis mati saat main program berhenti
    mqtt_thread = threading.Thread(target=jalankan_mqtt, daemon=True)
    mqtt_thread.start()
    print("[MAIN] MQTT Client berjalan di background thread.\n")

    # 2. Jalankan Flask REST API di main thread
    #    Import app dari api_server.py
    from api_server import app
    
    print("[MAIN] Memulai Flask REST API Server...")
    print(f"[MAIN] API dapat diakses dari: http://0.0.0.0:5000\n")
    
    # debug=False karena kita sudah mengelola threading secara manual
    # use_reloader=False agar Flask tidak me-restart dan menduplikasi thread MQTT
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)