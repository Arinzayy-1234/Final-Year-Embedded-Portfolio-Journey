# 🤖 Arduino I²C Master-Slave Communication Project

This project demonstrates reliable two-way communication between two Arduino Uno boards using the **I²C (Inter-Integrated Circuit)** protocol, managed by the standard **Wire Library**.

The Master Arduino (ARD1) continuously requests 6 bytes of data from the Slave Arduino (ARD2, Address 8), and the Slave responds with the fixed message "HelloY".

## 🔌 Hardware Setup (Proteus/Physical Wiring)

The I²C protocol requires only two data wires, plus a common ground reference.

|Wire Name|Master (ARD1) Pin|Slave (ARD2) Pin|Notes|
|---|---|---|---|
|**SDA** (Serial Data)|**A4** (Analog 4)|**A4** (Analog 4)|The data line.|
|**SCL** (Serial Clock)|**A5** (Analog 5)|**A5** (Analog 5)|The synchronization clock line.|
|**GND** (Ground)|**GND**|**GND**|**Crucial:** Must be connected to a shared **GROUND Terminal** in Proteus.|

## ⚙️ 1. Slave Code (`arduino_slave.ino`)

The Slave device (Address **8**) is a passive sender. Its primary job is to wait for the Master to make a request and then execute the `requestEvent()` function to send data.

### Key Logic

- `Wire.begin(8);`: Initializes this board as a Slave with the unique address `8`.
    
- **`Wire.onRequest(requestEvent);`**: Registers a function that only runs _when_ the Master requests data.
    
- **`Wire.write("HelloY");`**: Sends the 6-byte payload over the I²C bus.
    

```
// Sender Reciever Arduino Demo

#include <Wire.h>

void setup() {
  Wire.begin(8); // Initializes the Slave device with unique I2C address 8.
  Wire.onRequest(requestEvent); 
  
  // DEBUGGING SETUP
  Serial.begin(9600); 
  Serial.println("Slave 8 is active.");
}

void loop() {
  // Slave is passive, the loop does minimal work.
  delay(100); 
}

void requestEvent()
{
  // This sends exactly 6 bytes to match the Master's request.
  Wire.write("HelloY"); 
  
  // Debugging: Confirms that the function was successfully triggered.
  Serial.println("Data requested and sent!"); 
}
```

## 🎯 2. Master Code (`arduino_master.ino`)

The Master device initiates communication and reads the response from the Slave.

### Key Logic

- **`Wire.begin();`**: Initializes the board as the Master (no address needed).
    
- **`Wire.requestFrom(8, 6);`**: Sends the command: "Request **6 bytes** from the device at address **8**."
    
- **`while(Wire.available())`**: Ensures the Master reads every single byte that the Slave sends, preventing data loss.
    
- **`Serial.write(c);`**: Sends the raw byte received from the I²C bus directly to the Serial Terminal for accurate printing.
    

```
// Master Reader Arduino Demo

#include <Wire.h>

void setup() {
  // Sets up the hardware pins (A4/A5) for I2C communication.
  Wire.begin(); 
  Serial.begin(9600);
}

void loop() {
  // Request 6 bytes from the Slave device with address 8
  Wire.requestFrom(8,6); 

  // Read all available bytes from the internal buffer
  while(Wire.available()) {
    char c = Wire.read();
    
    // Prints the raw character (byte) received to the Serial Terminal
    Serial.write(c); 
  }
  
  Serial.println(); // Newline for clean, separated output
  delay (500);      // Delay to stabilize serial output between requests
}
```

## 💡 Troubleshooting & Key I²C Concepts

If you experience garbled or corrupted text (e.g., "YYOLLYY"), verify the following:

### 1. **Baud Rate Match**

The `Serial.begin(9600);` in the code must exactly match the speed setting (9600 bps) on your Proteus Virtual Terminal.

### 2. **Byte Count Match (Critical!)**

The number of bytes the **Master requests** must match the number of bytes the **Slave sends**.

- **Master:** `Wire.requestFrom(8, **6**);` (Requests 6 bytes)
    
- **Slave:** `Wire.write("HelloY");` (Sends exactly 6 bytes)
    

### 3. **`print()` vs. `write()`**

- **`Serial.print()`**: Converts numbers to multiple human-readable character digits (e.g., 123 becomes '1', '2', '3').
    
- **`Serial.write()`**: Sends the literal, raw byte value. **This is used for I²C data** to ensure the raw ASCII character is displayed correctly, preventing conversion issues.
    

This project provides a robust foundation for building more complex I²C sensor networks!