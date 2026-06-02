# ⚙️ InMoov Cybernetic Arm & 3D Virtual Hand Simulator ⚙️

Welcome to the **InMoov Cybernetic Hand & Visual Portfolio Simulator**! This is a state-of-the-art, real-time AI-powered robotic arm tracking and visualization system. Designed with a premium **Emerald Green Victorian Gaslight / Steampunk** aesthetic, it features rotating clockwork gears, an Arc Reactor core, real-time visual telemetry, and physical servo-motor mirroring.

The system captures your real hand movements via webcam and maps them seamlessly onto a virtual robotic hand and an Arduino-controlled physical hand with cinematic smoothness and precision.

---

## 🎨 Aesthetic Design & Features
*   **Victorian Steampunk Theme**: Rich brass and cast iron construction paired with a vibrant glowing emerald-green gaslight theme.
*   **Articulated Mechanical Gears**: Multiple rotating gears inside the palm, forearm, and Arc Reactor core rotate in real-time, scaling their speeds with hand activity.
*   **Arc Reactor Core**: A pulsing, glowing central energy reactor in the palm of the hand.
*   **Holographic HUD**: Built-in visual telemetry display that details the status of the neural bridge, current system mode, and individual finger servo angles.
*   **3D Perspective & Joint Physics**: Features 3D perspective foreshortening as fingers bend, making joints and phalanxes fold naturally inward like a real hand.

---

## 🚀 Key Technical Architecture

### 1. High-Performance tracking (`rawMp.py`)
Powered by **MediaPipe Tasks API** in `VIDEO` mode, the tracking engine captures 21 landmarks of your hand with high temporal stability and extremely low latency.

### 2. Intelligent Gesture Module (`gesture_module.py`)
The main "brain" of the tracking pipeline, responsible for:
*   **Dynamic Auto-Calibration**: Instantly auto-tunes the open/closed limits for each finger to fit the user's hand size and distance from the webcam as soon as you wave.
*   **Subtle Lateral Spread**: Restricts side-to-side movement to a realistic mechanical `±3.0°` to prevent unrealistic joint flexibility.
*   **Signal Smoother (Cinematic Alpha Filter)**: Removes tracking jitters using an exponential moving average (alpha) to deliver ultra-smooth movements.
*   **Speech Recognizer**: Integrated Voice Module to listen to spoken commands (e.g., "open", "fist", "victory") and command the hand dynamically.

### 3. Hardware Bridge (`arduino_to_servo_driver.py`)
Translates software calculations into serial signals sent directly to an Arduino Mega to control physical robotic servos in real-time.

---

## ⌨️ Control Schemes & Hotkeys

### Interactive UI Keys (Pygame Window)
*   `[F]` — **Horizontal Flip Toggle**: Instantly mirrors the virtual hand to match your webcam setup (left-hand/right-hand mirroring).
*   `[M]` — **Override Mode Toggle**: Switch between **LIVE tracking** and **MANUAL override**. In manual mode, you can adjust the bottom sliders with your mouse.
*   `[ESC]` — **Exit Program**: Safely shuts down the renderer and closes the serial socket.

### Diagnostic & Gesture Keys (OpenCV Window)
*   `[O]` — Capture a frame to calibrate the **Open Hand** baseline.
*   `[C]` — Capture a frame to calibrate the **Closed Hand** baseline.
*   `[S]` — Save/Sync captured baselines to lock calibration.
*   `[K]` — Save the current hand pose to the permanent SQLite/JSON database as a gesture.
*   `[T]` — Execute a stored gesture by typing its name in the console.
*   `[V]` — Activate the Voice Listening module for spoken commands.
*   `[Q]` — Quit the program safely.

---

## 🛠️ Installation & Getting Started

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. Install the required libraries:
```bash
pip install opencv-python mediapipe pygame pyserial numpy
```

To enable the voice control features, also install:
```bash
pip install SpeechRecognition pyaudio
```

### 2. Running the System
Always run the `gesture_module.py` script, which launches both the AI tracking pipeline and the Pygame simulator:
```bash
python OpenCV/DIY_AI_TEST_CODE/gesture_module.py
```

*Note: If no physical Arduino is connected, the program will automatically notify you and run purely in virtual simulation mode without crashing.*

---

## 📐 Custom Servo Mappings
The system maps mechanical ranges precisely according to physical servo limits to prevent structural binding:
*   **Thumb**: `175°` (Open) to `285°` (Closed)
*   **Index**: `90°` (Open) to `290°` (Closed)
*   **Middle**: `100°` (Open) to `290°` (Closed)
*   **Ring**: `100°` (Open) to `290°` (Closed)
*   **Pinky**: `85°` (Open) to `290°` (Closed)
*   **Wrist**: `0°` to `300°` (Centered straight-up at `150°`)
