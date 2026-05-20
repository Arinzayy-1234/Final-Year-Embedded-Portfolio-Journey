import serial
import json
import time

class ArduinoServoDriver:
    """
    Handles serial communication between Python and Arduino Mega.
    Sends servo angles as a comma-separated string or JSON.
    """
    def __init__(self, port='COM3', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        
        try:
            self.connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2) # Wait for Arduino to reset
            print(f"✅ Connected to Arduino on {self.port}")
        except Exception as e:
            print(f"❌ SERIAL ERROR: Could not connect to {self.port}. Check your USB connection.")
            print(f"Technical details: {e}")

    def send_angles(self, angles_dict):
        """
        Sends angles in format: Thumb,Index,Middle,Ring,Pinky,Wrist\n
        Example: 20.0,160.0,160.0,155.0,145.0,90.0\n
        """
        if self.connection and self.connection.is_open:
            # Order must match what the Arduino expects!
            order = ["Thumb", "Index", "Middle", "Ring", "Pinky", "Wrist"]
            angle_list = [str(angles_dict.get(name, 90)) for name in order]
            data_string = ",".join(angle_list) + "\n"
            
            try:
                self.connection.write(data_string.encode())
            except Exception as e:
                print(f"❌ Failed to send data: {e}")
        else:
            # Silent fail if not connected so it doesn't crash the main loop
            pass

    def close(self):
        if self.connection:
            self.connection.close()

# Usage Example:
# driver = ArduinoServoDriver(port='COM3')
# driver.send_angles({'Thumb': 20, 'Index': 160, ...})
