EEPROM Event Counter Project README
FOR MORE INFO. 👇
https://www.notion.so/SELF-MADE-Q-AND-A-25eaa6242c27802c9223f5659c5d3be0?source=copy_link#296aa6242c2780019a43efa1bfd2cfe2

Proteus cct -> EEPROM_Event_Counter

Needs Review

1. I still don't fully understand the logic that requires a consecutive reset (two quick restarts) to truly start the counter from 0. I need to review the concept that the first reset loads the old count but wipes the memory for the next time, and the second reset loads the fresh 0 that the first one saved.

2. The LED in the cct. is not working.

EEPROM EVENT COUNTER PROJECT 

===================================
A reliable event counter using EEPROM for persistence and debouncing for accuracy.

1. Project Overview

This Arduino sketch implements a reliable event counter. Its main function is to use a single push button to increment a count, while using the Arduino's internal EEPROM (Electrically Erasable Programmable Read-Only Memory) to save the total count. This ensures the data persists even when the power is disconnected.

Key Features:

Persistent Counting: The counter value is saved permanently.

Debouncing: Ensures one button press equals one count.

Visual Feedback: An LED flashes when the button is successfully pressed.

2. Hardware Setup

The components should be wired as follows:

Push Button: Connects Digital Pin 2 to Ground (GND). (Uses internal PULLUP resistor.)

LED: Connects Digital Pin 12 to Ground, through a current-limiting resistor (e.g., 280 ohm or 100 ohm for simulation).

3. Key Code Logic Explanation

A. EEPROM Initialization in setup()

This is the most critical part of the code, handling data persistence and the controlled reset.

Read Saved Count:
CODE: counter = EEPROM.read(0);
EXPLANATION: This line checks the first memory slot (address 0) in the EEPROM and loads that number into the temporary counter variable in RAM. This allows the count to continue from where it left off after a power failure.

Initial EEPROM Wipe (The Reset Trick):
CODE: EEPROM.write(0, 0);
EXPLANATION: This immediately writes the value 0 into the first memory slot (address 0) of the permanent EEPROM memory. This line sets up the ability to perform a clean reset.

B. Counting and Debouncing in loop()

Debouncing: The condition (millis() - lastPress) > 20 prevents a single physical button press from registering multiple electrical "bounces" as separate clicks.

Counting: The count increments only when the button state changes from released to pressed (buttonState == 0 && lastButtonState == 1).

Saving: The new counter value is immediately saved to permanent storage: EEPROM.write(0, counter);.