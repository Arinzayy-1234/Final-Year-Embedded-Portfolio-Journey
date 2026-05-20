import sys
import os
import numpy as np
import json
import cv2
import threading
import time
import serial.tools.list_ports

# This tells Python to look one folder "up" for modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rawMp import RawHandDetector
from python_virtual_hand import init_virtual_hand, send_to_virtual_hand
from arduino_to_servo_driver import ArduinoServoDriver

# --- TRY TO IMPORT VOICE (Requires 'pip install SpeechRecognition PyAudio') ---
try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️ VOICE MODULE DISABLED: Run 'pip install SpeechRecognition PyAudio' to enable.")

# --- HELPER: Auto-detect Arduino COM port ---
def find_arduino_port():
    """Scans for Arduino/USB Serial ports. Returns first match or falls back to COM3."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Common Arduino identifiers on Windows
        if any(x in port.description.lower() for x in ['arduino', 'usb serial', 'ch340', 'cp2102', 'ftdi', 'usb']):
            print(f"🔍 Arduino detected on {port.device}")
            return port.device
    print("⚠️ Arduino not auto-detected. Using COM3 as fallback.")
    return 'COM3'

# --- INITIALIZATION ---
init_virtual_hand()  # Launches pygame window
arduino = ArduinoServoDriver(port=find_arduino_port())

# Mapping landmarks to human-readable names
FINGER_LANDMARK_MAP = {
    "Thumb":  {"tip": 4,  "base": 1},
    "Index":  {"tip": 8,  "base": 5},
    "Middle": {"tip": 12, "base": 9},
    "Ring":   {"tip": 16, "base": 13},
    "Pinky":  {"tip": 20, "base": 17},
}

GESTURE_DB_FILE = "gestures.json"

# --- STORAGE ---
open_hand_ratios = {}
closed_hand_ratios = {}
final_calibration_profile = {}
calibration_is_complete = False

SERVO_LIMITS = {
    "Thumb":  {"min": 20, "max": 150},
    "Index":  {"min": 20, "max": 160},
    "Middle": {"min": 20, "max": 160},
    "Ring":   {"min": 25, "max": 155},
    "Pinky":  {"min": 25, "max": 145},
    "Wrist":  {"min": 0,  "max": 180},
}

hand_detector = RawHandDetector()
cap = cv2.VideoCapture(0)
is_camera_frozen = False
last_valid_frame = None

# --- DATABASE LOGIC ---

def save_gesture_to_database(gesture_name, servo_angles):
    database = {}
    if os.path.exists(GESTURE_DB_FILE):
        try:
            with open(GESTURE_DB_FILE, 'r') as f: database = json.load(f)
        except: database = {}
    database[gesture_name.lower()] = servo_angles
    with open(GESTURE_DB_FILE, 'w') as f: json.dump(database, f, indent=4)
    print(f"\n✅ SUCCESS: '{gesture_name}' added to Keeper of Words!")

def get_gesture_from_database(gesture_name):
    if os.path.exists(GESTURE_DB_FILE):
        with open(GESTURE_DB_FILE, 'r') as f:
            return json.load(f).get(gesture_name.lower())
    return None

# --- VOICE COMMANDER CLASS ---

class VoiceModule:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

    def listen(self):
        with self.mic as source:
            print("\n🎤 LISTENING...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                return text.lower()
            except:
                return None

voice = VoiceModule() if VOICE_AVAILABLE else None

# --- MATH & PROCESSING ---

def calculate_finger_curl_ratio(hand_landmarks, tip_idx, base_idx, wrist_idx=0):
    tip   = np.array([hand_landmarks[tip_idx][1],  hand_landmarks[tip_idx][2]])
    base  = np.array([hand_landmarks[base_idx][1], hand_landmarks[base_idx][2]])
    wrist = np.array([hand_landmarks[wrist_idx][1], hand_landmarks[wrist_idx][2]])
    return np.linalg.norm(tip - wrist) / (np.linalg.norm(base - wrist) + 1e-6)

def calculate_wrist_rotation(hand_landmarks):
    # Angle between Index MCP(5) and Pinky MCP(17)
    p1, p2 = np.array([hand_landmarks[5][1], hand_landmarks[5][2]]), np.array([hand_landmarks[17][1], hand_landmarks[17][2]])
    delta = p1 - p2
    return np.degrees(np.arctan2(delta[1], delta[0])) + 90

# ═══════════════════════════════════════════════════════════
# 🔧 WRIST CALIBRATION - TUNE THESE VALUES AFTER PHYSICAL TEST
# ═══════════════════════════════════════════════════════════
# Run gesture_module.py, rotate wrist fully LEFT → note w_raw value → set as WRIST_RAW_MIN
# Rotate wrist fully RIGHT → note w_raw value → set as WRIST_RAW_MAX
# These values convert raw camera angle → normalized 0.0-1.0 → servo angle
WRIST_RAW_MIN = -30   # ← TUNE: raw value when wrist fully rotated LEFT
WRIST_RAW_MAX = 60    # ← TUNE: raw value when wrist fully rotated RIGHT
# ═══════════════════════════════════════════════════════════

def calculate_finger_spread(hand_landmarks, tip_idx, mcp_idx):
    """
    Detect lateral finger movement for cartoonish virtual animation.
    Physical hand can't move fingers side-to-side, but virtual hand can!
    Returns: spread angle in degrees (-30 to +30)
    """
    tip = np.array([hand_landmarks[tip_idx][1], hand_landmarks[tip_idx][2]])
    mcp = np.array([hand_landmarks[mcp_idx][1], hand_landmarks[mcp_idx][2]])
    # Lateral offset: x-axis difference (left/right movement)
    lateral = tip[0] - mcp[0]
    # Normalize: divide by sensitivity factor, clip to ±1.0, scale to ±30°
    # Adjust 15.0 to change sensitivity (smaller = more sensitive)
    spread = np.clip(lateral / 15.0, -1.0, 1.0) * 30.0
    return spread

def normalize_value(current, limit_open, limit_close):
    if abs(limit_open - limit_close) < 1e-6: return 0.5
    return float(np.clip((current - limit_close) / (limit_open - limit_close), 0.0, 1.0))

def map_to_servo(norm, name):
    l = SERVO_LIMITS[name]
    return round(l["min"] + (norm * (l["max"] - l["min"])), 1)

class Smoother:
    def __init__(self, alpha=0.25):
        self.alpha, self.history = alpha, {}
    def smooth(self, label, val):
        if label not in self.history: self.history[label] = val
        self.history[label] = (self.alpha * val) + (1 - self.alpha) * self.history[label]
        return self.history[label]

signal_smoother = Smoother()

# --- MAIN FUNCTIONS ---

def capture_snapshot(frame, label):
    global is_camera_frozen
    landmarks = hand_detector.find_position(frame, draw=False)
    if not landmarks: return None
    ratios = {n: round(calculate_finger_curl_ratio(landmarks, ids["tip"], ids["base"]), 3) for n, ids in FINGER_LANDMARK_MAP.items()}
    ratios["Wrist"] = calculate_wrist_rotation(landmarks)
    
    cv2.imshow("Preview", frame)
    print(f"\nSave {label} state? (y/n)")
    while True:
        k = cv2.waitKey(0) & 0xFF
        if k == ord('y'): is_camera_frozen = False; return ratios
        if k == ord('n'): is_camera_frozen = False; return None

def process_frame(landmarks):
    cmds = {}
    for n, ids in FINGER_LANDMARK_MAP.items():
        ratio = calculate_finger_curl_ratio(landmarks, ids["tip"], ids["base"])
        norm = normalize_value(ratio, final_calibration_profile[n]['open'], final_calibration_profile[n]['close'])
        cmds[n] = round(signal_smoother.smooth(n, map_to_servo(norm, n)), 1)
        
        # 🎨 CARTOONISH FALLBACK: Add virtual spread for side-to-side finger motion
        # Physical hand can't do this, but virtual hand will animate it!
        spread = calculate_finger_spread(landmarks, ids["tip"], ids["base"])
        cmds[f"{n}_Spread"] = round(signal_smoother.smooth(f"{n}_Spread", spread), 1)
    
    # Wrist rotation: normalize raw angle to 0.0-1.0 using calibrated limits
    w_raw = calculate_wrist_rotation(landmarks)
    # Normalize: (raw - min) / (max - min), clipped to [0,1]
    w_range = WRIST_RAW_MAX - WRIST_RAW_MIN + 1e-6  # +1e-6 prevents division by zero
    w_norm = np.clip((w_raw - WRIST_RAW_MIN) / w_range, 0.0, 1.0)
    cmds["Wrist"] = round(signal_smoother.smooth("Wrist", map_to_servo(w_norm, "Wrist")), 1)
    return cmds

# --- MAIN LOOP ---
print("\n🔥 INMOOV GESTURE MODULE READY")
print("Controls: [O] Open, [C] Closed, [S] Sync, [K] Save, [T] Text, [V] Voice, [Q] Quit")

while True:
    k = cv2.waitKey(1) & 0xFF
    if not is_camera_frozen:
        success, img = cap.read()
        if success:
            last_valid_frame = img.copy()
            hand_detector.find_hands(img)
            marks = hand_detector.find_position(img)
            if marks and calibration_is_complete:
                servo_data = process_frame(marks)
                print(f"TRACKING: {servo_data}", end='\r')
                send_to_virtual_hand(servo_data)
                arduino.send_angles(servo_data)
                # ⚡ Tiny delay helps sync threads and reduce visual lag
                time.sleep(0.01)
            cv2.imshow("InMoov Control", img)

    if k != 255:
        if k == ord('q'): break
        elif k == ord('o'): is_camera_frozen = True; data = capture_snapshot(last_valid_frame, "open"); (open_hand_ratios := data) if data else None
        elif k == ord('c'): is_camera_frozen = True; data = capture_snapshot(last_valid_frame, "closed"); (closed_hand_ratios := data) if data else None
        elif k == ord('s'):
            if open_hand_ratios and closed_hand_ratios:
                for n in SERVO_LIMITS:
                    if n in open_hand_ratios: final_calibration_profile[n] = {'open': open_hand_ratios[n], 'close': closed_hand_ratios[n]}
                calibration_is_complete = True
                print("\n✅ CALIBRATION LOCKED.")
        elif k == ord('k') and 'servo_data' in locals():
            name = input("\nName this sign: ")
            save_gesture_to_database(name, servo_data)
        elif k == ord('t'):
            name = input("\nType sign name: ")
            angles = get_gesture_from_database(name)
            if angles: send_to_virtual_hand(angles); arduino.send_angles(angles)
        elif k == ord('v') and VOICE_AVAILABLE:
            cmd = voice.listen()
            if cmd:
                print(f"User said: {cmd}")
                angles = get_gesture_from_database(cmd)
                if angles: send_to_virtual_hand(angles); arduino.send_angles(angles)
                else: print(f"'{cmd}' not in database.")

cap.release()
cv2.destroyAllWindows()
arduino.close()
