# Smart-Health-Monitoring
An Adaptive Thresholding and Fog-enabled Remote Healthcare Monitoring System

the code from the esp32ce can be found in the directory esp/main (it can be run on every arduino)
code for simulating sensor data is in sensor-sim (main_simulation#main)
code for ubuntu server in server (server#start_server)
code for benchmarking in benchmarking (benchmarking#run_tests)

/data/ used for simulating data to edge device (link to /data/README.md)
benchmarking/data/ used for benchmarking different algorithms and sampling rates (link to /data/README.md)




# Smart-Health-Monitoring

An Adaptive Thresholding and Fog-enabled Remote Healthcare Monitoring System.

## Project Structure

- **ESP32 Code**: Located in `esp/main`. This code can be run on any Arduino-compatible device [`/esp/README.md`](esp/README.md).
- **Sensor Simulation**: Found in `sensor-sim` (`main_simulation#main`), responsible for generating simulated sensor data.
- **Ubuntu Server Code**: Stored in `server` (`server#start_server`), handling data processing and communication.
- **Benchmarking**: Code for performance evaluation is in `benchmarking` (`benchmarking#run_tests`) [`/benchmarking/data/README.md`](benchmarking/data/README.md).
- **Sensor Data**: The `/data/` directory is used for simulating data to the edge device. More details can be found in the [`/data/README.md`](data/README.md).

## Additional Notes
Ensure all components are properly configured and connected to enable real-time monitoring and data processing.

For further details on specific components, refer to their respective README files within each directory.

