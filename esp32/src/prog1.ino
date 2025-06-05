// Bibliotecas para WiFi, MQTT, Sensores e Display
#include <WiFi.h>
#include <PubSubClient.h> // Será configurado com buffer maior abaixo
#include <DHT.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "time.h" 

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1 

const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = -3 * 3600; 
const int   daylightOffset_sec = 0;    

const char* ssid = "Wokwi-GUEST"; 
const char* password = "";

const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP32GuardiaoNatural_Python_99"; 
const char* mqtt_topic = "guardiao_natural/sensor_data"; // Mantendo o tópico de teste simplificado

const int trigPin = 5;  const int echoPin = 18; const int ldrPin = 34;  
#define DHTPIN 4        
#define DHTTYPE DHT22   
const int mq2Pin = 35;  
const int ledPin = 2;   

const int ULTRASONIC_MAX_SENSOR_DISTANCE_CM = 200; const int ULTRASONIC_MIN_SENSOR_DISTANCE_CM = 0;
const int WATER_LEVEL_MIN_PERCENT = 0; const int WATER_LEVEL_MAX_PERCENT = 100;
const int LDR_MAX_ANALOG_READING = 4095; const int LDR_MIN_ANALOG_READING = 0;
const int RAINFALL_MIN_PERCENT = 0; const int RAINFALL_MAX_PERCENT = 100;
const int MQ2_MAX_ANALOG_READING = 4095; const int MQ2_MIN_ANALOG_READING = 0;
const int SMOKE_MIN_PERCENT = 0; const int SMOKE_MAX_PERCENT = 100;
const int ALERT_WATER_LEVEL_THRESHOLD = 70; const int ALERT_RAINFALL_THRESHOLD = 80;
const float ALERT_TEMPERATURE_THRESHOLD = 35.0; const int ALERT_SMOKE_THRESHOLD = 60;

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient client(espClient); // Cliente é criado aqui

long duration; int distanceCm; int rawLDRValue; int rawMQ2Value;
int waterLevel; int rainfallIntensity; float temperatura; float umidade;     
int smokeConcentration; String currentDeviceTimestamp = "N/A"; bool dhtErrorFlag = false;
unsigned long lastMsg = 0; const int MESSAGE_INTERVAL = 5000;

void syncTimeNTP() { /* ... (igual à versão anterior) ... */ 
  display.clearDisplay(); display.setTextSize(1); display.setTextColor(SSD1306_WHITE); display.setCursor(0, 0);
  display.println("Sincronizando NTP..."); display.display(); Serial.println("Sincronizando hora com servidor NTP...");
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer); struct tm timeinfo;
  if (!getLocalTime(&timeinfo, 10000)) { Serial.println("Falha ao obter hora do NTP."); display.println("Falha NTP!"); currentDeviceTimestamp = "NTP_SYNC_FAILED";
  } else { Serial.println("Hora NTP sincronizada."); Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S"); display.println("NTP Sincronizado!"); 
    char buffer[30]; strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo); currentDeviceTimestamp = String(buffer); display.println(currentDeviceTimestamp);
  } display.display(); delay(2000);
}
void setup_wifi() { /* ... (igual à versão anterior) ... */ 
  delay(10); display.clearDisplay(); display.setTextSize(1); display.setTextColor(SSD1306_WHITE); display.setCursor(0,0);
  display.println("Conectando WiFi..."); display.display(); Serial.print("Conectando a "); Serial.println(ssid);
  WiFi.begin(ssid, password); int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) { delay(500); Serial.print("."); display.print("."); display.display(); attempts++; }
  display.clearDisplay(); display.setCursor(0,0);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!"); Serial.print("Endereco IP: "); Serial.println(WiFi.localIP());
    display.println("WiFi Conectado!"); display.println(WiFi.localIP()); display.display(); delay(1000); syncTimeNTP();
  } else { Serial.println("\nFalha ao conectar WiFi."); display.println("Falha WiFi!"); display.println("Verifique rede."); }
  display.display(); delay(2000);
}
void reconnect_mqtt() { 
  while (!client.connected()) {
    Serial.print("Tentando conexao MQTT..."); display.clearDisplay(); display.setTextSize(1); display.setTextColor(SSD1306_WHITE); display.setCursor(0,0);
    display.println("Conectando MQTT..."); display.display();
    if (client.connect(mqtt_client_id)) { Serial.println("conectado!"); display.println("MQTT Conectado!"); display.display(); delay(1000);
    } else { Serial.print("falhou, rc="); Serial.print(client.state()); Serial.println(" tentando novamente em 5 segundos");
      display.println("Falha MQTT!"); display.println("Tentando de novo..."); display.display(); delay(5000);
    }
  }
}

