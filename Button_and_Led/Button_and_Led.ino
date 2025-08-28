
int ledPin = 4;
int buttonPin = 3;

void setup() {

  pinMode(ledPin,OUTPUT);
  pinMode(buttonPin,INPUT_PULLUP);
}

void loop() { 
  int buttonState = digitalRead(buttonPin); // "Read the button and remember what state it's in."
  digitalWrite(ledPin,buttonState); // "you're trying to use a value from the button to turn the LED on or off"
}

// Here when the button is not pressed, the LED comes on
