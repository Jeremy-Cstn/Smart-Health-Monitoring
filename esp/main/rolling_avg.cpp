#include "Arduino.h"
#include "FS.h"
#include "LittleFS.h"
#include <ArduinoJson.h>

#define MAX_VALUES 500 // TODO: Change number of values for rolling average

// Function to calculate the mean of an array
float calculateMean(JsonArray values) {
    float sum = 0.0;
    for (float value : values) {
        sum += value;
    }
    return sum / values.size();
}

// Function to calculate the standard deviation of an array
float calculateStdDev(JsonArray values, float mean) {
    float variance = 0.0;
    for (float value : values) {
        variance += pow(value - mean, 2);
    }
    return sqrt(variance / values.size());
}

bool detectAnomaly(String patientId, String sensorType, float sensorValue) {
    String filePath = "/" + sensorType + "-" + patientId + ".json";

    // Initialize LittleFS
    if (!LittleFS.begin(true)) {
        Serial.println("Failed to mount LittleFS!");
        return false;
    }

    // Create a JSON document
    StaticJsonDocument<1024> jsonDoc;

    // Check if file exists
    if (LittleFS.exists(filePath)) {
        // Open file for reading
        File file = LittleFS.open(filePath, "r");
        if (file) {
            DeserializationError error = deserializeJson(jsonDoc, file);
            file.close();

            if (error) {
                Serial.println("Failed to parse JSON file!");
                return false;
            }
        }
    }

    // Read existing values
    JsonArray values = jsonDoc["values"].as<JsonArray>();

    // Add the new sensor value
    values.add(sensorValue);

    // Ensure only the last MAX_VALUES are stored
    while (values.size() > MAX_VALUES) {
        values.remove(0); // Remove oldest value

        // TODO: Add logic here to send to cloud for analysis

    }

    // Update JSON with new values
    jsonDoc["values"] = values;

    // Calculate the rolling average and standard deviation
    float rollingAvg = calculateMean(values);
    float stdDev = calculateStdDev(values, rollingAvg);

    // Update JSON with rolling average and standard deviation
    jsonDoc["average"] = rollingAvg;
    jsonDoc["stdDev"] = stdDev;

    // Save the updated JSON back to the file
    File file = LittleFS.open(filePath, "w");
    if (file) {
        serializeJson(jsonDoc, file);
        file.close();
    } else {
        Serial.println("Failed to write JSON file!");
        return false;
    }

    // Define thresholds as average +/- 2 standard deviations
    float lowerThreshold = rollingAvg - 2 * stdDev;
    float upperThreshold = rollingAvg + 2 * stdDev;

    // Detect anomaly
    bool isAnomaly = (sensorValue < lowerThreshold || sensorValue > upperThreshold);

    return isAnomaly;
}