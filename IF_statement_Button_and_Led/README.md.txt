This project centres on how to use the if statement. It creates circuit where when the button is pressed the Led goes ON and when it is pressed again it goes OFF

### The Code Explained 📄

```cpp

int ledPin = 12;
int buttonPin = 2;

int toggleState = 0; //  it keeps track of the LED's current state.
int lastButtonState = 1; // The previous button state
long unsigned int lastPress = 0; // The last time the button was pressed
int debounceTime = 20; // set to 20 milliseconds to ignore the tiny, unwanted bounces that happen when you press a physical button.



void setup() {
  // put your setup code here, to run once:

  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
}

void loop() {
  // put your main code here, to run repeatedly:
  int buttonState = digitalRead(buttonPin);
  if ((millis() - lastPress) > debounceTime) // if the debouncing Time has passed (the time has passed 20mili seconds)
  {
    lastPress = millis();
    if (buttonState == 0 && lastButtonState == 1) // Checkes if the button is pressed -> is like animating not pressing (lastButtonState  = 1) the button then pressing (buttonState = 0) it and
    {
      toggleState =! toggleState;
      digitalWrite(ledPin, toggleState);
      lastButtonState = buttonState;
    }
    if (buttonState == 1 && lastButtonState == 0) //  Checkes if the button is not pressed -> is like animating pressing (lastButtonState = 0) the button then not pressing the button (buttonState = 1)
    {
      lastButtonState = buttonState;
    }
  }

}
