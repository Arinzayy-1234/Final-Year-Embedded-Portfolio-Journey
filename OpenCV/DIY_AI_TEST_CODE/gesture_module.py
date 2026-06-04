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

# --- VOICE MODULE (speech_recognition + pyaudio already in Pipfile) ---
try:
    from voice_module import VoiceCommander
    VOICE_AVAILABLE = True
    print("[OK] Voice module loaded (SpeechRecognition + PyAudio).")
except ImportError as _ve:
    VOICE_AVAILABLE = False
    print(f"[WARNING] VOICE MODULE DISABLED: {_ve}")
    print("         Run: pipenv install speechrecognition pyaudio")

# --- HELPER: Auto-detect Arduino COM port ---
def find_arduino_port():
    """Scans for Arduino/USB Serial ports. Returns first match or falls back to COM3."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Common Arduino identifiers on Windows
        if any(x in port.description.lower() for x in ['arduino', 'usb serial', 'ch340', 'cp2102', 'ftdi', 'usb']):
            print(f"[ARDUINO] Detected on {port.device}")
            return port.device
    print("[WARNING] Arduino not auto-detected. Using COM3 as fallback.")
    return 'COM5'

# --- INITIALIZATION ---
init_virtual_hand()  # Launches pygame window
arduino = ArduinoServoDriver(port=find_arduino_port())

# Mapping landmarks to human-readable names
# Each finger has: mcp (knuckle), pip (first bend), dip (second bend), tip
FINGER_LANDMARK_MAP = {
    "Thumb":  {"tip": 4,  "base": 1,  "mcp": 1,  "pip": 2,  "dip": 3},
    "Index":  {"tip": 8,  "base": 5,  "mcp": 5,  "pip": 6,  "dip": 7},
    "Middle": {"tip": 12, "base": 9,  "mcp": 9,  "pip": 10, "dip": 11},
    "Ring":   {"tip": 16, "base": 13, "mcp": 13, "pip": 14, "dip": 15},
    "Pinky":  {"tip": 20, "base": 17, "mcp": 17, "pip": 18, "dip": 19},
}

# Resolve the database path relative to this script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GESTURE_DB_FILE = os.path.join(SCRIPT_DIR, "gestures.json")

# --- STORAGE ---
open_hand_ratios = {}
closed_hand_ratios = {}

# ═══════════════════════════════════════════════════════════
# 🔧 WRIST CALIBRATION - CENTRED AT 0.0 DEGREES (STRAIGHT UP)
# ═══════════════════════════════════════════════════════════
WRIST_RAW_MIN = -45.0   # raw tilt left in degrees
WRIST_RAW_MAX = 45.0    # raw tilt right in degrees
# ═══════════════════════════════════════════════════════════

# Extremely tight baseline ranges so the tracker auto-calibrates to the user's hand instantly!
DEFAULT_CALIBRATION_PROFILE = {
    "Thumb":  {"open": 1.01, "close": 0.99},
    "Index":  {"open": 1.01, "close": 0.99},
    "Middle": {"open": 1.01, "close": 0.99},
    "Ring":   {"open": 1.01, "close": 0.99},
    "Pinky":  {"open": 1.01, "close": 0.99},
    "Wrist":  {"open": WRIST_RAW_MAX, "close": WRIST_RAW_MIN},
}

def _make_default_profile():
    return {finger: {"open": vals["open"], "close": vals["close"]}
            for finger, vals in DEFAULT_CALIBRATION_PROFILE.items()}

final_calibration_profile = _make_default_profile()
calibration_is_complete = True  # live tracking starts immediately
calibration_is_locked = False   # locks auto-updating calibration limits

SERVO_LIMITS = {
    "Thumb":  {"min": 175, "max": 285},
    "Index":  {"min": 90,  "max": 290},
    "Middle": {"min": 100, "max": 290},
    "Ring":   {"min": 100, "max": 290},
    "Pinky":  {"min": 85,  "max": 290},
    "Wrist":  {"min": 0,   "max": 300},
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
    print(f"\n[SUCCESS] '{gesture_name}' added to Keeper of Words!")

def get_gesture_from_database(gesture_name):
    if os.path.exists(GESTURE_DB_FILE):
        with open(GESTURE_DB_FILE, 'r') as f:
            return json.load(f).get(gesture_name.lower())
    return None

def print_focus_reminder():
    print("\n[SYSTEM] ⚠️  Click on the video window ('InMoov Control') to resume keyboard controls! ⚠️\n")

def delete_gesture_from_database():
    name = input("\nEnter the name of the gesture you want to delete: ").strip()
    if not name:
        print("[ERROR] Gesture name cannot be empty.")
        print_focus_reminder()
        return
    
    angles = get_gesture_from_database(name)
    if not angles:
        print(f"[ERROR] Gesture '{name}' not found in database.")
        print_focus_reminder()
        return
    
    print(f"\nGesture found: '{name}'")
    print("Servo angles:")
    for comp in ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]:
        print(f"  {comp:<7}: {angles.get(comp, 'N/A')} degrees")
        
    choice = input("\nAre you sure you want to delete this entry? (y/n): ").strip().lower()
    if choice == 'y':
        database = {}
        if os.path.exists(GESTURE_DB_FILE):
            try:
                with open(GESTURE_DB_FILE, 'r') as f:
                    database = json.load(f)
            except:
                database = {}
        if name.lower() in database:
            del database[name.lower()]
            with open(GESTURE_DB_FILE, 'w') as f:
                json.dump(database, f, indent=4)
            print(f"[SUCCESS] '{name}' has been erased from the Keeper of Words!")
        else:
            print(f"[ERROR] Could not find '{name}' in database keys.")
    else:
        print("[CANCELLED] Erase operation aborted.")
    print_focus_reminder()

def manual_add_gesture():
    name = input("\nEnter the name of the new gesture: ").strip()
    if not name:
        print("[ERROR] Gesture name cannot be empty.")
        print_focus_reminder()
        return
    
    manual_angles = {}
    components = ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]
    print("\n--- Manual Servo Input ---")
    for comp in components:
        limits = SERVO_LIMITS[comp]
        while True:
            try:
                val_str = input(f"Enter {comp} angle (Range: {limits['min']} to {limits['max']}): ").strip()
                val = float(val_str)
                if val < limits['min'] or val > limits['max']:
                    print(f"[WARNING] Angle out of safe physical limits ({limits['min']} - {limits['max']}). Clamping value.")
                    val = max(limits['min'], min(limits['max'], val))
                manual_angles[comp] = round(val, 1)
                break
            except ValueError:
                print("[ERROR] Invalid input. Please enter a valid number.")
                
    for comp in ["Thumb", "Index", "Middle", "Ring", "Pinky"]:
        manual_angles[f"{comp}_Spread"] = 0.0
        
    save_gesture_to_database(name, manual_angles)
    print_focus_reminder()

# --- VOICE STATE (thread-safe, non-blocking) ---
# _voice_state is shared between the main thread and the listener thread.
# 'listening' : True while the mic thread is active (shows HUD banner on camera)
# 'result'    : the recognized text string, or None (no speech / error)
# 'ready'     : True when the thread has finished and a result is waiting
_voice_state = {'listening': False, 'result': None, 'ready': False}
_voice_lock  = threading.Lock()

def _voice_listen_thread():
    """Runs in a background thread so the camera loop never freezes."""
    global _voice_state, voice_commander
    if voice_commander is None:
        if VOICE_AVAILABLE:
            voice_commander = VoiceCommander()
            voice_commander.calibrate(duration=0.8)
        else:
            with _voice_lock:
                _voice_state['result']    = None
                _voice_state['listening'] = False
                _voice_state['ready']     = True
            return

    text = voice_commander.listen_and_convert(should_calibrate=False)
    with _voice_lock:
        _voice_state['result']    = text
        _voice_state['listening'] = False
        _voice_state['ready']     = True

def start_voice_listen():
    """Spawns the listener thread if voice is available and not already listening."""
    with _voice_lock:
        if _voice_state['listening']:
            return  # already running
        _voice_state['listening'] = True
        _voice_state['result']    = None
        _voice_state['ready']     = False
    t = threading.Thread(target=_voice_listen_thread, daemon=True)
    t.start()

def poll_voice_result():
    """Returns (True, text_or_None) if a result is ready, else (False, None)."""
    with _voice_lock:
        if _voice_state['ready']:
            _voice_state['ready'] = False
            return True, _voice_state['result']
    return False, None

# Create and pre-calibrate voice commander at startup
voice_commander = None
if VOICE_AVAILABLE:
    voice_commander = VoiceCommander()
    voice_commander.calibrate(duration=0.8)

# --- MATH & PROCESSING ---

def calculate_finger_curl_ratio(hand_landmarks, tip_idx, base_idx, wrist_idx=0):
    # Calculate 3D Euclidean distance (tip-to-wrist and base-to-wrist)
    tip   = np.array([hand_landmarks[tip_idx][1],  hand_landmarks[tip_idx][2],  hand_landmarks[tip_idx][3]])
    base  = np.array([hand_landmarks[base_idx][1], hand_landmarks[base_idx][2], hand_landmarks[base_idx][3]])
    wrist = np.array([hand_landmarks[wrist_idx][1], hand_landmarks[wrist_idx][2], hand_landmarks[wrist_idx][3]])
    return np.linalg.norm(tip - wrist) / (np.linalg.norm(base - wrist) + 1e-6)

def calculate_wrist_rotation(hand_landmarks):
    # 3D points
    w = np.array([hand_landmarks[0][1], hand_landmarks[0][2], hand_landmarks[0][3]])
    m = np.array([hand_landmarks[9][1], hand_landmarks[9][2], hand_landmarks[9][3]])
    p = np.array([hand_landmarks[17][1], hand_landmarks[17][2], hand_landmarks[17][3]])
    
    # Vectors
    v1 = m - w
    v2 = p - w
    
    # Cross product to get palm normal vector
    normal = np.cross(v1, v2)
    norm_len = np.linalg.norm(normal)
    if norm_len < 1e-6:
        return 0.0
    normal = normal / norm_len
    
    # Rotate normal vector X/Z angle (representing hand roll/wrist rotation)
    # Centered flat at 0.0 degrees
    angle = np.degrees(np.arctan2(normal[0], normal[2]))
    return angle

def calculate_finger_spread(hand_landmarks, tip_idx, mcp_idx):
    """
    Subtle distance-invariant lateral splay.
    Normalizes lateral splay by hand scale (distance from wrist to middle MCP)
    so splay angle is completely independent of camera distance.
    """
    tip = np.array([hand_landmarks[tip_idx][1], hand_landmarks[tip_idx][2]])
    mcp = np.array([hand_landmarks[mcp_idx][1], hand_landmarks[mcp_idx][2]])
    
    # Calculate current hand reference scale in pixels
    w = np.array([hand_landmarks[0][1], hand_landmarks[0][2]])
    m = np.array([hand_landmarks[9][1], hand_landmarks[9][2]])
    hand_size = np.linalg.norm(m - w) + 1e-6
    
    # Distance-invariant normalized lateral offset
    lateral = (tip[0] - mcp[0]) / hand_size
    
    # Scale to splay angles
    spread = np.clip(lateral * 3.5, -1.0, 1.0) * 3.0
    return spread

def normalize_value(current, limit_open, limit_close):
    if abs(limit_open - limit_close) < 1e-6:
        return 0.5
    return float(np.clip((current - limit_close) / (limit_open - limit_close), 0.0, 1.0))

def auto_update_calibration(finger_name, ratio):
    """
    Expand calibration limits dynamically with safety bounds.
    Rejects tracking glitches (crazy ratios) from permanently corrupting limits.
    """
    profile = final_calibration_profile.setdefault(
        finger_name, {"open": ratio, "close": ratio})
        
    # Standard finger curl ratio safety bounds: typical ranges are between 0.6 and 1.8
    if finger_name != "Wrist":
        safe_min, safe_max = 0.55, 1.85
        if not (safe_min <= ratio <= safe_max):
            return # Skip updates from tracking drops or glitches
            
    if ratio > profile["open"]:
        profile["open"] = ratio
    elif ratio < profile["close"]:
        profile["close"] = ratio

def map_to_servo(norm, name):
    l = SERVO_LIMITS[name]
    if name == "Wrist":
        return round(l["min"] + (norm * (l["max"] - l["min"])), 1)
    else:
        # Fingers: norm=1.0 is open (l["min"] servo), norm=0.0 is closed (l["max"] servo)
        inverted_norm = 1.0 - norm
        return round(l["min"] + (inverted_norm * (l["max"] - l["min"])), 1)

class Smoother:
    def __init__(self, alpha=0.35):
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
    cv2.waitKey(1)  # Force GUI refresh to draw window
    
    while True:
        choice = input(f"\nSave {label} state? (y/n): ").strip().lower()
        if choice == 'y':
            print(f"[OK] {label.upper()} state calibration ratios captured!")
            is_camera_frozen = False
            try:
                cv2.destroyWindow("Preview")
            except:
                pass
            print_focus_reminder()
            return ratios
        elif choice == 'n':
            print(f"[DISCARDED] {label.upper()} snapshot discarded.")
            is_camera_frozen = False
            try:
                cv2.destroyWindow("Preview")
            except:
                pass
            print_focus_reminder()
            return None
        else:
            print("[ERROR] Invalid choice. Please type 'y' or 'n' in the terminal.")

def process_frame(landmarks):
    cmds = {}
    for n, ids in FINGER_LANDMARK_MAP.items():
        ratio = calculate_finger_curl_ratio(landmarks, ids["tip"], ids["base"])
        if not calibration_is_locked:
            auto_update_calibration(n, ratio)
        profile = final_calibration_profile[n]
        norm = normalize_value(ratio, profile['open'], profile['close'])
        cmds[n] = round(signal_smoother.smooth(n, map_to_servo(norm, n)), 1)
        
        # Dampened organic lateral finger spread
        spread = calculate_finger_spread(landmarks, ids["tip"], ids["base"])
        cmds[f"{n}_Spread"] = round(signal_smoother.smooth(f"{n}_Spread", spread), 1)
    
    # Wrist rotation with dynamic calibration!
    w_raw = calculate_wrist_rotation(landmarks)
    if not calibration_is_locked:
        auto_update_calibration("Wrist", w_raw)
    w_profile = final_calibration_profile["Wrist"]
    w_norm = normalize_value(w_raw, w_profile['open'], w_profile['close'])
    cmds["Wrist"] = round(signal_smoother.smooth("Wrist", map_to_servo(w_norm, "Wrist")), 1)
    return cmds

# --- MAIN LOOP ---
print("\n[INMOOV] GESTURE MODULE READY")
print("Controls:")
print("  [G] Capture & Save Live Gesture")
print("  [T] Trigger Pre-saved Gesture (Prompts to add if missing)")
print("  [E] Erase Gesture from Database")
print("  [J] Manually Add Gesture & Angles")
print("  [V] Voice Command (Speech-to-Sign)")
print("  [O] Open Hand Snapshot (Calib)")
print("  [C] Closed Hand Snapshot (Calib)")
print("  [S] Sync/Lock Calibration (Stops auto-tuning)")
print("  [L] Calibrate Wrist LHS (Far Left limit)")
print("  [R] Calibrate Wrist RHS (Far Right limit)")
print("  [SPACE] Resume Live Hand Tracking (when override is active)")
print("  [Q] Quit")
print("Default calibration loaded - wave at the camera to auto-tune.")

servo_data = {}
active_override_gesture = None

while True:
    k = cv2.waitKey(1) & 0xFF
    if not is_camera_frozen:
        success, img = cap.read()
        if success:
            last_valid_frame = img.copy()
            if active_override_gesture is None:
                hand_detector.find_hands(img)
                marks = hand_detector.find_position(img)
                if marks and calibration_is_complete:
                    servo_data = process_frame(marks)
                    print(f"TRACKING: {servo_data}      ", end='\r', flush=True)
                    send_to_virtual_hand(servo_data)
                    arduino.send_angles(servo_data)
            else:
                # Draw a sleek cybernetic blue banner for the override mode
                overlay = img.copy()
                cv2.rectangle(overlay, (0, 0), (img.shape[1], 60), (255, 191, 0), -1) # Ice Blue/Cyan (BGR: 255, 191, 0)
                cv2.addWeighted(overlay, 0.65, img, 0.35, 0, img)
                cv2.putText(img, f"GESTURE OVERRIDE: {active_override_gesture.upper()}",
                            (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                            (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(img, "Press [SPACE] or speak 'resume' to return to tracking",
                            (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                            (220, 255, 255), 1, cv2.LINE_AA)
                print(f"OVERRIDE ACTIVE [{active_override_gesture.upper()}] - Press SPACE or speak 'resume' to track    ", end='\r', flush=True)
            cv2.imshow("InMoov Control", img)

    if k != 255:
        if k == ord('q') or k == ord('Q'):
            break
        elif k == 32:  # SPACE key
            active_override_gesture = None
            print("\n" + "═" * 55)
            print("  🔄  RESUMING LIVE HAND TRACKING")
            print("═" * 55)
        elif k == ord('o') or k == ord('O'):
            is_camera_frozen = True
            data = capture_snapshot(last_valid_frame, "open")
            if data:
                open_hand_ratios = data
        elif k == ord('c') or k == ord('C'):
            is_camera_frozen = True
            data = capture_snapshot(last_valid_frame, "closed")
            if data:
                closed_hand_ratios = data
        elif k == ord('s') or k == ord('S'):
            if open_hand_ratios and closed_hand_ratios:
                for n in SERVO_LIMITS:
                    if n != "Wrist":  # Skip Wrist so it doesn't overwrite your L/R calibration!
                        if n in open_hand_ratios:
                            final_calibration_profile[n] = {'open': open_hand_ratios[n], 'close': closed_hand_ratios[n]}
                calibration_is_complete = True
                calibration_is_locked = True
                print("\n" * 3, flush=True)  # Push past the TRACKING line
                print("═" * 55, flush=True)
                print("  ✅  CALIBRATION LOCKED & AUTO-TUNING DISABLED", flush=True)
                print("      Clamping is now ENABLED.", flush=True)
                print("═" * 55, flush=True)
            else:
                print("\n" * 3, flush=True)
                print("═" * 55, flush=True)
                print("  ❌  SYNC FAILED: Capture Open (O) and Closed (C) first!", flush=True)
                print("═" * 55, flush=True)
        elif k == ord('l') or k == ord('L'):
            if 'marks' in locals() and marks:
                w_raw = calculate_wrist_rotation(marks)
                final_calibration_profile["Wrist"]["close"] = w_raw
                print("\n" * 3, flush=True)
                print("═" * 55, flush=True)
                print(f"  🔧  WRIST LHS LIMIT SET → {w_raw:.1f}°", flush=True)
                print("═" * 55, flush=True)
            else:
                print("\n" * 3, flush=True)
                print("═" * 55, flush=True)
                print("  ⚠️  NO HAND DATA — Show your hand to the camera!", flush=True)
                print("═" * 55, flush=True)
        elif k == ord('r') or k == ord('R'):
            if 'marks' in locals() and marks:
                w_raw = calculate_wrist_rotation(marks)
                final_calibration_profile["Wrist"]["open"] = w_raw
                print("\n" * 3, flush=True)
                print("═" * 55, flush=True)
                print(f"  🔧  WRIST RHS LIMIT SET → {w_raw:.1f}°", flush=True)
                print("═" * 55, flush=True)
            else:
                print("\n" * 3, flush=True)
                print("═" * 55, flush=True)
                print("  ⚠️  NO HAND DATA — Show your hand to the camera!", flush=True)
                print("═" * 55, flush=True)
        elif k == ord('g') or k == ord('G'):
            if servo_data:
                is_camera_frozen = True
                print("\n--- LIVE GESTURE SNAPSHOT CAPTURED ---")
                print("Calculated Servo Angles:")
                for comp in ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]:
                    print(f"  {comp:<7}: {servo_data.get(comp, 'N/A')} degrees")
                
                name = input("\nEnter name for this gesture: ").strip()
                if name:
                    choice = input(f"Save gesture '{name}'? (y/n): ").strip().lower()
                    if choice == 'y':
                        save_gesture_to_database(name, servo_data)
                    else:
                        print("[CANCELLED] Snapshot discarded.")
                else:
                    print("[ERROR] Gesture name cannot be empty. Discarding snapshot.")
                is_camera_frozen = False
            else:
                print("\n[WARNING] No active hand tracking data. Put your hand in front of the camera!")
            print_focus_reminder()
        elif k == ord('t') or k == ord('T'):
            is_camera_frozen = True
            name = input("\nEnter gesture name to sign: ").strip()
            if name:
                angles = get_gesture_from_database(name)
                if angles:
                    print(f"[OK] Sending '{name}' to virtual hand and robotic arm immediately!")
                    active_override_gesture = name.lower()
                    send_to_virtual_hand(angles)
                    arduino.send_angles(angles)
                else:
                    choice = input(f"Gesture '{name}' not found. Do you want to add it to the database? (y/n): ").strip().lower()
                    if choice == 'y':
                        print("\nPosition your hand in front of the camera.")
                        input("Press Enter when ready to capture the snapshot...")
                        is_camera_frozen = False
                        success, img_cap = cap.read()
                        if success:
                            hand_detector.find_hands(img_cap)
                            marks_cap = hand_detector.find_position(img_cap)
                            if marks_cap:
                                servo_data_cap = process_frame(marks_cap)
                                print("\nCalculated Servo Angles:")
                                for comp in ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]:
                                    print(f"  {comp:<7}: {servo_data_cap.get(comp, 'N/A')} degrees")
                                
                                confirm = input(f"Save gesture '{name}' with these angles? (y/n): ").strip().lower()
                                if confirm == 'y':
                                    save_gesture_to_database(name, servo_data_cap)
                                    active_override_gesture = name.lower()
                                else:
                                    print("[CANCELLED] Discarded.")
                            else:
                                print("[ERROR] No hand detected in the camera feed. Unable to add.")
                        else:
                            print("[ERROR] Camera read failed. Unable to add.")
            is_camera_frozen = False
            print_focus_reminder()
        elif k == ord('e') or k == ord('E'):
            is_camera_frozen = True
            delete_gesture_from_database()
            is_camera_frozen = False
        elif k == ord('j') or k == ord('J'):
            is_camera_frozen = True
            manual_add_gesture()
            is_camera_frozen = False
        elif k == ord('v') or k == ord('V'):
            if VOICE_AVAILABLE:
                with _voice_lock:
                    already = _voice_state['listening']
                if not already:
                    print("\n" + "═" * 55)
                    print("  🎤  VOICE MODE — Speak a gesture name now...")
                    print("═" * 55)
                    start_voice_listen()   # non-blocking — camera stays live
                else:
                    print("[VOICE] Already listening — please wait.")
            else:
                print("[WARNING] Voice module disabled.")
                print("         Run: pipenv install speechrecognition pyaudio")

    # --- Poll voice result every frame (non-blocking) ---
    if VOICE_AVAILABLE:
        done, cmd = poll_voice_result()
        if done:
            if cmd:
                print("\n" + "═" * 55)
                print(f"  ✅  HEARD: '{cmd}'")
                if cmd in ["resume", "track", "live", "camera"]:
                    active_override_gesture = None
                    print("  🔄  Resuming live tracking!")
                else:
                    angles = get_gesture_from_database(cmd)
                    if angles:
                        print(f"  🤖  Sending '{cmd}' → virtual hand + robotic arm!")
                        active_override_gesture = cmd
                        send_to_virtual_hand(angles)
                        arduino.send_angles(angles)
                    else:
                        print(f"  ⚠️   '{cmd}' not in gesture database.")
                        print("       Press [G] to capture + save a gesture with that name.")
                print("═" * 55)
            else:
                print("\n" + "═" * 55)
                print("  ❌  VOICE: No speech recognised — try again with [V].")
                print("═" * 55)

    # --- Paint LISTENING banner on the camera frame ---
    if VOICE_AVAILABLE:
        with _voice_lock:
            is_listening = _voice_state['listening']
        if is_listening and not is_camera_frozen:
            success, img = cap.read()
            if success:
                last_valid_frame = img.copy()
                # Overlay a pulsing magenta "LISTENING" banner
                overlay = img.copy()
                cv2.rectangle(overlay, (0, 0), (img.shape[1], 60), (180, 0, 120), -1)
                cv2.addWeighted(overlay, 0.55, img, 0.45, 0, img)
                cv2.putText(img, "  MIC ACTIVE — SPEAK NOW",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                            (255, 255, 255), 2, cv2.LINE_AA)
                cv2.imshow("InMoov Control", img)
            continue  # skip normal frame-processing while listening

cap.release()
cv2.destroyAllWindows()
arduino.close()
