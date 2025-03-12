# Sensor Data Directory

This directory is used for simulating and sending sensor data to the ESP.

## File Format
- All data files should be in CSV format.
- Each file should be named using the following convention:
  ```
  <sensor_type>-<patient_id>.csv
  ```
  Example:
  ```
  heart_rate-1234.csv
  temperature-5678.csv
  ```

## Guidelines
- Each patient should have their own CSV file per sensor type.
- Ensure that data is formatted consistently for accurate processing.

This directory is essential for simulating and transmitting sensor data.

