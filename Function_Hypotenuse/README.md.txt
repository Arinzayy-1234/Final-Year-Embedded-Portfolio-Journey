Serial Hypotenuse Calculator
This Arduino sketch uses the Serial Monitor to take two side lengths from the user and calculates the hypotenuse (c) of the resulting right-angle triangle using the Pythagorean theorem (A-squared plus B-squared equals C-squared).

1. How to Use
Open the sketch in the Arduino IDE.

Upload the code to your Arduino board.

Open the Serial Monitor and ensure the baud rate is set to 9600.

The program will prompt you to enter the two side values one at a time.

2. Key Code Components
The program is broken into three main functions:

void setup(): Initialization. Starts the Serial communication channel at 9600 baud.

int readSerial(): Input & Validation. Reads the user's input, converts it to an integer, and verifies that the number is positive and whole. If the input is invalid, it returns a 0 error signal.

void findSide(): Calculation. Takes the two validated numbers, performs the calculation, and prints the final result to the Serial Monitor.

void loop(): User Flow. Prompts the user, uses a blocking loop (while(!Serial.available());) to wait for input, and checks the error signal (if (a == 0)) to restart the process if input failed.

3. Error Handling
The code includes robust error handling:

Input Check (readSerial): Rejects any negative, zero, or non-integer input.

Loop Restart (loop): If an error is detected, the return; command immediately restarts the loop() function, prompting the user for input again instead of continuing with an invalid number.

FOR MORE INFO. 👇
https://www.notion.so/ARDUINO-INTRO-24faa6242c2780fba269c377f3dd08e8?source=copy_link#283aa6242c2780838968e91a85f56a18