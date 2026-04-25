#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- KONFIGURASI WIFI & MQTT ---
const char* ssid        = "RumahKecil";
const char* password    = "marpaung57";
const char* mqtt_server = "168.144.136.41"; // IP VPS Anda
const int   mqtt_port   = 1883;

// --- IDENTITAS PERANGKAT ---
const char* clientID      = "ESP32_Kumbung_01";
const char* topic_sensor  = "agraric/kumbung1/sensors";
const char* topic_control = "agraric/kumbung1/actuators";

// --- PIN ACTUATOR (Sesuaikan dengan wiring Anda) ---
const int PIN_KIPAS  = 18; // PWM
const int PIN_MIST   = 19; // Relay
const int PIN_HEATER = 21; // Relay
const int PIN_POMPA  = 22; // Relay

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

// FUNGSI MENERIMA PERINTAH DARI VPS
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Instruksi masuk [");
  Serial.print(topic);
  Serial.print("]: ");
  
  StaticJsonDocument<256> doc;
  deserializeJson(doc, payload, length);

  // Parsing Kontrol dari Server
  if (doc.containsKey("kipas_pwm")) {
    int pwmValue = doc["kipas_pwm"];
    analogWrite(PIN_KIPAS, pwmValue);
    Serial.printf("Kipas -> %d | ", pwmValue);
  }
  
  if (doc.containsKey("mist_maker")) {
    const char* mistStatus = doc["mist_maker"];
    digitalWrite(PIN_MIST, (strcmp(mistStatus, "ON") == 0) ? LOW : HIGH); // LOW aktif jika pakai Relay Module
    Serial.printf("Mist -> %s | ", mistStatus);
  }

  if (doc.containsKey("heater")) {
    const char* heaterStatus = doc["heater"];
    digitalWrite(PIN_HEATER, (strcmp(heaterStatus, "ON") == 0) ? LOW : HIGH);
    Serial.printf("Heater -> %s\n", heaterStatus);
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(clientID)) {
      Serial.println("Connected to VPS!");
      client.subscribe(topic_control); // Dengerin perintah dari server
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Setup Pin Mode
  pinMode(PIN_KIPAS, OUTPUT);
  pinMode(PIN_MIST, OUTPUT);
  pinMode(PIN_HEATER, OUTPUT);
  pinMode(PIN_POMPA, OUTPUT);

  // Matikan semua aktuator saat startup
  digitalWrite(PIN_MIST, HIGH);
  digitalWrite(PIN_HEATER, HIGH);
  digitalWrite(PIN_POMPA, HIGH);
  analogWrite(PIN_KIPAS, 0);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  // Kirim data sensor setiap 5 detik
  if (now - lastMsg > 5000) {
    lastMsg = now;

    // SIMULASI PEMBACAAN SENSOR (Ganti dengan fungsi sensor asli Anda: dht.read dsb)
    float suhu = 28.0 + (random(0, 100) / 10.0);
    float hum  = 80.0 + (random(0, 100) / 10.0);
    int co2    = 400 + random(0, 1000);

    // Bungkus ke JSON
    StaticJsonDocument<200> doc;
    doc["suhu"] = suhu;
    doc["kelembapan_udara"] = hum;
    doc["kadar_co2"] = co2;

    char buffer[256];
    serializeJson(doc, buffer);

    // Kirim ke VPS
    client.publish(topic_sensor, buffer);
    Serial.println("Data Terkirim: " + String(buffer));
  }
}