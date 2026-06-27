#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// Wi-Fi
const char* WIFI_SSID = "Jungle";
const char* WIFI_PASSWORD = "12345678";

// Backend FastAPI
const char* API_URL =
    "http://192.168.0.100:8000/esp32/reading";

// Identificação do dispositivo
const char* DEVICE_ID =
    "esp32-camara-fria-01";

// Enviar a cada 10 segundos
const unsigned long SEND_INTERVAL_MS = 10000;
unsigned long lastSend = 0;

void connectWiFi() {
    Serial.print("Conectando ao WiFi");

    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD
    );

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

bool sendReading(
    float temperature,
    float humidity
) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    HTTPClient http;

    http.begin(API_URL);

    http.addHeader(
        "Content-Type",
        "application/json"
    );

    String payload = "{";
    payload += "\"device_id\":\"";
    payload += DEVICE_ID;
    payload += "\",";
    payload += "\"temperature_internal\":";
    payload += String(temperature, 2);
    payload += ",";
    payload += "\"humidity_internal\":";
    payload += String(humidity, 2);
    payload += "}";

    Serial.println("Payload enviado:");
    Serial.println(payload);

    int httpCode =
        http.POST(payload);

    Serial.print("HTTP Code: ");
    Serial.println(httpCode);

    if (httpCode > 0) {
        String response =
            http.getString();

        Serial.println("Resposta:");
        Serial.println(response);
    }

    http.end();

    return (
        httpCode >= 200 &&
        httpCode < 300
    );
}

void setup() {
    Serial.begin(115200);

    dht.begin();

    connectWiFi();
}

void loop() {

    if (
        millis() - lastSend >=
        SEND_INTERVAL_MS
    ) {
        lastSend = millis();

        float humidity =
            dht.readHumidity();

        float temperature =
            dht.readTemperature();

        if (
            isnan(temperature) ||
            isnan(humidity)
        ) {
            Serial.println(
                "Falha na leitura do DHT22"
            );
            return;
        }

        Serial.print("Temperatura: ");
        Serial.print(temperature);
        Serial.println(" °C");

        Serial.print("Umidade: ");
        Serial.print(humidity);
        Serial.println(" %");

        sendReading(
            temperature,
            humidity
        );
    }

    // Reconexão simples
    if (
        WiFi.status() !=
        WL_CONNECTED
    ) {
        connectWiFi();
    }

    delay(100);
}