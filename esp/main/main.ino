#include <WiFi.h>

// Change to desired algorithm
#include "percentiles.h"
// #include "rolling_avg.h"
// #include "iqr.h"

#include "FS.h"
#include "LittleFS.h"

const char *ssid = "TestWifi"; // TODO: Change Wi-Fi SSID
const char *password = "12345678"; // TODO: Change Wi-Fi password

WiFiServer espServer(8080);
WiFiClient clients[10]; // Supports up to 10 concurrent connections

WiFiClient ubuntuClient;
const char *ubuntuServerIP = "123.456.789.0"; // Change server ip
const int ubuntuServerPort = 9090;

void setup() {
    Serial.begin(115200);

    // Connect to Wi-Fi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to Wi-Fi...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n✅ Wi-Fi connected!");

    Serial.println("\n📡 ESP32 IP Address:");
    Serial.println(WiFi.localIP());

    if (!LittleFS.begin(true)) {
        Serial.println("LittleFS Mount Failed");
        return;
    }

    espServer.begin();
    Serial.println("✅ ESP32 TCP Server started on port 8080");

    connectToUbuntu();
}

void loop() {
    // Accept new clients
    for (int i = 0; i < 5; i++) {
        if (!clients[i] || !clients[i].connected()) {
            clients[i] = espServer.available();
            if (clients[i]) {
                Serial.println("✅ New Python client connected!");
            }
        }
    }

    // Handle incoming sensor data
    for (int i = 0; i < 5; i++) {
        if (clients[i] && clients[i].connected() && clients[i].available()) {
            String receivedData = clients[i].readStringUntil('\n');
            receivedData.trim();

            Serial.print("📩 Received: ");
            Serial.println(receivedData);

            // Process the data and detect anomalies
            checkAnomalies(receivedData);

            // Send ACK to client
            clients[i].println("OK");
        }
    }

    // Keep Ubuntu connection alive
    if (!ubuntuClient.connected()) {
        connectToUbuntu();
    }
}

void checkAnomalies(String sensorData) {
    int patientIdIndex = sensorData.indexOf("#");
    int sensorTypeIndex = sensorData.indexOf(":");

    if (patientIdIndex != -1 && sensorTypeIndex != -1) {
        String patientIdStr = sensorData.substring(0, patientIdIndex);
        String sensorType = sensorData.substring(patientIdIndex + 1, sensorTypeIndex);
        String sensorValueStr = sensorData.substring(sensorTypeIndex + 1);
        float sensorValue = sensorValueStr.toFloat();

        Serial.println("\nExtracted Data: Patient ID: " + patientIdStr + " | Sensor: " + sensorType + " | Value: " + sensorValue);

        bool anomalyDetected = detectAnomaly(patientIdStr, sensorType, sensorValue);

        if (anomalyDetected) {
            Serial.println("⚠️ Anomaly detected! Sending alert to Ubuntu...");
            sendToUbuntu(sensorType, sensorValueStr);
        }
    }
}

void connectToUbuntu() {
    static unsigned long lastAttempt = 0;
    unsigned long now = millis();

    if (now - lastAttempt < 5000) {
        return;
    }

    lastAttempt = now;
    Serial.print("🔄 Connecting to Ubuntu Server... ");
    if (ubuntuClient.connect(ubuntuServerIP, ubuntuServerPort)) {
        Serial.println("✅ Connected to Ubuntu Server!");
    } else {
        Serial.println("❌ Connection failed! Retrying...");
    }
}

void sendToUbuntu(String sensorType, String sensorValue) {
    if (ubuntuClient.connected()) {
        String message = sensorType + " anomaly: " + sensorValue;
        ubuntuClient.println(message);
        Serial.println("✅ Sent anomaly to Ubuntu: " + message);
    } else {
        Serial.println("❌ Ubuntu Server not connected. Retrying...");
        connectToUbuntu();
    }
}
