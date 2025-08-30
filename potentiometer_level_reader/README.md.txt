potentiometer_level_reader; Proteus Patner -> potentiometer_Button_and_Led.ino

This sketch demonstrates how to read an analog value from a potentiometer and then print a specific message to the Serial Monitor based on the potentiometer's position.

How it Works
The sketch reads a value from the potentiometer, which is an analog sensor that changes its resistance as you turn it. The analogRead() function reads this value, which can range from 0 to 1023.

The code then divides this value by 255 to scale it down into a more manageable range of 0 to 4.

A switch statement is used to check the scaled value and print a corresponding message. This allows you to easily understand the potentiometer's position without having to look at the raw numbers.

The if (potValue != lastPotValue) check prevents the program from continuously printing the same message to the Serial Monitor, making the output cleaner and easier to read.

Components Needed
Arduino Board

Potentiometer

Breadboard

Jumper Wires