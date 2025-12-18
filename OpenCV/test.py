import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
import sys

# Explicitly import the solutions submodule to bypass the AttributeError
from mediapipe.python.solutions import pose as mp_pose

print("--- Python Environment Check ---")
print(f"Python Executable: {sys.executable}")
print(f"OpenCV Version: {cv2.__version__}")

# Initialize using the explicit submodule import
try:
    # Use mp_pose instead of mp.solutions.pose
    pose_tracker = mp_pose.Pose()
    print("MediaPipe Pose initialized successfully.")
except Exception as e:
    print(f"MediaPipe Initialization Error: {e}")

# Create a small NumPy array to verify NumPy
arr = np.array([1, 2, 3])
print(f"NumPy array created: {arr}")

# Basic TensorFlow check
if tf.config.list_physical_devices('GPU'):
    print("TensorFlow (GPU) is ready.")
else:
    print("TensorFlow (CPU) is ready.")

print("\nSUCCESS: All core packages imported correctly!")