// ==========================================
// DEFINISI PIN AKTUATOR (HANYA POMPA)
// ==========================================
const int PIN_PUMP_PH_DOWN = 26;   // Pompa pH Asam/Down (Relay IN2)
const int PIN_PUMP_PH_UP = 27;     // Pompa pH Basa/Up (Relay IN3)

void setup() {
  Serial.begin(115200);
  Serial.println(F("\n=== MEMULAI TEST AKTUATOR (Hanya Pompa Relay) ==="));

  // 1. SETUP RELAY POMPA
  pinMode(PIN_PUMP_PH_DOWN, OUTPUT);
  pinMode(PIN_PUMP_PH_UP, OUTPUT);
  
  // Matikan relay saat pertama kali hidup 
  // (Sebagian besar relay bekerja dengan sistem Active-LOW, artinya mati jika diberi HIGH)
  digitalWrite(PIN_PUMP_PH_DOWN, HIGH);
  digitalWrite(PIN_PUMP_PH_UP, HIGH);

  Serial.println(F("Setup selesai, memulai test dalam 2 detik..."));
  delay(2000); // Jeda sebelum memulai test
}

void loop() {
  Serial.println(F("\n--- SIKLUS TEST POMPA DIMULAI ---"));

  // ==========================================
  // TEST 1: POMPA pH DOWN (RELAY CH 2)
  // ==========================================
  Serial.println(F("1. Pompa pH DOWN (Asam) -> MENYALA [Cetek!]"));
  digitalWrite(PIN_PUMP_PH_DOWN, LOW);  // Memberikan sinyal LOW untuk menyalakan Relay
  delay(3000);                          // Tahan posisi menyala selama 3 detik
  
  Serial.println(F("   Pompa pH DOWN (Asam) -> MATI"));
  digitalWrite(PIN_PUMP_PH_DOWN, HIGH); // Memberikan sinyal HIGH untuk mematikan Relay
  delay(2000);                          // Jeda 2 detik sebelum pindah ke pompa sebelah

  // ==========================================
  // TEST 2: POMPA pH UP (RELAY CH 3)
  // ==========================================
  Serial.println(F("2. Pompa pH UP (Basa) -> MENYALA [Cetek!]"));
  digitalWrite(PIN_PUMP_PH_UP, LOW);    // Memberikan sinyal LOW untuk menyalakan Relay
  delay(3000);                          // Tahan posisi menyala selama 3 detik
  
  Serial.println(F("   Pompa pH UP (Basa) -> MATI"));
  digitalWrite(PIN_PUMP_PH_UP, HIGH);   // Memberikan sinyal HIGH untuk mematikan Relay
  
  // ==========================================
  // SELESAI SIKLUS
  // ==========================================
  Serial.println(F("--- SIKLUS SELESAI. Menunggu 5 detik untuk mengulang... ---"));
  delay(5000); // Istirahat 5 detik sebelum mengulang dari pompa pertama
}