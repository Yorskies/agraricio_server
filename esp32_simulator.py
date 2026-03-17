import tkinter as tk
from tkinter import ttk, scrolledtext
import paho.mqtt.client as mqtt
import json
import time

# ================= KONFIGURASI BROKER =================
BROKER_ADDRESS = "192.168.18.82" 
PORT = 1883
TOPIC_SENSOR = "agraric/kumbung1/sensors"
TOPIC_AKTUATOR = "agraric/kumbung1/actuators"

class SimulatorESP32_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Control Panel: ESP32 Simulator - Agraric.io")
        self.root.geometry("500x700")
        self.root.configure(padx=20, pady=20)
        
        self.is_running = False

        # ================= SETUP UI (SLIDERS) =================
        ttk.Label(root, text="⚙️ PENGATURAN SENSOR MANUAL", font=("Arial", 14, "bold")).pack(pady=(0, 20))

        # Variabel untuk Slider
        self.suhu_var = tk.DoubleVar(value=24.5)
        self.kel_udara_var = tk.DoubleVar(value=85.0)
        self.kel_media_var = tk.DoubleVar(value=65.0)
        self.co2_var = tk.IntVar(value=800)
        self.ph_var = tk.DoubleVar(value=7.0)

        # Membuat Slider UI
        self._buat_slider("Suhu Udara (°C)", self.suhu_var, 0, 50)
        self._buat_slider("Kelembapan Udara (%)", self.kel_udara_var, 0, 100)
        self._buat_slider("Kelembapan Media (%)", self.kel_media_var, 0, 100)
        self._buat_slider("Kadar CO2 (PPM)", self.co2_var, 400, 2000)
        self._buat_slider("pH Media", self.ph_var, 0, 14)

        # ================= SETUP UI (TOMBOL & LOG) =================
        self.btn_toggle = ttk.Button(root, text="▶ MULAI SIMULASI", command=self.toggle_simulasi)
        self.btn_toggle.pack(pady=20, fill='x', ipady=10)

        ttk.Label(root, text="Terminal Log:", font=("Arial", 10, "bold")).pack(anchor='w')
        self.log_area = scrolledtext.ScrolledText(root, height=12, state='disabled', bg='black', fg='lime', font=("Consolas", 9))
        self.log_area.pack(fill='both', expand=True)

        # ================= INISIALISASI MQTT =================
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    # ================= FUNGSI BANTUAN UI =================
    def _buat_slider(self, label_text, variable, min_val, max_val):
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', pady=5)
        
        # Label Nama & Nilai (Otomatis update saat digeser)
        lbl_frame = ttk.Frame(frame)
        lbl_frame.pack(fill='x')
        ttk.Label(lbl_frame, text=label_text).pack(side='left')
        
        value_label = ttk.Label(lbl_frame, text=str(variable.get()), font=("Arial", 10, "bold"), foreground="blue")
        value_label.pack(side='right')
        
        # Fungsi untuk mengupdate angka saat tuas digeser
        def update_label(val):
            # Format desimal 1 angka jika float, jika int biarkan
            formatted_val = f"{float(val):.1f}" if isinstance(variable, tk.DoubleVar) else str(int(float(val)))
            value_label.config(text=formatted_val)

        slider = ttk.Scale(frame, from_=min_val, to=max_val, orient='horizontal', variable=variable, command=update_label)
        slider.pack(fill='x')

    def log_print(self, message):
        """Mencetak pesan ke kotak terminal hitam di dalam GUI"""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END) # Auto-scroll ke bawah
        self.log_area.config(state='disabled')

    # ================= LOGIK MQTT =================
    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.log_print("[STATUS] Berhasil terhubung ke Broker!")
            self.client.subscribe(TOPIC_AKTUATOR)
        else:
            self.log_print(f"[ERROR] Gagal terhubung (Kode: {reason_code})")

    def on_message(self, client, userdata, msg):
        # Saat menerima perintah memutar kipas/mist maker dari main.py
        pesan = msg.payload.decode("utf-8")
        self.log_print(f"\n⚙️ PERINTAH AKTUATOR MASUK:\n{pesan}\n")

    def toggle_simulasi(self):
        if not self.is_running:
            # MULAI
            try:
                self.client.connect(BROKER_ADDRESS, PORT, 60)
                self.client.loop_start()
                self.is_running = True
                self.btn_toggle.config(text="⏹ HENTIKAN SIMULASI")
                self.log_print("\n=== SIMULASI DIMULAI ===")
                self.kirim_data_rutin() # Panggil loop pengiriman
            except Exception as e:
                self.log_print(f"[FATAL] Gagal Start: {e}")
        else:
            # BERHENTI
            self.is_running = False
            self.client.loop_stop()
            self.client.disconnect()
            self.btn_toggle.config(text="▶ MULAI SIMULASI")
            self.log_print("=== SIMULASI DIHENTIKAN ===\n")

    def kirim_data_rutin(self):
        if self.is_running:
            # Ambil data langsung dari posisi tuas slider saat ini
            payload = {
                "suhu": round(self.suhu_var.get(), 1),
                "kelembapan_udara": round(self.kel_udara_var.get(), 1),
                "kelembapan_media": round(self.kel_media_var.get(), 1),
                "kadar_co2": int(self.co2_var.get()),
                "kadar_ph": round(self.ph_var.get(), 1)
            }
            
            pesan_json = json.dumps(payload)
            self.client.publish(TOPIC_SENSOR, pesan_json)
            self.log_print(f"📡 KIRIM: {pesan_json}")
            
            # Gunakan 'after' agar GUI tidak nge-hang, ulang setiap 3000 ms (3 detik)
            self.root.after(3000, self.kirim_data_rutin)

# ================= JALANKAN APLIKASI GUI =================
if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorESP32_GUI(root)
    
    # Mencegah error jika jendela ditutup paksa menggunakan tanda 'X'
    def on_closing():
        if app.is_running:
            app.client.loop_stop()
            app.client.disconnect()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()