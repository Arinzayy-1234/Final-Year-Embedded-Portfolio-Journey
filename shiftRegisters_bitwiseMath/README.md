

**README - Arduino Shift Register LED Control**

This sketch allows you to control 8 LEDs connected via a shift register using bitwise operations (AND, OR, XOR). You input a number between 0 and 255 via Serial Monitor, and the code displays the binary result of each operation and updates the LEDs accordingly.

---

**Code Overview**

- `const int dataPin = 6;`
- `const int clockPin = 7;`
- `const int latchPin = 8;`

> **Why use `const`?**  
> These pin numbers never change, so `const` ensures they stay fixed and helps optimize memory.

- `byte ledMap = 0b11111111;`

> **What is `0b`?**  
> It's a binary literal prefix in Arduino.  
> `0b11111111` = 255 in decimal = `0xFF` in hexadecimal.

> **Why use `byte` instead of `int`?**  
> `byte` uses 1 byte (8 bits), while `int` uses 2 bytes.  
> Saves memory when only 8 bits are needed.

- `pinMode(dataPin, OUTPUT);`

> **Why OUTPUT if it receives data?**  
> The Arduino sends data *out* to the shift register, so the pin must be set as OUTPUT.

- `shiftWrite(0x00);`

> **What is `0x00`?**  
> It's a hexadecimal value meaning all bits are 0.  
> This turns off all LEDs initially.

- `Serial.println("Enter a number btw 0 and 255");`

> **Why between 0 and 255?**  
> 8 bits can represent values from 0 to 255.  
> Each bit controls one LED.

- `Serial.println(inputVal, BIN);`

> **Why not use `bin(inputVal)`?**  
> Arduino uses `Serial.println(val, BIN)` to print binary.  
> `bin()` is not valid in Arduino C/C++.

- `Serial.println(ledMap & inputVal, BIN);`

> **What does this do?**  
> Performs a bitwise AND between `ledMap` and `inputVal`.  
> Result is shown in binary.

- `shiftWrite(ledMap & inputVal);`

> **What does this do?**  
> Sends the result to the shift register to update LEDs.

---

**Function Explanation**

```cpp
void shiftWrite(byte value)
{
  digitalWrite(latchPin, LOW); // Open latch gate
  shiftOut(dataPin, clockPin, MSBFIRST, value); // Send bits one by one
  digitalWrite(latchPin, HIGH); // Close latch gate, update LEDs
}
```

> **What is `byte value`?**  
> It's the 8-bit data to send to the shift register.  
> Each bit controls one LED (1 = ON, 0 = OFF).

---

**How It Works**

1. User inputs a number (0–255).
2. Code performs AND, OR, XOR with `ledMap`.
3. Results are printed in binary.
4. LEDs are updated to show each result.

---

Let me know if you'd like this saved as a file or want to add comments directly into the code!
