FOR MORE INFO. 👇
https://www.notion.so/ARDUINO-INTRO-24faa6242c2780fba269c377f3dd08e8?source=copy_link#283aa6242c2780838968e91a85f56a18

PROTEUS DESIGN PROJECT NAME -> Button_and_Led

# 🚀 Arduino Button-Controlled LED with Interrupts and Debouncing

This project demonstrates a reliable method for controlling an LED using a physical push button. It uses **external interrupts** for immediate, high-priority detection of the button press, and implements robust **software debouncing** within the main program loop to ensure the LED only toggles once per intentional press.

## 🛠️ Components Required

- **Arduino Board** (e.g., Uno, Nano)
    
- **1 x Push Button**
    
- **1 x LED**
    
- **1 x 220 Ohm Resistor** (for the LED)
    
- **Jumper Wires**
    

## 📌 Wiring and Schematics

The button is connected to Pin 2, which is an external interrupt pin. We use the internal pull-up resistor, simplifying the wiring.

|**Component**|**Arduino Pin**|**Notes**|
|---|---|---|
|**LED** (Anode/Long Leg)|Digital Pin **13**|Connect the Cathode (short leg) to GND via a 220 $\Omega$ resistor.|
|**Push Button**|Digital Pin **2**|This is **Interrupt 0** on the Arduino Uno.|
|**Push Button**|GND (Ground)|Uses the internal `INPUT_PULLUP` setting.|

## 💻 Code Architecture and Explanation

The core architecture relies on the crucial distinction between the Interrupt Service Routine (ISR) and the main loop logic.

### 1. Variables and Configuration

|**Variable/Setting**|**Value/Type**|**Purpose in Code**|
|---|---|---|
|`buttonPin`|`2`|Must be an external interrupt pin.|
|`ledPin`|`13`|Standard output pin.|
|`debounceTime`|`20` (ms)|Time needed for the button contacts to settle.|
|`buttonFlag`|`volatile int`|The single-bit signal passed from the ISR to the main loop. **`volatile`** is critical for this variable.|
|`attachInterrupt()`|`CHANGE`|Triggers the ISR on both press (HIGH $\rightarrow$ LOW) and release (LOW $\rightarrow$ HIGH).|

### 2. The Interrupt Service Routine (ISR)

C

```
void ISR_button()
{
  buttonFlag = 1;
}
```

- **Purpose:** This function serves as the **trigger**.
    
- **Execution:** When the button state changes, the CPU halts the main `loop()` and immediately executes this routine.
    
- **Action:** It performs only one task: setting the global `buttonFlag` to `1`. This is done to ensure the ISR is **minimal and fast**, preventing missed interrupts.
    

### 3. The Main Program Loop (`loop()`)

The `loop()` function handles all the complex logic, running only after the ISR has signaled an event and the debouncing time has passed.

C

```
// Check 1: Debounce Time Check | Check 2: ISR Flag Check
if ((millis() - lastPress > debounceTime) && buttonFlag)
{
    // ... logic to read pin, toggle LED, update lastButtonState ...
    buttonFlag = 0; // Clear the flag for the next interrupt
}
```

- **Debouncing Check:** It verifies that a minimum of 20 milliseconds (`debounceTime`) has elapsed since the last valid button action. This prevents the bouncy mechanical signal of the button from triggering the LED multiple times.
    
- **Toggle Logic:** The code then checks the precise state of the button (pressed or released) and toggles the LED (`toggleState =! toggleState;`) only when a true press is detected.
    
- **Flag Reset:** Finally, it clears `buttonFlag = 0;`, acknowledging the event and preparing the system for the next interrupt signal.
    

## 🚀 Getting Started

1. Connect your components as described in the **Wiring and Schematics** section.
    
2. Copy the code into your Arduino IDE.
    
3. Upload the sketch to your Arduino board.
    
4. Press the button to toggle the LED ON and OFF reliably.