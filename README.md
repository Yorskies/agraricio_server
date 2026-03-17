# Agraric.io: Smart Mushroom Cultivation System 🍄

**Agraric.io** adalah sistem monitoring dan kontrol otomatis untuk budidaya jamur kancing menggunakan teknologi IoT, Kecerdasan Buatan (Fuzzy Logic), dan Aplikasi Mobile. Sistem ini dirancang untuk menjaga kondisi ideal suhu dan kelembapan secara real-time.

---

## 🏗️ Arsitektur Sistem

Proyek ini terdiri dari empat komponen utama yang bekerja secara sinkron:

1.  **AI Fuzzy Engine (Python)**: Menggunakan logika fuzzy Mamdani untuk menentukan kecepatan kipas (PWM) dan status *mist maker* berdasarkan input sensor suhu dan kelembapan.
2.  **MQTT Broker Integration**: Jalur komunikasi *real-time* antara sensor (ESP32), server kontrol, dan aplikasi mobile.
3.  **REST API Service (Flask)**: Menyediakan data statistik dan analitik historis untuk ditampilkan di aplikasi mobile.
4.  **Mobile Dashboard (Flutter)**: Antarmuka pengguna yang elegan untuk monitoring kondisi kumbung jamur dari mana saja.

---

## 🛠️ Tech Stack

### Backend & Control (Python)
- **Logika Fuzzy**: `scikit-fuzzy`, `numpy`
- **Komunikasi**: `paho-mqtt`
- **Database**: `mysql-connector-python`
- **Web API**: `Flask`, `flask-cors`

### Mobile App (Flutter)
- **State Management**: `Provider` (atau default Material)
- **Komunikasi**: `mqtt_client`, `http`
- **Visualisasi**: `fl_chart`

### Hardware (Simulated/ESP32)
- **Protokol**: MQTT
- **Data**: Suhu, Kelembapan Udara/Media, CO2, dan pH.

---

## 🚀 Cara Menjalankan

### 1. Persiapan Environment
```bash
# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependensi
pip install paho-mqtt flask flask-cors mysql-connector-python numpy scikit-fuzzy
```

### 2. Jalankan Server Utama (Mqtt Controller)
Server ini akan mendengarkan data dari sensor dan mengirim perintah ke aktuator.
```bash
python main.py
```

### 3. Jalankan API Server (Untuk Mobile)
```bash
python api_server.py
```

### 4. Jalankan Simulator ESP32 (Jika tidak ada hardware)
```bash
python esp32_simulator.py
```

---

## 📂 Struktur Folder
```text
.
├── agraric_io/          # Source Code Aplikasi Flutter
├── api_server.py       # REST API untuk data analytics
├── config.py           # Konfigurasi IP Broker & Database
├── database.py         # Modul interaksi MySQL
├── esp32_simulator.py  # GUI Simulator ESP32 (Tkinter)
├── fuzzy_engine.py    # Mesin Logika Fuzzy Mamdani
├── main.py             # MQTT Controller Utama
└── .gitignore          # File pengecualian Git
```

---

## 👤 Developer
- **Name**: Anri Anugerah Marpaung
- **University**: Universitas Sumatera Utara (USU)
- **Project Year**: 2026

---

© 2026 Universitas Sumatera Utara.
