import serial
import time
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from tensorflow.keras.models import load_model
import joblib

# ------------------------------------
# FILE PATHS
# ------------------------------------
STATE_FILE = "data/state.json"
CALIB_FILE = "data/calibration.csv"
HISTORY_FILE = "data/history.csv"
LATEST_FILE = "data/latest.json"

MODEL_FILE = "model/model.h5"
SCALER_FILE = "model/scaler.pkl"

# ------------------------------------
# SERIAL PORT (Arduino → Pi)
# ------------------------------------
PORT = "/dev/ttyACM0"   # update if different
BAUD = 115200

# Try connecting to Arduino
while True:
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print("Connected to Arduino on", PORT)
        break
    except:
        print("Waiting for Arduino...")
        time.sleep(2)

# ------------------------------------
# STATE HANDLING
# ------------------------------------
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"mode": "normal", "collecting": False}

def save_latest(data):
    with open(LATEST_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ------------------------------------
# LOAD MODEL IF EXISTS
# ------------------------------------
model = None
scaler = None

def load_ml_model():
    global model, scaler
    if os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
        model = load_model(MODEL_FILE)
        scaler = joblib.load(SCALER_FILE)
        print("ML Model Loaded.")
    else:
        print("⚠ No model found — running NO-ML mode")

load_ml_model()

# ------------------------------------
# PARSE CSV FROM ARDUINO
# ------------------------------------
def parse_csv(line):
    try:
        parts = line.strip().split(",")
        if len(parts) != 14:
            return None

        # convert values
        soil1 = int(parts[0])
        soil2 = int(parts[1])
        rain = int(parts[2])
        vib1 = int(parts[3])
        vib2 = int(parts[4])
        distance = float(parts[5])
        ax = int(parts[6])
        ay = int(parts[7])
        az = int(parts[8])
        gx = int(parts[9])
        gy = int(parts[10])
        gz = int(parts[11])
        timestamp = parts[12]  # hh:mm:ss

        return {
            "soil1": soil1,
            "soil2": soil2,
            "rain": rain,
            "vib1": vib1,
            "vib2": vib2,
            "distance": distance,
            "ax": ax,
            "ay": ay,
            "az": az,
            "gx": gx,
            "gy": gy,
            "gz": gz,
            "timestamp": timestamp
        }
    except:
        return None

# ------------------------------------
# MAIN LOOP
# ------------------------------------
print("Starting ML background engine...")

while True:
    state = load_state()

    # Read line from Arduino
    try:
        line = ser.readline().decode().strip()
    except:
        continue

    if not line:
        continue

    data = parse_csv(line)
    if data is None:
        print("Bad packet:", line)
        continue

    # --------------------------------
    # 🟦 MODE 1 — CALIBRATION MODE
    # --------------------------------
    if state["mode"] == "calibration" and state["collecting"]:
        df_row = pd.DataFrame([data])
        df_row.to_csv(CALIB_FILE, mode="a", header=not os.path.exists(CALIB_FILE), index=False)
        print("[CALIBRATION] Saved row")
        continue

    # --------------------------------
    # 🟪 MODE 2 — TRAINING MODE
    # (Handled by train_lstm.py in app.py)
    # --------------------------------
    if state["mode"] == "training":
        print("[TRAINING MODE] Waiting...")
        time.sleep(1)
        continue

    # --------------------------------
    # 🟩 MODE 3 — NORMAL (ML PREDICTION)
    # --------------------------------
    if model is not None:
        X = np.array([[      
            data["soil1"],
            data["soil2"],
            data["rain"],
            data["distance"],
            data["vib1"],
            data["vib2"],
            data["ax"],
            data["ay"],
            data["az"],
            data["gx"],
            data["gy"],
            data["gz"]
        ]])

        # Scale
        X_scaled = scaler.transform(X)

        # 3 risk predictions
        preds = model.predict(X_scaled)[0]

        landslide_risk = float(preds[0])
        flood_risk = float(preds[1])
        combined_risk = float(preds[2])

    else:
        # fallback NO-ML mode (rule-based)
        landslide_risk = 10 + data["rain"] / 15
        flood_risk = 5 + max(0, 100 - data["distance"]) / 3
        combined_risk = (landslide_risk + flood_risk) / 2

    # SAVE HISTORY
    row = data.copy()
    row.update({
        "landslide": landslide_risk,
        "flood": flood_risk,
        "combined": combined_risk
    })

    pd.DataFrame([row]).to_csv(HISTORY_FILE, mode="a", header=not os.path.exists(HISTORY_FILE), index=False)

    # SAVE LATEST JSON (dashboard reads this)
    save_latest({
        "landslide": landslide_risk,
        "flood": flood_risk,
        "combined": combined_risk,
        "timestamp": data["timestamp"]
    })

    print(f"[PREDICT] LS={landslide_risk:.1f} FL={flood_risk:.1f} CB={combined_risk:.1f}")

    time.sleep(0.1)
