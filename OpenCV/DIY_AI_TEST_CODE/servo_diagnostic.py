"""
servo_diagnostic.py
===================
Standalone test — no camera, no hand tracking needed.
Tests the full pipeline from Python → Serial → ESP32 → PCA9685 → Servos.

Run: pipenv run python servo_diagnostic.py
"""

import serial
import serial.tools.list_ports
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ── 1. Show all available COM ports ───────────────────────────────────────
print("\n" + "="*55)
print("  STEP 1: Scanning COM ports")
print("="*55)
ports = list(serial.tools.list_ports.comports())
if not ports:
    print("  [ERROR] No COM ports found at all! Is ESP32 plugged in?")
    sys.exit(1)

for p in ports:
    print(f"  {p.device:8s}  {p.description}")

# ── 2. Pick the port ──────────────────────────────────────────────────────
print()
auto_port = None
for p in ports:
    if any(x in p.description.lower() for x in ['cp210', 'ch340', 'ftdi', 'uart', 'arduino', 'usb']):
        auto_port = p.device
        break

if auto_port:
    print(f"  [AUTO] Detected: {auto_port}")
else:
    print("  [WARN] Could not auto-detect.")

choice = input(f"  Enter COM port (press Enter for '{auto_port or 'COM5'}'): ").strip()
port = choice if choice else (auto_port or 'COM5')

baud = input("  Enter baud rate (press Enter for 9600): ").strip()
baud = int(baud) if baud.isdigit() else 9600

# ── 3. Connect ────────────────────────────────────────────────────────────
print(f"\n  Connecting to {port} @ {baud} baud...")
try:
    conn = serial.Serial(port, baud, timeout=2)
    time.sleep(2)
    print(f"  [OK] Connected!")
    # Read any startup message from ESP32
    if conn.in_waiting:
        msg = conn.readline().decode('utf-8', errors='ignore').strip()
        print(f"  [ESP32 says]: {msg}")
except Exception as e:
    print(f"  [ERROR] Could not connect: {e}")
    sys.exit(1)

# ── Helper: send + print ──────────────────────────────────────────────────
def send(thumb, index, middle, ring, pinky, wrist, label=""):
    data = f"{thumb},{index},{middle},{ring},{pinky},{wrist}\n"
    conn.write(data.encode())
    print(f"  Sent [{label:20s}]: {data.strip()}")
    time.sleep(0.05)  # small gap between sends

# ── 4. Run tests ─────────────────────────────────────────────────────────
print("\n" + "="*55)
print("  STEP 2: Serial → ESP32 → Servo Tests")
print("  Watch your servos and answer Y/N for each test")
print("="*55)

results = {}

# TEST A: All servos to REST position
input("\n  [TEST A] Press Enter to send ALL servos to REST position...")
for _ in range(5):  # send 5 times to make sure it gets through
    send(175, 90, 100, 100, 85, 150, "REST")
time.sleep(2)
r = input("  Did ALL 6 servos move to rest position? (y/n): ").strip().lower()
results['A_rest'] = r == 'y'

# TEST B: One servo at a time
print("\n  [TEST B] Testing each servo channel individually...")
servo_tests = [
    (0, "THUMB",  285, 175),
    (1, "INDEX",  290, 90),
    (2, "MIDDLE", 290, 100),
    (3, "RING",   290, 100),
    (4, "PINKY",  290, 85),
    (5, "WRIST",  300, 150),
]

for ch, name, close_angle, open_angle in servo_tests:
    input(f"\n  Press Enter to test {name} (channel {ch})...")
    # Build angles — all at rest except this one
    angles = [175, 90, 100, 100, 85, 150]
    angles[ch] = close_angle
    for _ in range(5):
        send(*angles, label=f"{name} CLOSE")
    time.sleep(1.5)
    angles[ch] = open_angle
    for _ in range(5):
        send(*angles, label=f"{name} OPEN")
    time.sleep(1.5)
    r = input(f"  Did {name} move correctly? (y/n): ").strip().lower()
    results[f'B_{name}'] = r == 'y'

# TEST C: Rapid fire (simulate gesture module sending at 10fps)
print("\n  [TEST C] Sending rapid updates for 5 seconds (simulates gesture module)...")
input("  Press Enter to start...")
start = time.time()
count = 0
import math
while time.time() - start < 5:
    t = time.time() - start
    # Sweep all fingers open→close→open using a sine wave
    thumb  = int(175 + 55  * (math.sin(t * 1.5) + 1) / 2)
    index  = int(90  + 100 * (math.sin(t * 1.5) + 1) / 2)
    middle = int(100 + 95  * (math.sin(t * 1.5) + 1) / 2)
    ring   = int(100 + 95  * (math.sin(t * 1.5) + 1) / 2)
    pinky  = int(85  + 100 * (math.sin(t * 1.5) + 1) / 2)
    wrist  = 150
    send(thumb, index, middle, ring, pinky, wrist, "SWEEP")
    time.sleep(0.1)  # 10fps rate limit
    count += 1

print(f"  Sent {count} messages in 5 seconds")
r = input("  Did ALL servos sweep smoothly together? (y/n): ").strip().lower()
results['C_sweep'] = r == 'y'

# ── 5. Results summary ────────────────────────────────────────────────────
print("\n" + "="*55)
print("  DIAGNOSTIC RESULTS")
print("="*55)
all_pass = True
for test, passed in results.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}  {test}")
    if not passed:
        all_pass = False

print()
if all_pass:
    print("  ✅ All hardware tests passed!")
    print("  The problem is in gesture_module.py (hand tracking / calibration).")
    print("  Run gesture_module.py, press [S] immediately to lock calibration,")
    print("  then press [O] open hand + [C] fist + [S] to properly calibrate.")
elif not results.get('A_rest') and not any(v for k, v in results.items() if k.startswith('B_')):
    print("  ❌ No servos responded at all!")
    print("  → Wrong COM port, wrong baud rate, or ESP32 not running inmoov_servo_controller.ino")
elif not results.get('C_sweep'):
    print("  ⚠️  Individual servos work but rapid sweep fails.")
    print("  → Possible power supply issue (not enough current for all servos simultaneously)")
    print("  → Check 6V buck converter output under load")
else:
    fails = [k for k, v in results.items() if not v and k.startswith('B_')]
    print(f"  ❌ Failed servos: {fails}")
    print("  → Check wiring on those specific PCA9685 channels")

conn.close()
print("\nDone.")
