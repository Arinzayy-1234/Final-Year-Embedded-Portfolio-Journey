"""
rawMp.py  -  AI Hand Detection Engine (MediaPipe Tasks API)
===========================================================
Uses the modern MediaPipe Tasks HandLandmarker in VIDEO mode
for fast, temporally-stable hand tracking from a webcam feed.
"""

import os
import sys
import time
import cv2
import numpy as np
import urllib.request
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ──────────────────────────────────────────────────
#  HAND SKELETON CONNECTIONS (for drawing)
# ──────────────────────────────────────────────────
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),                  # Thumb
    (5, 6), (6, 7), (7, 8),                           # Index
    (9, 10), (10, 11), (11, 12),                      # Middle
    (13, 14), (14, 15), (15, 16),                     # Ring
    (17, 18), (18, 19), (19, 20),                     # Pinky
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17),      # Palm base
]

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)


class RawHandDetector:
    """
    High-level hand detector powered by MediaPipe Tasks API.

    Usage:
        detector = RawHandDetector()
        frame = detector.find_hands(frame, draw=True)
        landmarks = detector.find_position(frame)
    """

    def __init__(self, mode=False, max_hands=2,
                 detection_con=0.5, track_con=0.5):
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        self.hand_data = None        # latest detection result
        self._last_ts = 0            # monotonic timestamp tracker

        # ── Locate / download the model file ──
        model_filename = "hand_landmarker.task"
        self.model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), model_filename
        )
        self._ensure_model()

        # ── Create the HandLandmarker in VIDEO mode ──
        base_options = python.BaseOptions(
            model_asset_path=self.model_path
        )
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.detection_con,
            min_hand_presence_confidence=self.track_con,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        print("[OK] HandLandmarker ready  (VIDEO mode, "
              f"det={self.detection_con}, trk={self.track_con})")

    # ──────────────────────────────────────────────
    def _ensure_model(self):
        """Download the model if missing or corrupted."""
        need_download = False

        if not os.path.exists(self.model_path):
            need_download = True
        else:
            size = os.path.getsize(self.model_path)
            if size < 1_000_000:           # model should be ~10 MB
                print(f"[WARNING] Model file is only {size} bytes "
                      "- likely corrupt. Re-downloading...")
                os.remove(self.model_path)
                need_download = True

        if need_download:
            print("[Download] Fetching hand_landmarker.task ...")
            try:
                urllib.request.urlretrieve(MODEL_URL, self.model_path)
                final_size = os.path.getsize(self.model_path)
                print(f"[OK] Model downloaded ({final_size:,} bytes)")
            except Exception as e:
                print(f"[FATAL] Model download failed: {e}")
                raise

    # ──────────────────────────────────────────────
    def find_hands(self, frame, draw=True):
        """
        Run hand detection on *frame* (BGR numpy array).
        Stores results internally and optionally draws the skeleton.
        Returns the (possibly annotated) frame.
        """
        # Monotonically increasing timestamp (milliseconds)
        now_ms = int(time.monotonic() * 1000)
        ts = max(self._last_ts + 1, now_ms)
        self._last_ts = ts

        # Convert BGR -> RGB and wrap for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB, data=frame_rgb
        )

        # Detect
        try:
            self.hand_data = self.detector.detect_for_video(mp_image, ts)
        except Exception as e:
            print(f"[Detection Error] {e}")
            self.hand_data = None
            return frame

        # ── Draw skeleton + status overlay ──
        h, w, _ = frame.shape

        if self.hand_data and self.hand_data.hand_landmarks:
            num = len(self.hand_data.hand_landmarks)
            cv2.putText(frame, f"HANDS: {num}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)

            if draw:
                for hand_lms in self.hand_data.hand_landmarks:
                    # connections
                    for s, e in HAND_CONNECTIONS:
                        p1 = hand_lms[s]
                        p2 = hand_lms[e]
                        x1, y1 = int(p1.x * w), int(p1.y * h)
                        x2, y2 = int(p2.x * w), int(p2.y * h)
                        cv2.line(frame, (x1, y1), (x2, y2),
                                 (0, 255, 0), 2)
                    # joints
                    for lm in hand_lms:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(frame, (cx, cy), 5,
                                   (255, 0, 255), cv2.FILLED)
        else:
            cv2.putText(frame, "NO HAND DETECTED",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 255), 2)

        return frame

    # ──────────────────────────────────────────────
    def find_position(self, frame, hand_indexes=[0], draw=False):
        """
        Extract pixel-coordinate landmarks for requested hand(s).
        Returns a list of [id, x, y] entries (empty list if no hand).
        """
        landmark_list = []
        if not self.hand_data or not self.hand_data.hand_landmarks:
            return landmark_list

        h, w, _ = frame.shape
        for hand_index in hand_indexes:
            if hand_index < len(self.hand_data.hand_landmarks):
                for idx, lm in enumerate(
                        self.hand_data.hand_landmarks[hand_index]):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cz = int(lm.z * w)  # Scale depth by width to keep X/Y/Z coordinate scales matching
                    landmark_list.append([idx, cx, cy, cz])
                    if draw:
                        cv2.circle(frame, (cx, cy), 5,
                                   (255, 0, 255), cv2.FILLED)

        return landmark_list
