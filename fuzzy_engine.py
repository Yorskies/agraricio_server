# fuzzy_engine.py (Revisi Jamur Merang)
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ================= 1. INISIALISASI VARIABEL =================
# Input (Antecedent) - Hanya 3 Parameter
suhu = ctrl.Antecedent(np.arange(0, 51, 1), 'suhu') # Rentang 0-50 C
kelembapan = ctrl.Antecedent(np.arange(0, 101, 1), 'kelembapan')
co2 = ctrl.Antecedent(np.arange(0, 2001, 1), 'co2')

# Output (Consequent) - Hanya 3 Aktuator
kipas = ctrl.Consequent(np.arange(0, 256, 1), 'kipas') # PWM 0-255
mist_maker = ctrl.Consequent(np.arange(0, 101, 1), 'mist_maker') # %
lampu_pemanas = ctrl.Consequent(np.arange(0, 101, 1), 'lampu_pemanas') # %

# ================= 2. MEMBERSHIP FUNCTION =================
# --- Input Membership (Kalibrasi Jamur Merang) ---

# 1. Suhu (Target Ideal: 30-35 C)
suhu['dingin'] = fuzz.trapmf(suhu.universe, [0, 0, 26, 28])
suhu['ideal'] = fuzz.trimf(suhu.universe, [27, 32, 35])
suhu['panas'] = fuzz.trapmf(suhu.universe, [34, 36, 50, 50])

# 2. Kelembapan Udara (Target Ideal: 80-90%)
kelembapan['kering'] = fuzz.trapmf(kelembapan.universe, [0, 0, 75, 80])
kelembapan['ideal'] = fuzz.trimf(kelembapan.universe, [78, 85, 92])
kelembapan['basah'] = fuzz.trapmf(kelembapan.universe, [90, 95, 100, 100])

# 3. CO2 (Target Ideal < 1000 ppm)
co2['normal'] = fuzz.trapmf(co2.universe, [0, 0, 800, 1000])
co2['tinggi'] = fuzz.trapmf(co2.universe, [800, 1000, 2000, 2000])

# --- Output Membership ---
# Kipas (PWM 0 - 255)
kipas['mati'] = fuzz.trimf(kipas.universe, [0, 0, 50])
kipas['lambat'] = fuzz.trimf(kipas.universe, [40, 120, 200])
kipas['cepat'] = fuzz.trapmf(kipas.universe, [180, 220, 255, 255])

# Mist Maker & Lampu Pemanas (ON/OFF - Threshold 50%)
for output_var in [mist_maker, lampu_pemanas]:
    output_var['mati'] = fuzz.trapmf(output_var.universe, [0, 0, 30, 60])
    output_var['menyala'] = fuzz.trapmf(output_var.universe, [40, 70, 100, 100])

# ================= 3. RULE BASE (ATURAN IF-THEN) =================
# Aturan Suhu -> Lampu Pemanas (Heater Darurat)
rule1 = ctrl.Rule(suhu['dingin'], lampu_pemanas['menyala'])
rule2 = ctrl.Rule(suhu['ideal'] | suhu['panas'], lampu_pemanas['mati'])

# Aturan Kelembapan -> Mist Maker
rule3 = ctrl.Rule(kelembapan['kering'], mist_maker['menyala'])
rule4 = ctrl.Rule(kelembapan['ideal'] | kelembapan['basah'], mist_maker['mati'])

# Aturan Gabungan Suhu & CO2 -> Kipas Exhaust
rule5 = ctrl.Rule(co2['tinggi'], kipas['cepat']) # Prioritas utama: Buang racun
rule6 = ctrl.Rule(co2['normal'] & suhu['panas'], kipas['lambat']) # Buang panas perlahan
rule7 = ctrl.Rule(co2['normal'] & suhu['ideal'], kipas['mati'])
rule8 = ctrl.Rule(co2['normal'] & suhu['dingin'], kipas['mati']) # Tahan panas agar tidak terbuang

# Membangun sistem kontrol
sistem_kontrol = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
mesin_fuzzy = ctrl.ControlSystemSimulation(sistem_kontrol)

# ================= 4. FUNGSI EKSEKUSI =================
def hitung_fuzzy(nilai_suhu, nilai_kelembapan, nilai_co2):
    try:
        mesin_fuzzy.input['suhu'] = nilai_suhu
        mesin_fuzzy.input['kelembapan'] = nilai_kelembapan
        mesin_fuzzy.input['co2'] = nilai_co2
        
        mesin_fuzzy.compute()
        
        hasil_kipas = int(mesin_fuzzy.output['kipas'])
        hasil_mist = int(mesin_fuzzy.output['mist_maker'])
        hasil_lampu = int(mesin_fuzzy.output['lampu_pemanas'])
        
        return hasil_kipas, hasil_mist, hasil_lampu
    
    except Exception as e:
        print(f"[ERROR FUZZY] Komputasi gagal: {e}")
        return 0, 0, 0