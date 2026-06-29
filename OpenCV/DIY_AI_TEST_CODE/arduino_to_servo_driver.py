import serial
import serial.tools.list_ports
import json
import time

class ArduinoServoDriver:
    """
    Handles serial communication between Python and ESP32/Arduino.
    Sends servo angles as comma-separated string: Thumb,Index,Middle,Ring,Pinky,Wrist\n
    """
    def __init__(self, port='COM5', baudrate=115200, timeout=1, debug=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.debug = debug
        self._send_count = 0
        self._last_send = 0.0   # timestamp of last successful send (rate limiter)
        
        try:
            self.connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for ESP32/Arduino to reset after serial open
            print(f"[OK] Connected to ESP32/Arduino on {self.port} @ {self.baudrate} baud")
        except Exception as e:
            print(f"[ERROR] SERIAL: Could not connect to {self.port}.")
            print(f"        Details: {e}")
            print(f"        Available ports: {[p.device for p in serial.tools.list_ports.comports()]}")

    def send_angles(self, angles_dict):
        """
        Sends 6 angles in format: Thumb,Index,Middle,Ring,Pinky,Wrist\n
        At 115200 baud, 30fps uses only 8% of bandwidth — no rate limiting needed.
        """
        if not (self.connection and self.connection.is_open):
            return

        order = ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]
        angle_list = [str(angles_dict.get(name, 90)) for name in order]
        data_string = ",".join(angle_list) + "\n"

        try:
            self.connection.write(data_string.encode())
            self._send_count += 1

            # Debug: print every 10th message to verify values without flooding terminal
            if self.debug and self._send_count % 10 == 0:
                print(f"[SERIAL >>] {data_string.strip()}")

        except Exception as e:
            print(f"[ERROR] Failed to send serial data: {e}")

    def close(self):
        if self.connection:
            self.connection.close()


# ── Quick standalone test ──────────────────────────────────────────────
# Run this file directly to scan ports and send a test sweep to all servos.
if __name__ == "__main__":
    print("\n=== Serial Port Scanner ===")
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found!")
    else:
        for p in ports:
            print(f"  {p.device:8s}  {p.description}")

    port_name = input("\nEnter COM port to test (e.g. COM5): ").strip() or "COM5"
    baud = input("Enter baud rate (press Enter for 9600): ").strip()
    baud = int(baud) if baud.isdigit() else 9600

    driver = ArduinoServoDriver(port=port_name, baudrate=baud, debug=True)
    if driver.connection:
        print("\nSending REST positions to all 6 servos...")
        rest = {"Thumb": 175, "Index": 90, "Middle": 100, "Ring": 100, "Pinky": 85, "Wrist": 150}
        driver.send_angles(rest)
        time.sleep(1)

        print("Sending OPEN positions...")
        open_pos = {"Thumb": 175, "Index": 90, "Middle": 100, "Ring": 100, "Pinky": 85, "Wrist": 150}
        driver.send_angles(open_pos)
        time.sleep(1)

        print("Sending CLOSE positions...")
        close_pos = {"Thumb": 285, "Index": 290, "Middle": 290, "Ring": 290, "Pinky": 290, "Wrist": 150}
        driver.send_angles(close_pos)
        time.sleep(2)

        print("Back to rest...")
        driver.send_angles(rest)
        driver.close()
        print("Done.")