void setup() { 
  Serial.begin(115200); Wire.begin();
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { Serial.println(F("Falha SSD1306")); for (;;); }
  display.display(); delay(1000); display.clearDisplay(); display.setTextSize(1); display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0); display.println("Guardiao Natural"); display.println("Iniciando..."); display.display(); delay(1000);
  pinMode(trigPin, OUTPUT); pinMode(echoPin, INPUT); dht.begin(); pinMode(ledPin, OUTPUT);
  
  client.setServer(mqtt_server, mqtt_port);
  // #######################################################################
  // ## AUMENTAR O BUFFER MQTT AQUI ##
  // #######################################################################
  client.setBufferSize(512); // Tenta definir o buffer para 512 bytes
  // #######################################################################

  setup_wifi(); // Conecta WiFi e depois o MQTT é conectado em reconnect_mqtt se necessário
}

void loop() {
  if (!client.connected()) { reconnect_mqtt(); }
  client.loop(); // Essencial para manter a conexão e processar callbacks (embora este cliente não use callbacks de recebimento)
  unsigned long now = millis();
  if (now - lastMsg > MESSAGE_INTERVAL) {
    lastMsg = now;
    // ... (lógica de leitura dos sensores igual à versão anterior) ...
    digitalWrite(trigPin, LOW); delayMicroseconds(2); digitalWrite(trigPin, HIGH); delayMicroseconds(10); digitalWrite(trigPin, LOW);
    duration = pulseIn(echoPin, HIGH); distanceCm = duration * 0.034 / 2;
    waterLevel = map(distanceCm, ULTRASONIC_MAX_SENSOR_DISTANCE_CM, ULTRASONIC_MIN_SENSOR_DISTANCE_CM, WATER_LEVEL_MIN_PERCENT, WATER_LEVEL_MAX_PERCENT);
    if (waterLevel < WATER_LEVEL_MIN_PERCENT) waterLevel = WATER_LEVEL_MIN_PERCENT; if (waterLevel > WATER_LEVEL_MAX_PERCENT) waterLevel = WATER_LEVEL_MAX_PERCENT;
    rawLDRValue = analogRead(ldrPin);
    rainfallIntensity = map(rawLDRValue, LDR_MAX_ANALOG_READING, LDR_MIN_ANALOG_READING, RAINFALL_MIN_PERCENT, RAINFALL_MAX_PERCENT);
    if (rainfallIntensity < RAINFALL_MIN_PERCENT) rainfallIntensity = RAINFALL_MIN_PERCENT; if (rainfallIntensity > RAINFALL_MAX_PERCENT) rainfallIntensity = RAINFALL_MAX_PERCENT;
    temperatura = dht.readTemperature(); umidade = dht.readHumidity(); dhtErrorFlag = false;
    if (isnan(temperatura) || isnan(umidade)) { Serial.println("Falha DHT22!"); dhtErrorFlag = true; }
    rawMQ2Value = analogRead(mq2Pin);
    smokeConcentration = map(rawMQ2Value, MQ2_MIN_ANALOG_READING, MQ2_MAX_ANALOG_READING, SMOKE_MIN_PERCENT, SMOKE_MAX_PERCENT);
    if (smokeConcentration < SMOKE_MIN_PERCENT) smokeConcentration = SMOKE_MIN_PERCENT; if (smokeConcentration > SMOKE_MAX_PERCENT) smokeConcentration = SMOKE_MAX_PERCENT;

    StaticJsonDocument<384> doc;
    doc["device_id"] = mqtt_client_id;
    doc["nivel_de_agua"] = waterLevel; doc["intensidade_de_chuva"] = rainfallIntensity;
    if (dhtErrorFlag) { doc["temperatura"] = (char*)nullptr; doc["umidade"] = (char*)nullptr; }
    else { doc["temperatura"] = temperatura; doc["umidade"] = umidade; }
    doc["concentracao_de_fumaca"] = smokeConcentration; doc["timestamp_device"] = currentDeviceTimestamp;
    doc["raw_distance_cm"] = distanceCm; doc["raw_ldr_value"] = rawLDRValue; doc["raw_mq2_value"] = rawMQ2Value;
    String payload; serializeJson(doc, payload);

    Serial.print("DEBUG WOKWI: Publicando no topico -> '"); Serial.print(mqtt_topic); Serial.println("'");
    Serial.print("DEBUG WOKWI: Comprimento do topico -> "); Serial.println(String(mqtt_topic).length());
    Serial.print("Publicando mensagem: "); Serial.println(payload);
    
    bool published = client.publish(mqtt_topic, payload.c_str());
    if (published) {
      Serial.println("DEBUG WOKWI: Publicacao MQTT -> SUCESSO (cliente tentou enviar)");
    } else {
      Serial.print("DEBUG WOKWI: Publicacao MQTT -> FALHA (cliente nao enviou). Estado do cliente: ");
      Serial.println(client.state()); // Checa o estado ATUAL do cliente
      // Se o estado for 0 (MQTT_CONNECTED), a falha pode ser buffer cheio.
      // Se for outro valor, pode ter desconectado.
      // Tentar reconectar explicitamente se o estado não for conectado:
      // if (!client.connected()) {
      //   Serial.println("DEBUG WOKWI: Cliente desconectado antes do publish, tentando reconectar...");
      //   reconnect_mqtt(); // Tenta reconectar e o próximo ciclo tentará publicar de novo.
      // }
    }

    // ... (lógica do LED e Display OLED igual à versão anterior) ...
    if (waterLevel > ALERT_WATER_LEVEL_THRESHOLD || rainfallIntensity > ALERT_RAINFALL_THRESHOLD || (!dhtErrorFlag && temperatura > ALERT_TEMPERATURE_THRESHOLD) || smokeConcentration > ALERT_SMOKE_THRESHOLD) {
      digitalWrite(ledPin, HIGH); } else { digitalWrite(ledPin, LOW); }
    display.clearDisplay(); display.setCursor(0,0); display.setTextSize(1); display.setTextColor(SSD1306_WHITE);
    display.println("--- Guardiao Natural ---"); display.print("Agua: "); display.print(waterLevel); display.println("%");
    display.print("Chuva: "); display.print(rainfallIntensity); display.println("%");
    display.print("Temp: "); if (dhtErrorFlag) display.print("-- C"); else { display.print(temperatura, 1); display.print(" C");} display.println();
    display.print("Umid: "); if (dhtErrorFlag) display.print("-- %"); else { display.print(umidade, 0); display.print(" %");} display.println();
    display.print("Fumaca: "); display.print(smokeConcentration); display.println("%");
    display.setTextSize(2); display.setCursor(0,50);

    
    if (waterLevel > ALERT_WATER_LEVEL_THRESHOLD || rainfallIntensity > ALERT_RAINFALL_THRESHOLD) { display.println("ALERTA ENCHENTE!"); }
    else if ((!dhtErrorFlag && temperatura > ALERT_TEMPERATURE_THRESHOLD) || smokeConcentration > ALERT_SMOKE_THRESHOLD) { display.println("ALERTA INCENDIO!"); }
    else if (dhtErrorFlag && smokeConcentration <= ALERT_SMOKE_THRESHOLD && waterLevel <= ALERT_WATER_LEVEL_THRESHOLD && rainfallIntensity <= ALERT_RAINFALL_THRESHOLD) { display.println("DHT FALHOU!"); }
    else { display.println("Status: OK"); }
    display.display();
  }
}