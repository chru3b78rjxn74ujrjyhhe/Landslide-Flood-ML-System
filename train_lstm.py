import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import joblib

# ------------------------------------
# FILE PATHS
# ------------------------------------
CALIB_FILE = "data/calibration.csv"
MODEL_DIR = "model"
MODEL_FILE = "model/model.h5"
SCALER_FILE = "model/scaler.pkl"

# ------------------------------------
# ENSURE MODEL FOLDER EXISTS
# ------------------------------------
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

print("🔧 TRAINING: Loading calibration data...")

# ------------------------------------
# LOAD DATA
# ------------------------------------
if not os.path.exists(CALIB_FILE):
    print("❌ No calibration file found! Run calibration first.")
    exit()

df = pd.read_csv(CALIB_FILE)

if len(df) < 20:
    print("❌ Not enough calibration data. Collect more rows.")
    exit()

print(f"📘 Loaded {len(df)} calibration samples.")

# ------------------------------------
# FEATURES (sensor inputs)
# ------------------------------------
FEATURES = [
    "soil1",
    "soil2",
    "rain",
    "distance",
    "vib1",
    "vib2",
    "ax",
    "ay",
    "az",
    "gx",
    "gy",
    "gz"
]

X = df[FEATURES].values

# ------------------------------------
# TARGETS — risk scores (auto generated)
# ------------------------------------
# These rules generate soft labels for training.
# The LSTM then learns & smooths the patterns.

def auto_landslide_risk(row):
    risk = 0
    risk += max(0, row["soil1"] - 600) * 0.05
    risk += max(0, row["soil2"] - 600) * 0.05
    if row["rain"] > 500:
        risk += 15
    if row["vib1"] == 1 or row["vib2"] == 1:
        risk += 10
    if abs(row["ax"]) > 15000 or abs(row["ay"]) > 15000:
        risk += 15
    return min(risk, 100)

def auto_flood_risk(row):
    risk = 0
    if row["distance"] > 0:
        risk += max(0, 100 - row["distance"]) * 0.6
    risk += max(0, row["rain"] - 400) * 0.05
    return min(risk, 100)

LS = []
FL = []
CB = []

for _, row in df.iterrows():
    l = auto_landslide_risk(row)
    f = auto_flood_risk(row)
    c = (l + f) / 2
    LS.append(l)
    FL.append(f)
    CB.append(c)

y = np.column_stack([LS, FL, CB])

print("📘 Auto-labels generated:")
print(" - Landslide ✓")
print(" - Flood ✓")
print(" - Combined ✓")

# ------------------------------------
# SCALING
# ------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("📘 Scaling complete.")

# Save scaler for live predictions
joblib.dump(scaler, SCALER_FILE)
print("💾 Saved scaler.pkl")

# ------------------------------------
# BUILD LSTM MODEL
# ------------------------------------
X_scaled = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))

model = Sequential()
model.add(LSTM(64, return_sequences=False, input_shape=(1, len(FEATURES))))
model.add(Dropout(0.2))
model.add(Dense(32, activation='relu'))
model.add(Dense(3, activation='linear'))  # 3 outputs

model.compile(optimizer="adam", loss="mse")

print("🧠 Training model...")

# ------------------------------------
# FIT MODEL
# ------------------------------------
es = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)

model.fit(
    X_scaled,
    y,
    epochs=40,
    batch_size=8,
    verbose=1,
    callbacks=[es]
)

# ------------------------------------
# SAVE MODEL
# ------------------------------------
model.save(MODEL_FILE)
print("💾 Saved model.h5")

print("\n✅ TRAINING COMPLETE!")
print("➡ Your system is now ready for LIVE ML PREDICTION.")
