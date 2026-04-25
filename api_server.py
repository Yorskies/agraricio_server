# api_server.py
# Modul Flask REST API untuk Aplikasi Monitoring Agraric.io
# Diimpor dan dijalankan oleh main.py

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import ambil_data_statistik

app = Flask(__name__)
CORS(app)  # Mengizinkan akses dari IP mana saja (HP Samsung / Flutter App)

# ========================================================
# GLOBAL STATE: Menyimpan Mode Operasi & Nilai Override
# Diakses oleh Flask (main thread) & MQTT (background thread)
# ========================================================
SYSTEM_STATE = {
    "mode": "AUTO",             # Opsi: AUTO, SIMULASI_SENSOR, MANUAL_AKTUATOR
    "manual_kipas": 0,          # PWM 0-255 (untuk mode MANUAL)
    "manual_mist": "OFF",       # ON/OFF    (untuk mode MANUAL)
    "manual_heater": "OFF",     # ON/OFF    (untuk mode MANUAL)
    "sim_suhu": 32.0,           # °C        (untuk mode SIMULASI)
    "sim_kel": 85.0,            # %         (untuk mode SIMULASI)
    "sim_co2": 800              # PPM       (untuk mode SIMULASI)
}

# ========================================================
# ENDPOINT: ROOT / HEALTH CHECK
# ========================================================
@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Agraric.io REST API Server Berjalan Sempurna!"}), 200

# ========================================================
# ENDPOINT: STATISTIK & ANALITIK KUMBUNG JAMUR
# ========================================================
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        # Ambil data langsung dari database melalui fungsi di database.py
        data_statistik = ambil_data_statistik()

        if data_statistik is None:
            return jsonify({
                "status": "error",
                "pesan": "Belum ada data sensor di database."
            }), 404

        # Format JSON Standar Industri untuk Grafik Flutter
        response_data = {
            "status": "success",
            "pesan": "Data berhasil diambil dari database",
            "data": data_statistik  # Langsung dari ambil_data_statistik()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "pesan": f"Gagal mengambil data dari server: {str(e)}"
        }), 500

# ========================================================
# ENDPOINT: KONTROL MODE OPERASI (POST dari Mobile App)
# ========================================================
@app.route('/api/control', methods=['POST'])
def post_control():
    """
    Menerima JSON dari Mobile App untuk mengubah mode operasi server.
    
    Contoh payload per mode:
    - AUTO:              {"mode": "AUTO"}
    - SIMULASI_SENSOR:   {"mode": "SIMULASI_SENSOR", "sim_suhu": 35.0, "sim_kel": 90.0, "sim_co2": 1200}
    - MANUAL_AKTUATOR:   {"mode": "MANUAL_AKTUATOR", "manual_kipas": 200, "manual_mist": "ON", "manual_heater": "OFF"}
    """
    try:
        data = request.get_json()

        if data is None:
            return jsonify({
                "status": "error",
                "pesan": "Request body harus berupa JSON yang valid."
            }), 400

        # --- 1. Update Mode (jika ada key "mode" di request) ---
        if "mode" in data:
            mode_baru = data["mode"].upper()
            mode_valid = ["AUTO", "SIMULASI_SENSOR", "MANUAL_AKTUATOR"]

            if mode_baru not in mode_valid:
                return jsonify({
                    "status": "error",
                    "pesan": f"Mode '{mode_baru}' tidak dikenali. Pilihan: {mode_valid}"
                }), 400
            
            SYSTEM_STATE["mode"] = mode_baru
            print(f"\n🔀 [API] Mode operasi diubah menjadi: {mode_baru}")

        # --- 2. Update nilai manual aktuator (jika mode MANUAL) ---
        if SYSTEM_STATE["mode"] == "MANUAL_AKTUATOR":
            if "manual_kipas" in data:
                SYSTEM_STATE["manual_kipas"] = int(data["manual_kipas"])
            if "manual_mist" in data:
                SYSTEM_STATE["manual_mist"] = data["manual_mist"].upper()
            if "manual_heater" in data:
                SYSTEM_STATE["manual_heater"] = data["manual_heater"].upper()
            
            print(f"   [MANUAL] Kipas: {SYSTEM_STATE['manual_kipas']} | "
                  f"Mist: {SYSTEM_STATE['manual_mist']} | "
                  f"Heater: {SYSTEM_STATE['manual_heater']}")

        # --- 3. Update nilai simulasi sensor (jika mode SIMULASI) ---
        if SYSTEM_STATE["mode"] == "SIMULASI_SENSOR":
            if "sim_suhu" in data:
                SYSTEM_STATE["sim_suhu"] = float(data["sim_suhu"])
            if "sim_kel" in data:
                SYSTEM_STATE["sim_kel"] = float(data["sim_kel"])
            if "sim_co2" in data:
                SYSTEM_STATE["sim_co2"] = int(data["sim_co2"])
            
            print(f"   [SIMULASI] Suhu: {SYSTEM_STATE['sim_suhu']}°C | "
                  f"Kel: {SYSTEM_STATE['sim_kel']}% | "
                  f"CO2: {SYSTEM_STATE['sim_co2']} ppm")

        return jsonify({
            "status": "success",
            "pesan": f"State berhasil diperbarui (Mode: {SYSTEM_STATE['mode']})",
            "state": SYSTEM_STATE
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "pesan": f"Gagal memproses perintah kontrol: {str(e)}"
        }), 500

# ========================================================
# ENDPOINT: CEK STATE SAAT INI (GET dari Mobile App)
# ========================================================
@app.route('/api/control', methods=['GET'])
def get_control():
    """Mengembalikan SYSTEM_STATE saat ini tanpa mengubah apapun."""
    return jsonify({
        "status": "success",
        "state": SYSTEM_STATE
    }), 200

@app.route('/api/sensors/latest', methods=['GET'])
def get_latest_data():
    try:
        # PENTING: Gunakan objek koneksi 'db' yang sudah ada di aplikasi Anda
        # Kita buat cursor baru khusus untuk request ini
        # dictionary=True agar hasil SELECT bisa diakses seperti sensor['suhu']
        cur = db.cursor(dictionary=True) 
        
        # 1. Ambil data sensor terbaru
        cur.execute("SELECT * FROM tb_sensor ORDER BY id DESC LIMIT 1")
        sensor = cur.fetchone()
        
        # 2. Ambil status aktuator terbaru
        cur.execute("SELECT * FROM tb_aktuator ORDER BY id DESC LIMIT 1")
        aktuator = cur.fetchone()

        # Tutup cursor setelah digunakan
        cur.close()

        if sensor:
            return jsonify({
                "status": "success",
                "data": {
                    "suhu": sensor['suhu'],
                    "kelembapan_udara": sensor['kelembapan_udara'],
                    "kadar_co2": sensor['kadar_co2'],
                    "kipas_pwm": aktuator['kipas_exhaust'] if aktuator else 0,
                    "mist_maker": aktuator['mist_maker'] if aktuator else "OFF",
                    "heater": aktuator['lampu_pemanas'] if aktuator else "OFF",
                    "mode": SYSTEM_STATE["mode"]
                }
            }), 200
        else:
            return jsonify({"status": "error", "message": "No data found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500