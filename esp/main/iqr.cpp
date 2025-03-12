#include "Arduino.h"
#include "iqr.h"
#include "FS.h"
#include "LittleFS.h"
#include <ArduinoJson.h>
#include <algorithm>

#define MAX_VALUES 86400 // TODO: Change number of values for iqr calculation

const float DEFAULT_LOWER_THRESHOLD = 60.0;
const float DEFAULT_UPPER_THRESHOLD = 100.0;

float calculatePercentile(float *values, int size, float percentile) {
    if (size == 0)
        return 0.0;

    std::sort(values, values + size);
    float index = percentile * (size - 1);
    int lowerIndex = floor(index);
    int upperIndex = ceil(index);

    if (lowerIndex == upperIndex) {
        return values[lowerIndex];
    } else {
        float lowerValue = values[lowerIndex];
        float upperValue = values[upperIndex];
        return lowerValue + (upperValue - lowerValue) * (index - lowerIndex);
    }
}

void appendToBinaryFile(String filePath, float value) {
    File file = LittleFS.open(filePath, "a");
    if (file) {
        file.write((uint8_t *)&value, sizeof(value));
        file.close();
    } else {
        Serial.println("Failed to open binary file for writing!");
    }
}

void readBinaryFile(String filePath, float *buffer, int maxValues) {
    File file = LittleFS.open(filePath, "r");
    if (file) {
        int numValues = file.size() / sizeof(float);
        int startIndex = max(0, numValues - maxValues);
        file.seek(startIndex * sizeof(float));
        for (int i = 0; i < maxValues && file.available(); i++) {
            file.read((uint8_t *)&buffer[i], sizeof(float));
        }
        file.close();
    } else {
        Serial.println("Failed to open binary file for reading!");
    }
}

void updateJsonFile(String filePath, float lowerBound, float upperBound, bool initialCalculationDone) {
    StaticJsonDocument<256> jsonDoc;
    jsonDoc["lowerBound"] = lowerBound;
    jsonDoc["upperBound"] = upperBound;
    jsonDoc["initialCalculationDone"] = initialCalculationDone;

    File file = LittleFS.open(filePath, "w");
    if (file) {
        serializeJson(jsonDoc, file);
        file.close();
    } else {
        Serial.println("Failed to write JSON file!");
    }
}

bool detectAnomaly(String patientId, String sensorType, float sensorValue) {
    String binaryFilePath = "/" + sensorType + "-" + patientId + ".bin";
    String jsonFilePath = "/" + sensorType + "-" + patientId + ".json";

    if (!LittleFS.begin(true)) {
        Serial.println("Failed to mount LittleFS!");
        return false;
    }

    bool initialCalculationDone = false;
    float lowerBound = 0.0;
    float upperBound = 0.0;

    if (LittleFS.exists(jsonFilePath)) {
        File file = LittleFS.open(jsonFilePath, "r");
        if (file) {
            StaticJsonDocument<256> jsonDoc;
            DeserializationError error = deserializeJson(jsonDoc, file);
            file.close();

            if (!error) {
                lowerBound = jsonDoc["lowerBound"];
                upperBound = jsonDoc["upperBound"];
                initialCalculationDone = jsonDoc["initialCalculationDone"];
            }
        }
    }

    if (!initialCalculationDone) {
        appendToBinaryFile(binaryFilePath, sensorValue);

        float values[MAX_VALUES];
        readBinaryFile(binaryFilePath, values, MAX_VALUES);

        int numValues = 0;
        for (int i = 0; i < MAX_VALUES; i++) {
            if (values[i] != 0.0)
                numValues++;
        }

        if (numValues >= MAX_VALUES) {
            float q1 = calculatePercentile(values, MAX_VALUES, 0.25);
            float q3 = calculatePercentile(values, MAX_VALUES, 0.75);
            float iqr = q3 - q1;
            lowerBound = q1 - 1.5 * iqr;
            upperBound = q3 + 1.5 * iqr;
            updateJsonFile(jsonFilePath, lowerBound, upperBound, true);

            // TODO: Add logic here to send to cloud for analysis

            LittleFS.remove(binaryFilePath);
        }
    }

    if (!initialCalculationDone) {
        return (sensorValue < DEFAULT_LOWER_THRESHOLD || sensorValue > DEFAULT_UPPER_THRESHOLD);
    } else {
        return (sensorValue < lowerBound || sensorValue > upperBound);
    }
}