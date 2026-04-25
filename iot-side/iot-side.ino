#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "DHT.h"
#include <MHZ19.h>

// ==========================================
// 1. KONFIGURASI WIFI & MQTT
// ==========================================
const char* ssid        = "Anri";
const char* password    = "12345678";
const char* mqtt_server = "192.168.18.82"; // IP Server Python Anda
const int   mqtt_port   = 1883;

// Topik MQTT (Harus sama dengan config.py di server)
const char* TOPIC_SENSOR   = "agraric/kumbung1/sensors";
const char* TOPIC_AKTUATOR = "agraric/kumbung1/actuators";

// ==========================================
// 2. PIN HARDWARE & SENSOR
// ==========================================
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

#define RX_PIN 16 
#define TX_PIN 17 
MHZ19 myMHZ19;

// Aktuator
const int PIN_FAN    = 18; // Mosfet Kipas (12V)
const int PIN_MIST   = 19; // Mosfet Mist Maker (5V)
const int PIN_HEATER = 25; // Relay Lampu Pijar (Ch 1)

// Konfigurasi PWM (ESP32 Core 3.0+)
const int pwmFreq = 1000;
const int pwmRes  = 8;

// Timing
unsigned long lastMsg = 0;

WiFiClient espClient;
PubSubClient client(espClient);

// ==========================================
// 3. FUNGSI KONEKSI
// ==========================================
void setup_wifi() {
  delay(10);
  Serial.print("\nConnecting to "); Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: "); Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32_Kumbung_Anri")) {
      Serial.println("connected");
      client.subscribe(TOPIC_AKTUATOR);
    } else {
      Serial.print("failed, rc="); Serial.print(client.state());
      delay(5000);
    }
  }
}

// ==========================================
// 4. CALLBACK: TERIMA PERINTAH DARI SERVER
// ==========================================
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived ["); Serial.print(topic); Serial.print("] ");
  
  StaticJsonDocument<256> doc;
  deserializeJson(doc, payload, length);

  // Ambil instruksi dari JSON server
  int kipas_pwm      = doc["kipas_pwm"];
  const char* mist   = doc["mist_maker"];      // "ON" atau "OFF"
  const char* heater = doc["lampu_pemanas"];   // "ON" atau "OFF"

  // Eksekusi Kipas (PWM)
  ledcWrite(PIN_FAN, kipas_pwm);

  // Eksekusi Mist Maker (Sesuai main.py, ini ON/OFF via Mosfet)
  if (String(mist) == "ON") ledcWrite(PIN_MIST, 255);
  else ledcWrite(PIN_MIST, 0);

  // Eksekusi Heater (Relay Active-LOW)
  if (String(heater) == "ON") digitalWrite(PIN_HEATER, LOW); // ON
  else digitalWrite(PIN_HEATER, HIGH); // OFF

  Serial.printf("Execute -> Fan: %d, Mist: %s, Heater: %s\n", kipas_pwm, mist, heater);
}

// ==========================================
// 5. SETUP & LOOP
// ==========================================
void setup() {
  Serial.begin(115200);
  
  // Setup Sensor
  dht.begin();
  Serial2.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN);
  myMHZ19.begin(Serial2);
  myMHZ19.autoCalibration(false);

  // Setup Aktuator
  ledcAttach(PIN_FAN, pwmFreq, pwmRes);
  ledcAttach(PIN_MIST, pwmFreq, pwmRes);
  pinMode(PIN_HEATER, OUTPUT);
  digitalWrite(PIN_HEATER, HIGH); // Mati di awal

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  unsigned long now = millis();
  // Kirim data sensor setiap 5 detik
  if (now - lastMsg > 5000) {
    lastMsg = now;

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int co2 = myMHZ19.getCO2();

    if (!isnan(t) && !isnan(h)) {
      StaticJsonDocument<256> doc;
      doc["suhu"]             = t;
      doc["kelembapan_udara"] = h;
      doc["kelembapan_media"] = 0;   // Placeholder (Sensor dicopot)
      doc["kadar_co2"]        = co2;
      doc["kadar_ph"]         = 0.0; // Placeholder (Sensor dicopot)

      char buffer[256];
      serializeJson(doc, buffer);
      client.publish(TOPIC_SENSOR, buffer);
      
      Serial.print("Sent to Server: "); Serial.println(buffer);
    }
  }
}