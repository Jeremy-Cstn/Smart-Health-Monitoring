import os
import re
import time
import socket
import threading
import pandas as pd

# ESP32 Wi-Fi IP and TCP Port
ESP32_IP = "192.168.38.1"  # TODO: Change to match your ESP32
ESP32_PORT = 8080  # TODO: Ensure this matches the ESP32's listening port
SENSOR_INTERVAL = 2 # TODO: Change to the desired sensor sampling rate in seconds

DATA_FOLDER = "./data"  # Directory where patient CSV files are stored

def send_data_thread(file_path, interval=SENSOR_INTERVAL):
    """Thread function to send a patient's data over TCP."""
    df = pd.read_csv(file_path)
    match = re.match(r"(.+)-(\d+)\.csv", os.path.basename(file_path))
    if match:
        sensor_type = match.group(1)
        patient_id = match.group(2)
    else:
        raise NameError("Sensor name or patient ID could not be recognized")

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ESP32_IP, ESP32_PORT))
                print(f"✅ Connected to ESP32 for Patient {patient_id} at {ESP32_IP}:{ESP32_PORT}")

                for _, row in df.iterrows():
                    sensor_value = row["heart_rate"] # TODO: Change for specific csv

                    message = f"{patient_id}#{sensor_type}:{sensor_value}\n"
                    print(f"📤 Sending {sensor_type} from Patient {patient_id}: {sensor_value}")

                    sock.sendall(message.encode())

                    try:
                        response = sock.recv(1024).decode()
                        print(f"✅ ESP32 Response: {response}")
                    except socket.error as e:
                        print(f"⚠️ Socket error while receiving: {e}")
                        break  # Stop sending if connection is lost

                    time.sleep(interval)

        except socket.error as e:
            print(f"❌ Connection error for Patient {patient_id}: {e}")
            time.sleep(5)  # Retry after a delay


def main():
    """Main function to start sending patient data using parallel threads."""
    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

    patient_files = {f.split(".")[0]: os.path.join(DATA_FOLDER, f) for f in csv_files}

    threads = []
    for patient_id, file_path in patient_files.items():
        thread = threading.Thread(target=send_data_thread, args=(file_path), daemon=True)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
