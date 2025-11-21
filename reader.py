import serial
import time
import json
import os
from datetime import datetime

LATEST_FILE = "data/latest.json"
HISTORY_FILE = "data/history.csv"

# ----------------------------------------
# Find Arduino Serial Port Automatically
# ----------------------------------------
def find_arduino():
    for port in ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0", "/dev/ttyUSB1"]:
        if os.path.exists(port):
            return port
    return None

# ----------------------------------------
# Ensure data directory exists
# ----------------------------------------
os.makedirs("data", exist_ok=True)

# Create history file header if missing
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        f.write("timestamp,soil1,soil2,rain,therm,bme_hum,bme_temp,bme_pres,acc_x,acc_y,acc_z,vibration,distance\n")

# ----------------------------------------
# Connect to Arduino
# ----------------------------------------
port = find_arduino()
if port is None:
    print("❌ ERROR: Arduino not found! Plug in USB.")
    exit()

print(f"✅ Connected to Arduino at {port}")

arduino = serial.Serial(port, 115200, timeout=1)
time.sleep(2)  # allow Arduino to reset


# ----------------------------------------
# Main Loop
# ----------------------------------------
while True:
    try:
        line = arduino.readline().decode().strip()

        if not line or "," not in line:
            continue  # ignore blank or malformed lines

        parts = line.split(",")

        if len(parts) != 14:
            print("⚠ Bad CSV line:", line)
            continue

        # Extract fields
        timestamp = parts[0]
        soil1 = parts[1]
        soil2 = parts[2]
        rain = parts[3]
        therm = parts[4]
        bme_hum = parts[5]
        bme_temp = parts[6]
        bme_pres = parts[7]
        acc_x = parts[8]
        acc_y = parts[9]
        acc_z = parts[10]
        vib = parts[11]
        dist = parts[12]

        # Save latest.json
        latest_data = {
            "timestamp": timestamp,
            "soil1": float(soil1),
            "soil2": float(soil2),
            "rain": float(rain),
            "thermistor": float(therm),
            "bme_humidity": float(bme_hum),
            "bme_temp": float(bme_temp),
            "bme_pressure": float(bme_pres),
            "acc_x": int(acc_x),
            "acc_y": int(acc_y),
            "acc_z": int(acc_z),
            "vibration": int(vib),
            "distance": float(dist)
        }

        with open(LATEST_FILE, "w") as f:
            json.dump(latest_data, f, indent=4)

        # Append to history.csv
        with open(HISTORY_FILE, "a") as f:
            f.write(",".join([
                timestamp, soil1, soil2, rain, therm,
                bme_hum, bme_temp, bme_pres,
                acc_x, acc_y, acc_z, vib, dist
            ]) + "\n")

        # Debug print
        print("✔ Data:", latest_data)

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(0.2)
