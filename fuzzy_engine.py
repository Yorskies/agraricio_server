# fuzzy_engine.py
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ================= 1. INISIALISASI VARIABEL =================
# Input (Antecedent)
suhu = ctrl.Antecedent(np.arange(0, 41, 1), 'suhu')
kelembapan = ctrl.Antecedent(np.arange(0, 101, 1), 'kelembapan')

# Output (Consequent)
kipas = ctrl.Consequent(np.arange(0, 256, 1), 'kipas')
mist_maker = ctrl.Consequent(np.arange(0, 101, 1), 'mist_maker')

# ================= 2. MEMBERSHIP FUNCTION =================
# Himpunan Suhu (Target Ideal: 16-22 C)
suhu['dingin'] = fuzz.trapmf(suhu.universe, [0, 0, 15, 17])
suhu['ideal'] = fuzz.trimf(suhu.universe, [16, 19, 22])
suhu['panas'] = fuzz.trapmf(suhu.universe, [21, 23, 40, 40])

# Himpunan Kelembapan Udara (Target Ideal: 80-95%)
kelembapan['kering'] = fuzz.trapmf(kelembapan.universe, [0, 0, 75, 82])
kelembapan['ideal'] = fuzz.trimf(kelembapan.universe, [80, 88, 96])
kelembapan['basah'] = fuzz.trapmf(kelembapan.universe, [94, 97, 100, 100])

# Himpunan Kipas (PWM 0 - 255)
kipas['mati'] = fuzz.trimf(kipas.universe, [0, 0, 50])
kipas['lambat'] = fuzz.trimf(kipas.universe, [40, 120, 200])
kipas['cepat'] = fuzz.trapmf(kipas.universe, [180, 220, 255, 255])

# Himpunan Mist Maker (0-100% Intensitas)
mist_maker['mati'] = fuzz.trapmf(mist_maker.universe, [0, 0, 30, 60])
mist_maker['menyala'] = fuzz.trapmf(mist_maker.universe, [40, 70, 100, 100])

# ================= 3. RULE BASE (ATURAN IF-THEN) =================
rule1 = ctrl.Rule(suhu['panas'] & kelembapan['kering'], (kipas['cepat'], mist_maker['menyala']))
rule2 = ctrl.Rule(suhu['panas'] & kelembapan['ideal'], (kipas['cepat'], mist_maker['mati']))
rule3 = ctrl.Rule(suhu['panas'] & kelembapan['basah'], (kipas['cepat'], mist_maker['mati']))

rule4 = ctrl.Rule(suhu['ideal'] & kelembapan['kering'], (kipas['lambat'], mist_maker['menyala']))
rule5 = ctrl.Rule(suhu['ideal'] & kelembapan['ideal'], (kipas['mati'], mist_maker['mati']))
rule6 = ctrl.Rule(suhu['ideal'] & kelembapan['basah'], (kipas['mati'], mist_maker['mati']))

rule7 = ctrl.Rule(suhu['dingin'] & kelembapan['kering'], (kipas['mati'], mist_maker['menyala']))
rule8 = ctrl.Rule(suhu['dingin'] & kelembapan['ideal'], (kipas['mati'], mist_maker['mati']))
rule9 = ctrl.Rule(suhu['dingin'] & kelembapan['basah'], (kipas['mati'], mist_maker['mati']))

# Membangun sistem kontrol
sistem_kontrol = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9])
mesin_fuzzy = ctrl.ControlSystemSimulation(sistem_kontrol)

# ================= 4. FUNGSI EKSEKUSI =================
def hitung_fuzzy(nilai_suhu, nilai_kelembapan):
    try:
        # Masukkan nilai sensor ke mesin fuzzy
        mesin_fuzzy.input['suhu'] = nilai_suhu
        mesin_fuzzy.input['kelembapan'] = nilai_kelembapan
        
        # Lakukan komputasi (Defuzzifikasi)
        mesin_fuzzy.compute()
        
        # Ambil hasil nilai crisp-nya (angka pasti)
        hasil_kipas = int(mesin_fuzzy.output['kipas'])
        hasil_mist = int(mesin_fuzzy.output['mist_maker'])
        
        return hasil_kipas, hasil_mist
    
    except Exception as e:
        print(f"[ERROR FUZZY] Komputasi gagal: {e}")
        return 0, 0