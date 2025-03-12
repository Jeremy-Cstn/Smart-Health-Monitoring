import socket
import threading
import csv
import os

# Server Configuration
HOST = "0.0.0.0"  # Listen on all network interfaces
PORT = 9090  # Must match ESP32C3's `ubuntuServerPort`

# Log file path
LOG_FILE = "anomalies_log.csv"

# Ensure log file exists and has headers
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Sensor Type", "Anomaly Value"])  # Column headers

def handle_client(client_socket, client_address):
    """Handles incoming messages from ESP32C3"""
    print(f"✅ Connected to ESP32C3 at {client_address}")

    try:
        while True:
            message = client_socket.recv(1024).decode().strip()
            if not message:
                print(f"❌ ESP32C3 {client_address} disconnected.")
                break  # Exit loop if client disconnects

            print(f"📩 Received anomaly: {message}")

            # Parse anomaly message
            if "anomaly" in message:
                parts = message.split(" ")
                if len(parts) >= 3:
                    sensor_type = parts[0]
                    sensor_value = parts[-1]

                    # Log anomaly to CSV file
                    with open(LOG_FILE, mode="a", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow([sensor_type, sensor_value])

                    print(f"✅ Logged anomaly: {sensor_type} = {sensor_value}")

            # Send acknowledgment back to ESP32C3
            client_socket.sendall(b"ACK\n")

    except Exception as e:
        print(f"⚠️ Error: {e}")

    finally:
        client_socket.close()
        print(f"❌ Disconnected from ESP32C3 {client_address}")

def start_server():
    """Starts the Ubuntu TCP server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"🚀 Ubuntu Server is running on port {PORT}...")

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True)
        client_thread.start()

if __name__ == "__main__":
    start_server()
