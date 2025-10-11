ARDUINO PROJECT: LED SEQUENTIAL LIGHT ARRAY

PROTEUS DESIGN PROJECT NAME -> Array_of_Leds

This project controls a series of 8 LEDs to create a "chase" or progression lighting effect. It uses an array to manage the pins efficiently, demonstrating fundamental control flow in embedded programming.

HARDWARE SETUP

You must connect 8 LEDs to the following digital pins. Each LED requires a current-limiting resistor (e.g., 220 Ohm).

LED 1: Pin 2

LED 2: Pin 3

LED 3: Pin 4

LED 4: Pin 5

LED 5: Pin 6

LED 6: Pin 7

LED 7: Pin 8

LED 8: Pin 9

CODE COMPONENTS

GLOBAL VARIABLES:

int ledArray[]: Stores the digital pin numbers (2 through 9).

int delayTime: Sets the speed of the animation (150 milliseconds).

void setup():

A for loop iterates through the 'ledArray' and sets all 8 corresponding pins to OUTPUT mode using pinMode().

void loop():

Loop 1 (ON Progression): A 'for' loop iterates forward (0 to 7), setting each pin HIGH sequentially to turn the LEDs on one by one.

Loop 2 (OFF Progression): A second 'for' loop iterates backward (7 to 0), setting each pin LOW sequentially to turn the LEDs off one by one.

SKILLS DEMONSTRATED

Array Management: Using an array to group and manage hardware resources (pins).

Code Efficiency: Employing 'for' loops to replace 8 redundant pinMode() calls and 16 redundant digitalWrite() calls.

Control Flow: Using forward (i++) and backward (i--) iteration to create distinct patterns.