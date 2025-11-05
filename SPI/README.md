SHIFT REGISTERS USING HARDWARE SPI

FOR MORE INFO. 👇

NOTION -> https://www.notion.so/SELF-MADE-Q-AND-A-25eaa6242c27802c9223f5659c5d3be0?source=copy_link#2a2aa6242c278007af3cf847de60449e
PROTUES -> SPI_ShiftRegisters


OVERVIEW

This project demonstrates the use of the Hardware SPI (Serial Peripheral Interface) protocol on an Arduino Uno to drive a 74HC595 Shift Register.

This code prioritizes efficiency by utilizing the dedicated SPI hardware (SPI.transfer()) instead of the slower, software-based shiftOut() function. The result is a simple, high-speed 8-bit binary counter displayed across 8 LEDs.

HARDWARE CONNECTIONS (ARDUINO UNO TO 74HC595)

The hardware SPI protocol requires specific pins to be used on the Arduino Uno. Note that the Clock (SCK) and Data (MOSI) pins are fixed by the Arduino hardware, simplifying the code.

1. D13 (SCK / Clock) connects to SH_CP (Shift Clock) on the 74HC595.

Purpose: Synchronizes data transfer.

2. D11 (MOSI / Data) connects to DS (Data) on the 74HC595.

Purpose: Sends the 8-bit value to the register.

3. D2 (SS / Latch) connects to ST_CP (Latch Clock) on the 74HC595.

Purpose: Latches the data to the outputs.

4. D10 (N/A) must be set as OUTPUT for Master Mode Safety.

CODE EXPLANATION

1. Initialization (setup() Function)

The setup routine configures the Arduino to operate as the SPI Master.

pinMode(slaveSelect, OUTPUT): Configures the user-defined Latch/SS pin (Pin 2) to control the 74HC595's data display.

pinMode(10, OUTPUT): Sets the default hardware Slave Select pin (D10) as an output. This is a critical step to ensure the Arduino remains in Master Mode.

SPI.begin(): Initializes and activates the dedicated SPI hardware (D11 and D13).

SPI.setBitOrder(LSBFIRST): Sets the data transfer to send the Least Significant Bit (LSB) first. This means for a binary count, the LED connected to the shift register's Q0 pin will be the one that lights up first, representing the '1's place.

2. The Main Loop (loop() Function)

The loop iterates through every 8-bit value from 0 to 255.

for (int i = 0 ; i < 256 ; i ++): The counter loop. i represents the decimal value to be displayed in binary.

digitalWrite(slaveSelect, LOW): Pulls the Latch/SS pin LOW to signal the shift register to begin accepting the 8 incoming data bits.

SPI.transfer(i): Sends the 8-bit representation of the integer i over the MOSI and SCK lines.

digitalWrite(slaveSelect, HIGH): Pulls the Latch/SS pin HIGH. This moves the data from the shift register's internal memory to the output pins (Q0-Q7), instantly updating the LED display.

delay(delayTime): Controls the speed of the counter (set to 1000ms in this version).