"""
voice_module.py — Offline Speech Recognition using Vosk
--------------------------------------------------------
No internet required. Works with noisy environments.
Automatically downloads the small English model (~50MB) on first run.

Usage:
    pipenv run python voice_module.py   <- interactive mic tester
"""

import sys
import os
import json
import zipfile
import urllib.request
import threading
import pyaudio

# Force UTF-8 output so the terminal handles all characters
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Vosk model settings ──────────────────────────────────────────────
# Small model (~50MB): fast, good enough for command words
MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL  = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), MODEL_NAME)

SAMPLE_RATE    = 16000   # Hz  — required by all Vosk models
CHUNK_SIZE     = 4096    # Frames per read
LISTEN_SECONDS = 5       # Max listening time before giving up
# Bluetooth earbuds in HFP mode usually only support 8000 Hz.
# We try 16000 first; fall back to 8000 then upsample for Vosk.
FALLBACK_RATES = [16000, 8000]

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("[WARNING] Vosk not installed. Run: pipenv install vosk")


# ── Helpers ──────────────────────────────────────────────────────────

def _download_model():
    """Download and unzip the Vosk model if not already present."""
    if os.path.exists(MODEL_DIR):
        return  # Already downloaded

    zip_path = MODEL_DIR + ".zip"
    print(f"[VOICE] Vosk model not found. Downloading ({MODEL_NAME}) — ~50MB...")
    print("[VOICE] This only happens once. Please wait...")

    # Download with progress indicator
    def _reporthook(count, block_size, total_size):
        mb_done  = count * block_size / 1_000_000
        mb_total = total_size / 1_000_000
        print(f"\r  Downloading: {mb_done:.1f} / {mb_total:.1f} MB", end="", flush=True)

    urllib.request.urlretrieve(MODEL_URL, zip_path, reporthook=_reporthook)
    print("\n[VOICE] Download complete. Extracting...")

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(os.path.dirname(MODEL_DIR))

    os.remove(zip_path)
    print("[OK] Vosk model ready!")


# ── Main class ───────────────────────────────────────────────────────

