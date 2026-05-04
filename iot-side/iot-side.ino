#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HardwareSerial.h>
#include <MHZ19.h>

// --- KONFIGURASI WIFI & MQTT ---
const char* ssid        = "ESP32";
const char* password    = "12345678";
const char* mqtt_server = "168.144.136.41"; // IP VPS
const int   mqtt_port   = 1883;

const char* clientID      = "ESP32_Kumbung_01";
const char* topic_sensor  = "agraric/kumbung1/sensors";
const char* topic_control = "agraric/kumbung1/actuators";

// --- KONFIGURASI PIN AKTUATOR ---
const int PIN_KIPAS  = 19; // MOSFET (PWM)
const int PIN_MIST   = 18; // MOSFET (Digital Active High)
const int PIN_HEATER = 21; // RELAY (Digital Active Low)

// --- KONFIGURASI SENSOR ---
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

#define RX_PIN 16 // Hubungkan ke TX MH-Z19C
#define TX_PIN 17 // Hubungkan ke RX MH-Z19C
HardwareSerial mySerial(2); // Menggunakan Hardware Serial 2 milik ESP32
MHZ19 myMHZ19;

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;

void setup_wifi() {
  delay(10);
  Serial.println("\nConnecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected! IP: " + WiFi.localIP().toString());
}

// --- FUNGSI MENERIMA PERINTAH (OVERRIDE / FUZZY) ---
void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  deserializeJson(doc, payload, length);

  if (doc.containsKey("kipas_pwm")) {
    int pwmValue = doc["kipas_pwm"];
    analogWrite(PIN_KIPAS, pwmValue);
  }
  
  if (doc.containsKey("mist_maker")) {
    const char* mistStatus = doc["mist_maker"];
    digitalWrite(PIN_MIST, (strcmp(mistStatus, "ON") == 0) ? HIGH : LOW); 
  }

  if (doc.containsKey("heater")) {
    const char* heaterStatus = doc["heater"];
    digitalWrite(PIN_HEATER, (strcmp(heaterStatus, "ON") == 0) ? LOW : HIGH);
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect(clientID)) {
      Serial.println(" Connected!");
      client.subscribe(topic_control); 
    } else {
      Serial.println(" Failed. Retrying in 5s...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Inisialisasi Sensor
  dht.begin();
  mySerial.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN);
  myMHZ19.begin(mySerial);
  myMHZ19.autoCalibration(false); // Matikan Auto-Kalibrasi (penting untuk lingkungan tertutup)

  // Inisialisasi WiFi & MQTT
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Inisialisasi Pin Aktuator
  pinMode(PIN_KIPAS, OUTPUT);
  pinMode(PIN_MIST, OUTPUT);
  pinMode(PIN_HEATER, OUTPUT);

  // Status Awal (Semua Mati)
  analogWrite(PIN_KIPAS, 0);       
  digitalWrite(PIN_MIST, LOW);     
  digitalWrite(PIN_HEATER, HIGH);  

  Serial.println("Sistem Siap! Memanaskan sensor (Butuh ~3 menit untuk CO2)...");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  // Kirim data setiap 5 detik (5000 ms)
  if (now - lastMsg > 5000) {
    lastMsg = now;

    // --- PEMBACAAN SENSOR FISIK ---
    float suhu = dht.readTemperature();
    float hum  = dht.readHumidity();
    int co2    = myMHZ19.getCO2();

    // Cek apakah DHT22 error/kabel goyang
    if (isnan(suhu) || isnan(hum)) {
      Serial.println("Gagal membaca DHT22! Cek kabel.");
      return; // Batal kirim data, tunggu 5 detik lagi
    }

    // --- CETAK KE SERIAL MONITOR ---
    Serial.printf("Suhu: %.1f °C | Kel: %.1f %% | CO2: %d ppm\n", suhu, hum, co2);

    // --- BUNGKUS KE JSON & KIRIM ---
    StaticJsonDocument<200> doc;
    doc["suhu"] = suhu;
    doc["kelembapan_udara"] = hum;
    doc["kadar_co2"] = co2;

    char buffer[256];
    serializeJson(doc, buffer);
    client.publish(topic_sensor, buffer);
  }
}