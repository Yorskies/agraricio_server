from flask import Flask, jsonify
from flask_cors import CORS

# Nanti Anda bisa meng-import modul database Anda di sini
# import database 

app = Flask(__name__)
CORS(app) # Mengizinkan akses dari IP mana saja (HP Samsung Anda)

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Agraric.io REST API Server Berjalan Sempurna!"}), 200

# ========================================================
# ENDPOINT: STATISTIK & ANALITIK KUMBUNG JAMUR
# ========================================================
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        # ----------------------------------------------------
        # TUGAS BERIKUTNYA UNTUK ANDA:
        # Ganti data statis di bawah ini dengan hasil query (SELECT)
        # dari database MySQL Anda melalui fungsi di database.py.
        # Contoh: data_mentah = database.ambil_data_mingguan()
        # ----------------------------------------------------
        
        # Format JSON Standar Industri untuk Grafik Flutter
        response_data = {
            "status": "success",
            "pesan": "Data berhasil diambil",
            "data": {
                "suhu": {
                    "trend": [22.0, 24.5, 26.0, 25.5, 23.0, 24.0, 24.8], # Data 7 hari
                    "rata_rata": 24.2,
                    "tertinggi": 26.0,
                    "terendah": 22.0
                },
                "kelembapan": {
                    "trend": [80.0, 85.0, 82.0, 78.0, 88.0, 85.0, 84.0],
                    "rata_rata": 83.1,
                    "tertinggi": 88.0,
                    "terendah": 78.0
                },
                "label_hari": ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        # Penanganan error yang elegan
        return jsonify({
            "status": "error", 
            "pesan": f"Gagal mengambil data dari server: {str(e)}"
        }), 500


# ========================================================
# MENJALANKAN SERVER FLASK
# ========================================================
if __name__ == '__main__':
    print("=== FLASK REST API SERVER AKTIF ===")
    print("Mendengarkan permintaan dari Flutter...")
    
    # PERHATIAN: host='0.0.0.0' WAJIB digunakan agar API ini 
    # bisa diakses oleh IP 192.168.18.42 (HP Samsung Anda)
    app.run(host='0.0.0.0', port=5000, debug=True)