class VoiceCommander:
    """
    Offline speech-to-text using Vosk.

    device_index : PyAudio device index (None = Windows default mic).
                   Run this file directly to see the full mic list and
                   find your index:  pipenv run python voice_module.py
    """

    def __init__(self, device_index=None, grammar=None):
        self.device_index = device_index
        self.grammar = grammar   # list of exact phrases to recognise, e.g. ['fist', 'i love you']
        self._model = None

        if not VOSK_AVAILABLE:
            print("[ERROR] Vosk is not installed. Voice features disabled.")
            return

        _download_model()

        print(f"[VOICE] Loading Vosk model '{MODEL_NAME}'...")
        self._model = Model(MODEL_DIR)
        print("[OK] Vosk model loaded. Ready for offline speech recognition.")

    # ── Mic helpers ──────────────────────────────────────────────────

    @staticmethod
    def list_microphones():
        """Print all available audio input devices."""
        p = pyaudio.PyAudio()
        print("\n" + "="*55)
        print("  AVAILABLE MICROPHONES")
        print("="*55)
        found = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:   # Input-only
                name = info['name']
                print(f"  [{i:>2}] {name}")
                found.append((i, name))
        print("="*55 + "\n")
        p.terminate()
        return found

    @staticmethod
    def _can_open_device(device_index, rate):
        """Try to briefly open a mic device. Returns True if it actually works."""
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=512,
            )
            stream.close()
            p.terminate()
            return True
        except Exception:
            p.terminate()
            return False

    @staticmethod
    def find_preferred_mic_index():
        """
        Auto-detect the best available mic that can actually be opened.
        Priority order:
          1. Wired headset (Realtek jack) — best quality
          2. Bluetooth earbuds / AirPods / TWS in HFP headset mode
          3. Any other working input device
          4. (None, None) → Windows system default mic (always works)

        Each candidate is TEST-OPENED to verify it really works before returning.
        Devices listed but not openable (e.g. Bluetooth in A2DP music mode) are skipped.
        """
        p = pyaudio.PyAudio()
        candidates = []   # list of (priority, index, name)

        print("[VOICE] Scanning microphones...")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) <= 0:
                continue
            name = info['name'].lower()
            full_name = info['name']

            # Priority 1 — Wired Realtek headset mic
            if 'realtek' in name and 'mic' in name and 'stereo' not in name:
                candidates.append((1, i, full_name))
                continue

            # Priority 2 — Bluetooth earbuds / headset (HFP mode has mic)
            is_bt = 'bthh' in name or any(k in name for k in [
                'headset', 'hands-free', 'handsfree', 'airpod', 'tws', 'buds'
            ])
            if is_bt:
                candidates.append((2, i, full_name))
                continue

            # Priority 3 — Any other input device (last resort before system default)
            candidates.append((3, i, full_name))

        p.terminate()

        # Sort by priority and test each one
        candidates.sort(key=lambda x: x[0])
        for priority, idx, name in candidates:
            # Try 16000Hz first, then 8000Hz (Bluetooth HFP fallback)
            for rate in FALLBACK_RATES:
                if VoiceCommander._can_open_device(idx, rate):
                    label = {1: "Wired mic", 2: "Earbuds/Bluetooth", 3: "Input device"}[priority]
                    print(f"[VOICE] {label} ready: [{idx}] {name} @ {rate}Hz")
                    return (idx, name)

        # Nothing worked — let Windows pick the default (None always works)
        print("[VOICE] No specific mic found — using Windows default mic")
        return (None, None)

    # Keep old name as alias so nothing breaks
    find_wired_mic_index = find_preferred_mic_index

    # ── Calibration (no-op for Vosk — noise-robust by design) ───────

    def calibrate(self, duration=0.8):
        """Vosk doesn't need calibration — it handles noise automatically."""
        mic_label = f"[{self.device_index}]" if self.device_index is not None else "[system default]"
        if self.grammar:
            print(f"[VOICE] Vosk ready with {len(self.grammar)} command(s) in grammar. Using mic {mic_label}")
        else:
            print(f"[VOICE] Vosk ready (free-form mode). Using mic {mic_label}")
        return True

    # ── Main recognition method ──────────────────────────────────────


    @staticmethod
    def get_device_sample_rate(device_index):
        """
        Probe which sample rate the mic actually supports.
        Tries 16000 Hz first (ideal for Vosk), then 8000 Hz (Bluetooth HFP fallback).
        Returns the first rate that works, or 16000 as default.
        """
        p = pyaudio.PyAudio()
        for rate in FALLBACK_RATES:
            try:
                supported = p.is_format_supported(
                    rate,
                    input_device=device_index,
                    input_channels=1,
                    input_format=pyaudio.paInt16
                )
                if supported:
                    p.terminate()
                    return rate
            except Exception:
                continue
        p.terminate()
        return 16000   # default if probing fails

    def listen_and_convert(self, should_calibrate=False):
        """
        Open the mic, listen for up to LISTEN_SECONDS seconds,
        and return the recognized text (or None on failure).
        Auto-detects sample rate so Bluetooth earbuds (8000Hz HFP) work too.
        """
        if not VOSK_AVAILABLE or self._model is None:
            print("[ERROR] Vosk model not loaded.")
            return None

        p = pyaudio.PyAudio()

        # Detect the actual sample rate this device supports
        device_rate = VoiceCommander.get_device_sample_rate(self.device_index)
        needs_upsample = (device_rate != SAMPLE_RATE)
        if needs_upsample:
            print(f"[MIC] Bluetooth earbuds detected at {device_rate}Hz — upsampling to {SAMPLE_RATE}Hz for Vosk")
        chunk = CHUNK_SIZE if not needs_upsample else CHUNK_SIZE // 2

        # Build recognizer — grammar mode if we have a vocabulary, else free-form
        if self.grammar:
            # Grammar must include '[unk]' so Vosk can return nothing instead of forcing a wrong match
            grammar_with_unk = list(self.grammar) + ["[unk]"]
            rec = KaldiRecognizer(self._model, SAMPLE_RATE, json.dumps(grammar_with_unk))
            print(f"[MIC] Grammar mode: {len(self.grammar)} known phrase(s)")
        else:
            rec = KaldiRecognizer(self._model, SAMPLE_RATE)

        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=device_rate,              # use actual device rate (8000 or 16000)
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=chunk,
            )
        except Exception as e:
            print(f"[ERROR] Could not open microphone [{self.device_index}] at {device_rate}Hz: {e}")
            p.terminate()
            return None

        print(f"\n[MIC] LISTENING... Speak clearly! (max {LISTEN_SECONDS}s)")

        result_text = ""
        total_chunks = int(device_rate / chunk * LISTEN_SECONDS)

        try:
            for _ in range(total_chunks):
                data = stream.read(chunk, exception_on_overflow=False)

                # Upsample 8000Hz -> 16000Hz for Vosk when using Bluetooth earbuds
                if needs_upsample:
                    import numpy as np
                    pcm = np.frombuffer(data, dtype=np.int16)
                    pcm = np.repeat(pcm, 2)   # simple 2x linear upsample
                    data = pcm.astype(np.int16).tobytes()

                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = res.get("text", "").strip()
                    if text:
                        result_text = text
                        break

            if not result_text:
                final = json.loads(rec.FinalResult())
                result_text = final.get("text", "").strip()

        except Exception as e:
            print(f"[ERROR] Listening error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        if result_text:
            print(f"[OK] Recognized: '{result_text}'")
            return result_text.lower()
        else:
            print("[WARNING] No speech detected.")
            return None


# ── Standalone tester ────────────────────────────────────────────────

if __name__ == "__main__":
    if not VOSK_AVAILABLE:
        print("[ERROR] Run: pipenv install vosk")
        sys.exit(1)

    print("\n--- Vosk Voice Tester ---\n")

    # Show input-only devices
    all_mics = VoiceCommander.list_microphones()

    # Auto-detect wired headset
    wire_idx, wire_name = VoiceCommander.find_wired_mic_index()
    if wire_idx is not None:
        print(f"[AUTO-DETECTED] Wired mic at [{wire_idx}]: {wire_name}")

    idx_str = input("Enter mic index to test (press Enter for system default): ").strip()
    idx = int(idx_str) if idx_str.isdigit() else None

    # Build grammar from gesture/sequence JSON files (same folder as this script)
    _base = os.path.dirname(os.path.abspath(__file__))
    _vocab = []
    for fname in ("gestures.json", "sequences.json"):
        fpath = os.path.join(_base, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r') as _f:
                    _data = json.load(_f)
                    _vocab.extend(list(_data.keys()))
            except Exception:
                pass
    _grammar = sorted(set(v.lower() for v in _vocab)) if _vocab else None
    if _grammar:
        print(f"[VOICE] Grammar loaded: {_grammar}")
    else:
        print("[VOICE] No grammar file found -- using free-form mode")

    vc = VoiceCommander(device_index=idx, grammar=_grammar)
    vc.calibrate()

    print("\nSpeak a gesture name now (e.g. 'fist', 'open', 'i love you')...")
    result = vc.listen_and_convert()
    print(f"\nFinal result: '{result}'")
