# Anomaly Detection on ESP32

## Overview
This project detects anomalies in sensor data using different algorithms. The ESP32 microcontroller connects to a Wi-Fi network, receives sensor data from multiple clients, and processes the data to detect anomalies. Detected anomalies are sent to a remote Ubuntu server for further processing.

## Supported Anomaly Detection Algorithms
1. **Percentile-based detection**
2. **Rolling average-based detection**
3. **IQR-based detection**

## Code Structure
- **percentile.cpp** - Implements percentile-based detection.
- **rolling_avg.cpp** - Implements rolling average-based detection.
- **iqr.cpp** - Implements IQR-based detection.
- **main.cpp** - Handles Wi-Fi connection, data reception, and anomaly detection.

## Switching Between Algorithms
Modify `anomalies_detection.h` to include the desired algorithm:

```cpp
// #include "percentile.h"
#include "rolling_avg.h"
// #include "iqr.h"
```

## Dependencies
- **ArduinoJson**: For handling JSON data.
- **LittleFS**: For file system operations on the ESP32.

## Setup
1. Update the `ssid` and `password` variables in `main.cpp` with your Wi-Fi credentials.
2. Update the `ubuntuServerIP` and `ubuntuServerPort` variables with your Ubuntu server’s details.

## Usage
1. Upload the code to your ESP32.
2. Connect sensor clients to the ESP32’s TCP server on port `8080`.
3. The ESP32 processes sensor data and detects anomalies using the selected algorithm.
4. Detected anomalies are sent to the Ubuntu server.

## Example Sensor Data Format
```
<PatientID>#<SensorType>:<SensorValue>
```
**Example:**
```
123#temperature:98.6
```
